# Unit Test Guide

> Last updated: 2026-04-12

本文档仅覆盖当前仓库中有效的 3 个测试文件：

1. `tests/test_flask_app.py`
2. `tests/test_machine_learning.py`
3. `tests/test_frontend_index.py`

---

## 1. 运行方式

推荐运行（带 PASS 输出）：

```bash
pytest -s \
  tests/test_flask_app.py \
  tests/test_machine_learning.py \
  tests/test_frontend_index.py
```

快速运行（安静模式）：

```bash
pytest -q \
  tests/test_flask_app.py \
  tests/test_machine_learning.py \
  tests/test_frontend_index.py
```

说明：

1. `tests/conftest.py` 会在每个通过的测试打印 `PASS: <nodeid>`。
2. `tests/test_frontend_index.py` 依赖 Node.js；未安装时该文件会被 `skip`。

---

## 2. 测试文件覆盖说明

### 2.1 `tests/test_flask_app.py`

覆盖模块：`flaskapi/app.py`（路由层）

覆盖项：

1. `/weather`
- 天气服务不可用时返回 `500` 与错误信息。
- 天气服务正常时返回 `200` 与 payload。

2. `/forecast`
- 预报服务正常时返回 `200` 与 payload。

3. `/stations/refresh`
- `fetch_stations_raw` 返回 `None` 时返回 `500`。
- `fetch_stations_raw + save_snapshot` 成功时返回 `200` 与写入计数。

4. `/stations`
- `get_latest_stations_view` 成功时返回 `200` 与站点列表。
- DB 读取失败时，自动 fallback 到实时 API 并返回标准化站点列表。
- DB 读取失败且 fallback API 不可用时，返回 `500` 与错误信息。

5. `/station/<id>/history`
- 底层抛异常时返回 `500`。

6. `/predict`
- 路由透传 `predict_from_payload` 的状态码与返回体。

7. `/predict/by-input`
- 参数解析函数返回错误时，路由返回对应 `400` 与错误 JSON。

通过判定：HTTP 状态码和 JSON 结构与预期一致。

### 2.2 `tests/test_machine_learning.py`

覆盖模块：`flaskapi/ml_service.py`

覆盖项：

1. `parse_predict_query_args`
- 缺少参数时返回 `400` 错误结构。

2. `predict_from_payload`
- 单条记录输入可完成特征构建和预测，返回：
  `target/raw_pred/pred_available_bikes`。

3. `predict_by_station_and_datetime`
- 通过 mock DB 特征与 forecast，验证预测主流程返回结构与状态码。

通过判定：返回状态、字段存在性、返回类型符合预期。

### 2.3 `tests/test_frontend_index.py`

覆盖模块：`flaskapi/static/js/index.js`（Node.js mock DOM 环境）

覆盖项：

1. `toLocalDatetimeValue`
- 时间格式化输出 `YYYY-MM-DDTHH:mm`。

2. `getStationColor`
- 覆盖 `grey/red/green/blue` 4 种可用性映射。

3. `predictByInput`
- 缺少输入时不发请求并提示。
- 输入完整时拼接 `/predict/by-input` query 并更新结果文案。

4. `loadCurrentWeather`
- 调用 `/weather` 后刷新温度、天气、风速、湿度 UI 字段。

5. `loadForecast`
- 调用 `/forecast` 后刷新两张预报卡片字段。

6. `getNearestStartStation/getNearestEndStation`
- 过滤不可用候选站点后，返回最近有效站点。

通过判定：函数行为、请求 URL、DOM 字段更新结果符合预期。

---

## 3. 当前测试清单（函数级）

### `tests/test_flask_app.py`

1. `test_weather_unavailable_returns_500`
2. `test_weather_success_returns_payload`
3. `test_forecast_success_returns_payload`
4. `test_stations_refresh_unavailable_returns_500`
5. `test_stations_refresh_success_returns_snapshot_result`
6. `test_stations_success_returns_payload`
7. `test_stations_db_failure_falls_back_to_live_api_payload`
8. `test_stations_returns_500_when_db_fails_and_fallback_api_unavailable`
9. `test_station_history_exception_returns_500`
10. `test_predict_route_returns_service_result`
11. `test_predict_by_input_invalid_query_returns_400`

### `tests/test_machine_learning.py`

1. `test_parse_predict_query_args_missing_returns_400`
2. `test_predict_from_payload_supports_single_record`
3. `test_predict_by_station_and_datetime_returns_basic_prediction`

### `tests/test_frontend_index.py`

1. `test_to_local_datetime_value_formats_expected_string`
2. `test_get_station_color_maps_availability_states`
3. `test_predict_by_input_validates_missing_inputs_without_fetch`
4. `test_predict_by_input_builds_api_request_and_updates_result`
5. `test_load_current_weather_updates_summary_fields`
6. `test_load_forecast_updates_two_cards`
7. `test_get_nearest_start_and_end_station_ignore_unusable_candidates`
