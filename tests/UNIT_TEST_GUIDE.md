# Unit Test Guide

> Last updated: 2026-04-09

本文档用于解释当前 `tests/` 目录中每个测试文件的覆盖范围、测试条件和通过判定，帮助你在执行测试时快速判断“哪些功能通过了、为什么通过”。

## 1. 如何看测试通过信息

项目里有两类 PASS 输出：

1. 全局 PASS（来自 `tests/conftest.py`）
- 格式：`PASS: tests/xxx.py::test_xxx`
- 含义：该测试函数整体通过。

2. 模块化 PASS（写在 P0 测试内部）
- 示例：`PASS [P0][Flask Routes] /forecast success`
- 含义：该条测试对某个具体功能分支验证通过。

建议运行时带 `-s`，否则 print 输出可能被 pytest 捕获：

```bash
pytest -s tests/
```

如需快速总览：

```bash
pytest -q tests/
```

## 2. 最小单元测试集（推荐）

```bash
pytest -s \
  tests/test_flask_app.py \
  tests/test_machine_learning.py \
  tests/test_frontend_index_mock.py
```

如需静默快速结果：

```bash
pytest -q \
  tests/test_flask_app.py \
  tests/test_machine_learning.py \
  tests/test_frontend_index_mock.py
```

顺序原则：先后端路由与 service，再补前端 mock 单测。

前端 mock 单测（新增，独立运行）：

```bash
pytest -p no:debugging -s tests/test_frontend_index_mock.py
```

## 3. 测试文件说明

### 3.1 `tests/test_openweather_jcdecaux_p0.py`（归档说明）

说明：这组测试文件已不在当前 `tests/` 目录的最小主测试集中，下面内容用于解释曾经的覆盖设计，便于你读旧提交或历史文档。

覆盖模块：`flaskapi/openweather.py`、`flaskapi/jcdecaux.py`

覆盖功能与条件：

1. `openweather.get_weather`
- 条件A：HTTP 200，字段完整。
- 期望：正确映射为 `temperature/weather/wind_speed/humidity`。
- 条件B：HTTP 非200。
- 期望：返回 `None`。

2. `openweather.get_forecast`
- 条件A：HTTP 200，`list` 至少3条。
- 期望：返回2个时间点（第1条和第3条）。
- 条件B：HTTP 非200。
- 期望：返回 `None`。
- 条件C：`list` 长度不足（仅1条）。
- 期望：抛 `IndexError`（用于暴露当前实现的边界风险）。

3. `jcdecaux.get_stations`
- 条件A：HTTP 200。
- 期望：字段映射正确（站点号、可用车位、经纬度等）。
- 条件B：HTTP 非200。
- 期望：返回 `None`。

4. `jcdecaux.get_station`
- 条件A：目标站点存在。
- 期望：返回站点详情。
- 条件B：目标站点不存在。
- 期望：返回 `None`。
- 条件C：HTTP 非200。
- 期望：返回 `None`。

5. `jcdecaux.fetch_stations_raw`
- 条件A：HTTP 200。
- 期望：返回原始 JSON。
- 条件B：HTTP 非200。
- 期望：返回 `None`。

通过判定：断言返回值结构、字段值、异常类型是否符合预期。

### 3.2 `tests/test_bikeinfo_sql_p0.py`（归档说明）

说明：同上，这部分是历史上的数据库层单测覆盖说明。

覆盖模块：`flaskapi/bikeinfo_SQL.py`

覆盖功能与条件：

1. `save_snapshot` 空输入
- 条件：传 `[]`。
- 期望：`stations_written=0`，`availability_written=0`。

2. `save_snapshot` 入参类型
- 条件：传 `dict` 非 list。
- 期望：抛 `ValueError`。

3. `save_snapshot` 转换与写入
- 条件：
  - 含重复 `number`（用于验证 station 去重后的最终值）
  - 含 `number=None` 脏数据（应被过滤）
  - 含毫秒时间戳 `last_update`
- 期望：
  - station 只写1条（同站点去重）
  - availability 写2条（每次快照都记录）
  - `last_update` 被转换为 `datetime` 且为 naive（无 tzinfo）

4. `get_station_sql`
- 条件A：`_fetch_all` 返回多条。
- 期望：只取首条。
- 条件B：`_fetch_all` 返回空。
- 期望：返回 `None`。

通过判定：断言调用参数、输出计数、时间类型、分支结果。

### 3.3 `tests/test_flask_app.py`

覆盖模块：`flaskapi/app.py`（路由层）

覆盖功能与条件：

1. `/weather`
- 条件A：`get_weather` 返回 `None`。
- 期望：500 + `Weather API unavailable`。
- 条件B：`get_weather` 返回天气字典。
- 期望：200 + 原样 JSON。

2. `/forecast`
- 条件A：`get_forecast` 返回数据。
- 期望：200 + 原样 JSON。

3. `/stations/refresh`
- 条件A：`fetch_stations_raw=None`。
- 期望：500 + `Bike API unavailable`。
- 条件B：`fetch_stations_raw` 有数据，`save_snapshot` 正常。
- 期望：200 + 写入计数字典。

4. `/stations`
- 条件A：`get_latest_stations_view` 返回列表。
- 期望：200 + 原样 JSON。
- 条件B：`get_latest_stations_view` 抛异常。
- 期望：500 + 错误 JSON。

5. `/predict`
- 条件：`predict_from_payload` 被 mock。
- 期望：路由原样返回服务层结果与状态码。

6. `/predict/by-input`
- 条件：`parse_predict_query_args` 返回参数错误。
- 期望：路由返回对应 400 错误 JSON。

7. `/station/<id>/history`
- 条件：底层函数抛异常。
- 期望：500 + 错误 JSON。

