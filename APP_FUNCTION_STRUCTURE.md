# `flaskapi/app.py` 功能结构说明（含行号）

> 基于当前代码版本；行号对应文件：`flaskapi/app.py`

## 1. 文件职责总览

`app.py` 主要承担三类职责：

1. Flask 应用初始化与模型加载
2. 预测前特征对齐/参数解析/后处理等通用逻辑
3. 对外 API 路由（站点、天气、SQL 查询、模型预测）

---

## 2. 初始化与依赖（1-54）

### 2.1 导入与项目路径（1-28）
- Flask 与基础库导入：1-9
- 项目根路径注入 `sys.path`：11-14
- 配置与外部模块导入：14-26
- Flask app 初始化：28

### 2.2 模型路径与加载（30-54）
- 默认模型路径（Ridge）：32
- Meta 候选路径：33-36
- 全局模型变量：38-40
- 启动时加载模型与 meta：42-49
- 加载失败兜底：50-54

---

## 3. 通用辅助函数（56-167）

### 3.1 特征对齐
- `_effective_model_features()`：56-60  
  作用：优先读取模型 `feature_names_in_`，否则使用 meta 特征列表。

- `_build_prediction_matrix(df)`：63-92  
  作用：将请求数据对齐到训练特征顺序；支持 `number -> number_*` one-hot 转换。

### 3.2 预测相关辅助
- `_pick_forecast_for_target(target_dt, forecast_rows)`：94-115  
  作用：根据目标时间选择最合适天气预测点。

- `_predict_post_process(raw_pred, capacity=None)`：118-122  
  作用：统一后处理（`<3 -> 0`、容量裁剪、四舍五入）。

- `_parse_predict_query_args(args)`：125-157  
  作用：解析并校验 `/predict/by-input` 参数，错误返回 400 响应。

- `_weather_to_features(weather)`：160-167  
  作用：天气字段映射到模型特征；天气不可用时回退到默认值。

---

## 4. 页面与基础数据路由（170-227）

- `GET /` -> `index()`：170-172  
  返回主页模板。

- `GET /stations` -> `stations()`：175-183  
  从 DB 返回最新站点视图。

- `GET /stations/refresh` -> `stations_refresh()`：186-196  
  手动拉取 Bike API 并写入数据库。

- `GET /weather` -> `weather()`：199-206  
  返回当前天气。

- `GET /forecast` -> `forecast()`：208-215  
  返回天气预测。

- `GET /station/<int:station_id>/info` -> `station_info()`：218-227  
  聚合站点信息 + 当前天气。

---

## 5. SQL 调试/查询路由（230-266）

- `GET /stations_SQL` -> `stations_sql()`：231-236
- `GET /availability_SQL` -> `availability_sql()`：240-245
- `GET /stations_SQL/<int:station_id>/info` -> `station_sql_info()`：249-257
- `GET /station/<int:station_id>/history` -> `station_history()`：261-266

这些路由用于数据库读取与联调验证。

---

## 6. 模型预测路由（269-357）

### 6.1 通用预测接口
- `POST /predict` -> `predict()`：269-298
- 核心流程：
  1. 校验模型已加载：273-274
  2. 读取 JSON：276-281
  3. 构造模型输入矩阵：283
  4. 模型预测：284
  5. 后处理：286-287
  6. 返回 raw 与后处理结果：289-296

### 6.2 输入式预测接口
- `GET /predict/by-input` -> `predict_by_input()`：301-357
- 核心流程：
  1. 模型加载检查：304-305
  2. 参数解析与 400 校验：307-309（调用 125-157）
  3. 读取 DB 特征：311-313
  4. 读取并选择天气预测：315-316
  5. 天气不可用回退：320（调用 160-167）
  6. 组装单行特征：322-335
  7. 特征对齐 + 预测：337-338
  8. 统一后处理：340
  9. 返回可解释结果（含 `feature_values` / `raw_pred`）：342-355

---

## 7. 启动入口（360-362）

- `if __name__ == "__main__":`：360-362
- 使用环境变量 `PORT`（默认 5000）启动 Flask。

---

## 8. 关键调用链（预测路径）

`/predict/by-input` 调用链：

1. 参数校验：`_parse_predict_query_args`（125-157）
2. DB 特征：`get_prediction_db_features`（在 `bikeinfo_SQL.py`）
3. 天气选择：`get_forecast` + `_pick_forecast_for_target`（94-115）
4. 天气映射：`_weather_to_features`（160-167）
5. 特征对齐：`_build_prediction_matrix`（63-92）
6. 预测后处理：`_predict_post_process`（118-122）

---

## 9. 维护建议（结构层面）

1. 将模型加载与特征对齐逻辑拆到独立模块（例如 `ml_runtime.py`）。
2. 将 SQL 调试路由与业务路由分文件管理，降低单文件复杂度。
3. 统一异常响应格式（error code + message + context），便于前端处理。
4. 为 `/predict` 与 `/predict/by-input` 增加集成测试，固定输入输出行为。

