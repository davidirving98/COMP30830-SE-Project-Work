# This Iteration Summary (English)

## 1) Goals and Background
- Eliminate duplicate writes in `availability` (same station + same timestamp inserted multiple times).
- Add station history visualization: when clicking a map marker, show recent 5-point history for `Available Bikes` and `Free Stands`.
- Fix frontend-backend error chain: `/stations` 500 causing JSON parse error, and `/station/<id>/history` 404.
- Align UI style: `Free Stands` text and series color changed to gold.

## 2) Code Diff (by module)

### A. Data write path and deduplication
- [flaskapi/bikeinfo_SQL.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/flaskapi/bikeinfo_SQL.py)
  - Added/completed DB functions:
    - `get_latest_stations_view()` to fetch latest per-station availability snapshot.
    - `save_snapshot(raw_data)` to persist API snapshot into `station` and `availability`.
  - Changed `availability` write from plain `INSERT` to idempotent UPSERT:
    - `ON DUPLICATE KEY UPDATE available_bike_stands/available_bikes/status`.
  - Added `get_station_history_sql(station_id)`:
    - Fetch latest 5 rows by `last_update DESC, id DESC`, then return in ascending time order for charting.

- [bikeinfo/bikeapi_cells/cell03_import_json_to_database.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/bikeinfo/bikeapi_cells/cell03_import_json_to_database.py)
  - Added unique-index check/create:
    - `uq_availability_number_last_update(number, last_update)`.
  - If missing, run historical duplicate cleanup first (keep smallest `id`).
  - Switched availability import to UPSERT.

- [bikeinfo/bikeapi_cells/cell04_import_api_to_database.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/bikeinfo/bikeapi_cells/cell04_import_api_to_database.py)
  - Switched availability insert to idempotent UPSERT.

- [bikeinfo/bikeSQL_cells/cell03_enforce_availability_dedup.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/bikeinfo/bikeSQL_cells/cell03_enforce_availability_dedup.py)
  - New one-off maintenance script:
    - Count duplicate groups.
    - Remove historical duplicates.
    - Create unique index.
    - Print index status.

### B. Flask backend endpoints
- [flaskapi/app.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/flaskapi/app.py)
  - `/stations` now:
    - fetches upstream data (`fetch_stations_raw`)
    - saves snapshot (`save_snapshot`)
    - returns DB latest view (`get_latest_stations_view`)
  - Wrapped full `/stations` flow with `try/except`, returning JSON error on failure.
  - Added history endpoint:
    - `/station/<int:station_id>/history`
  - Fixed a missing route decorator that previously caused `404`.

### C. Frontend map/chart behavior
- [flaskapi/static/js/index.js](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/flaskapi/static/js/index.js)
  - Marker popup chart changed from categorical bar chart to time-series line chart.
  - Added history fetch:
    - `fetch(/station/${station.number}/history)`
  - Chart columns changed to:
    - `datetime + Available Bikes + Free Stands`
  - Enabled smooth lines:
    - `curveType: 'function'`
  - Time-axis formatting:
    - `hAxis.format = 'HH:mm'`
  - `Free Stands` series color changed to gold:
    - `#d4af37`
  - Added gold `Free Stands` text in popup.
  - Added `response.ok` check before `response.json()` for `/stations`.

## 3) Delivered Functional Outcomes
- Deduplication mechanism:
  - Dedup key is `(number, last_update)`.
  - Existing data can be cleaned, then protected by unique index.
  - Future writes are idempotent via UPSERT.

- History chart:
  - On marker click, fetch latest 5 historical rows.
  - Render two smooth lines: `Available Bikes` and `Free Stands`.
  - X-axis is time (`HH:mm`), matching your requirement.

- Error handling:
  - Backend now returns JSON errors for `/stations`.
  - Frontend no longer blindly parses non-2xx responses as JSON.
  - History endpoint 404 issue has been fixed.

## 4) Key Issues Found and Fixed
- Issue 1: `SyntaxError` after `/stations` 500.
  - Cause: frontend attempted `response.json()` on non-JSON error response.
  - Fix: JSON error response on backend + `response.ok` check on frontend.

- Issue 2: `/station/<id>/history` returned 404.
  - Cause: route function existed but decorator was missing.
  - Fix: restored `@app.route("/station/<int:station_id>/history")`.

## 5) Validation Status
- Confirmed:
  - Dedup script output showed `duplicate_rows=0`.
  - Unique index exists (`Non_unique=0`).
  - Frontend now shows smooth time-series with gold `Free Stands`.
- Note:
  - Workspace still contains other unrelated modified files; this summary only covers this iteration’s scope.

---

# 本轮修改整理（中文）

## 1) 目标与问题背景
- 解决 `availability` 数据重复写入问题（同一站点同一时间戳重复落库）。
- 增加站点历史数据能力：点击地图站点后展示 `Available Bikes` 与 `Free Stands` 最近 5 条历史曲线。
- 修复前后端联调中的错误链路：`/stations` 500 后前端 JSON 解析报错、`/station/<id>/history` 404。
- 统一前端展示：`Free Stands` 文本与曲线颜色调整为金色。