通过判定：HTTP 状态码 + JSON 结构与最小分支行为。

### 3.4 `tests/test_config_and_bikeapi_p1.py`（归档说明）

说明：同上，这部分是历史上的配置和导入脚本单测覆盖说明。

覆盖模块：`config.py`、`bikeinfo/bikeapi_cells/cell02_init_database.py`、`bikeinfo/bikeapi_cells/cell03_import_json_to_database.py`

覆盖功能与条件：

1. `config.py`
- 条件A：`DB_ENV=local`。
- 期望：本地 DB 配置生效，未配 key 时 `BIKE_STATUS_URL is None`。
- 条件B：`DB_ENV=rds`。
- 期望：RDS 配置生效。
- 条件C：`DB_ENV=invalid`。
- 期望：抛 `ValueError`。

2. `cell02_init_database.py`
- 条件：mock `create_engine` 与连接对象。
- 期望：执行了 `CREATE DATABASE IF NOT EXISTS` 语句。

3. `cell03_import_json_to_database.py`
- 条件A：目录有 JSON，且包含脏数据 `number=None`。
- 期望：过滤脏数据，station/availability 插入列表计数符合预期。
- 条件B：目录为空。
- 期望：不产生插入列表执行。

通过判定：mock 的 SQL 调用痕迹 + 结果计数。



### 3.6 `tests/test_machine_learning.py`

覆盖模块：`flaskapi/ml_service.py`

覆盖功能与条件：

1. `parse_predict_query_args`
- 条件：缺参数。
- 期望：返回 `(None, None, ({error...}, 400))`。

2. `predict_from_payload`
- 条件：单条记录输入（dict）。
- 期望：正常预测并返回 `target/raw_pred/pred_available_bikes`。

3. `predict_by_station_and_datetime`
- 条件：mock DB 特征与 forecast。
- 期望：返回 `station_id/raw_pred/pred_available_bikes/debug`。

通过判定：返回结构、状态码与最小预测流程可用性。

### 3.7 `tests/test_frontend_index_mock.py`

覆盖模块：`flaskapi/static/js/index.js`

覆盖功能与条件：

1. `toLocalDatetimeValue`
- 条件：传入固定本地时间对象。
- 期望：返回 `YYYY-MM-DDTHH:mm` 格式字符串。

2. `getStationColor`
- 条件：分别传入 `0/0`、`0/x`、`x/0`、`x/x`。
- 期望：返回 `grey/red/green/blue`。

3. `predictByInput`
- 条件A：站点号或时间缺失。
- 期望：不发请求，显示提示文案。
- 条件B：站点号和时间完整，mock `/predict/by-input` 成功返回。
- 期望：正确拼接 query string，并更新预测结果。

4. `loadCurrentWeather`
- 条件：mock `/weather` 返回天气数据。
- 期望：温度、天气、风速、湿度写入页面。

5. `loadForecast`
- 条件：mock `/forecast` 返回两条预报。
- 期望：两张 forecast 卡片都被正确填充。

6. `getNearestStartStation` / `getNearestEndStation`
- 条件：mock 多个站点，其中部分站点不可用。
- 期望：只从可用站点里挑最近的起点/终点站。

通过判定：mock DOM、mock fetch、mock 站点列表后，断言文本内容、请求 URL 与最近站点选择结果。

## 4. 架构变更对测试文档的影响（ML 拆分）

`app.py` 目前定位为“路由层 + 服务调用”，ML 细节位于 `ml_service.py`。因此阅读测试结果时应区分：

1. Flask 路由测试通过：说明 HTTP 入口、参数流转与响应结构正常。
2. ML service 测试通过：说明模型加载、特征构造、预测后处理逻辑正常。
3. 若仅有路由测试通过，不能等价认为模型逻辑已完整覆盖。

当前这份 `tests/` 目录里，主测试文件已经收敛为：

1. `tests/test_flask_app.py`
2. `tests/test_machine_learning.py`
3. `tests/test_frontend_index_mock.py`

## 5. 常见问题

1. 看不到 print 的 PASS？
- 原因：未加 `-s`。
- 解决：`pytest -s tests/...`

2. pytest 启动即崩溃（段错误）
- 这是当前 Python/环境问题，不代表单测逻辑本身失败。
- 你可先在相对稳定环境（如 Python 3.11 venv）执行同一套 `tests/`。

3. 为什么很多测试用 mock？
- 目标是单元测试隔离外部依赖（MySQL/网络/API），让失败点更可定位。

## 6. 快速定位“某功能是否通过”

按关键词搜 PASS：

```bash
pytest -s tests/test_flask_app.py
pytest -s tests/test_machine_learning.py
pytest -p no:debugging -s tests/test_frontend_index_mock.py
```

这样可以直接按最小集查看当前主链路是否可用。

## 7. 与 ML Notebook 对齐说明（新增）

近期 `machine_learning/ML.ipynb` 已更新为 70/30 时间顺序切分评估，并在模型训练后统一保存模型文件。以下产物命名已与项目现有文件保持一致：

- `decision_tree_model.joblib`
- `decision_tree_model.pkl`
- `linear_regression_lag_model.joblib`
- `linear_regression_lag_model_meta.joblib`
- `random_forest_model.joblib`
- `random_forest_model.pkl`
- `ridge_regression_model.joblib`
- `ridge_regression_model.pkl`
- `svr_model.joblib`
- `svr_model.pkl`

说明：

1. 上述模型文件由 Notebook 训练流程生成，不属于 `pytest tests/` 的直接断言产物。  
2. 运行与模型文件强相关的测试前，建议先确认模型文件路径和命名一致。  
3. `linear_regression_lag_model_meta.joblib` 用于保存 `features/target` 元信息，便于预测侧按同一特征顺序加载。  