## 2) 代码对比（按模块）

### A. 数据写入与去重
- [flaskapi/bikeinfo_SQL.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/flaskapi/bikeinfo_SQL.py)
  - 新增/补全 DB 读写函数：
    - `get_latest_stations_view()`：按站点取最新一条可用性数据。
    - `save_snapshot(raw_data)`：将 API 快照写入 `station`、`availability`。
  - `availability` 写入从“纯 INSERT”改为“幂等 UPSERT”：
    - `ON DUPLICATE KEY UPDATE available_bike_stands/available_bikes/status`。
  - 新增 `get_station_history_sql(station_id)`：
    - 查询某站点最近 5 条记录（按 `last_update DESC, id DESC` 取样），再升序返回用于画时间轴。

- [bikeinfo/bikeapi_cells/cell03_import_json_to_database.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/bikeinfo/bikeapi_cells/cell03_import_json_to_database.py)
  - 初始化后增加唯一索引检查与创建：`uq_availability_number_last_update(number, last_update)`。
  - 若索引不存在，先执行历史重复清理 SQL（保留最小 `id`）。
  - 导入 `availability` 改为 `ON DUPLICATE KEY UPDATE`。

- [bikeinfo/bikeapi_cells/cell04_import_api_to_database.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/bikeinfo/bikeapi_cells/cell04_import_api_to_database.py)
  - `availability` 插入改为幂等 `ON DUPLICATE KEY UPDATE`。

- [bikeinfo/bikeSQL_cells/cell03_enforce_availability_dedup.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/bikeinfo/bikeSQL_cells/cell03_enforce_availability_dedup.py)
  - 新增一次性维护脚本：
    - 统计重复组数。
    - 清理历史重复。
    - 创建唯一索引。
    - 回显索引状态。

### B. 后端接口（Flask）
- [flaskapi/app.py](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/flaskapi/app.py)
  - `/stations` 路由改为：
    - 先拉外部 API（`fetch_stations_raw`）
    - 写入 DB（`save_snapshot`）
    - 返回 DB 最新视图（`get_latest_stations_view`）
  - `/stations` 全流程放入 `try/except`，500 时返回 JSON 错误（避免返回 HTML 导致前端解析异常）。
  - 新增历史接口：`/station/<int:station_id>/history`，返回最近 5 条历史数据。
  - 修复过一次路由缺失导致的 404（已补回 `@app.route(...)` 装饰器）。

### C. 前端展示（地图 + 图表）
- [flaskapi/static/js/index.js](/Users/alex/Documents/COMP30830_Software_Engineering/COMP30830-SE-Project-Work/flaskapi/static/js/index.js)
  - Marker 点击弹窗图从“分类柱状图”改为“时间序列折线图”。
  - 新增历史请求：`fetch(/station/${station.number}/history)`。
  - 图表数据改为：`datetime + Available Bikes + Free Stands`。
  - 曲线平滑：`curveType: 'function'`。
  - 横轴为时间：`hAxis.format = 'HH:mm'`。
  - `Free Stands` 曲线颜色改为金色：`#d4af37`。
  - 弹窗文案新增金色 `Free Stands` 文本。
  - `/stations` 请求前置 `response.ok` 判断，避免 500 响应被 `response.json()` 触发 `SyntaxError`。

## 3) 功能实现结果
- 去重机制：
  - 去重标准为 `(number, last_update)`。
  - 现有数据可通过维护脚本清重后建立唯一索引。
  - 后续写入同键将走 UPSERT，不再产生重复记录。

- 历史曲线功能：
  - 点击任意站点 marker 后，请求该站最近 5 条历史。
  - 弹窗显示两条平滑曲线：`Available Bikes`、`Free Stands`。
  - 横坐标为时间（`HH:mm`），满足“时间轴 + 平滑曲线 + 最近5条”。

- 错误处理改进：
  - `/stations` 后端失败会返回 JSON 错误信息。
  - 前端不再将非 2xx 响应直接当 JSON 解析。
  - 历史接口 404 问题已修复。

## 4) 本轮关键问题与修复记录
- 问题1：`/stations` 500 后前端报 `SyntaxError`。
  - 原因：500 响应体不是预期 JSON，前端仍强制 `response.json()`。
  - 修复：后端统一 JSON 错误返回 + 前端 `response.ok` 检查。

- 问题2：`/station/<id>/history` 404。
  - 原因：函数存在但路由装饰器缺失。
  - 修复：补充 `@app.route("/station/<int:station_id>/history")`。

## 5) 验证与状态
- 已确认：
  - 去重脚本可输出 `duplicate_rows=0`，且唯一索引已存在（`Non_unique=0`）。
  - 前端已切换为时间序列曲线图，`Free Stands` 为金色文本+金色曲线。
- 备注：当前工作区仍有其他非本轮文件变更（如 `diff.md`、`.DS_Store`、`flaskapi/jcdecaux.py` 等），本说明仅覆盖本轮相关改动。
