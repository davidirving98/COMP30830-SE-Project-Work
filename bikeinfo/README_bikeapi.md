# bikeinfo 模块说明

## 配置文件
- `bikeinfo/config.py`  
  存放数据库连接信息和 Dublin Bikes API 地址（如 `DB_USER`、`DB_PASSWORD`、`DB_HOST`、`BIKE_STATUS_URL`）。

## 原始 Notebook
- `bikeinfo/bikeapi.ipynb`  
  原始数据采集与入库流程 Notebook。
- `bikeinfo/bikeSQL.ipynb`  
  原始 SQL 查询与统计分析 Notebook。

## bikeapi 单元拆分脚本
- `bikeinfo/bikeapi_cells/cell01_fetch_status_to_json.py`  
  每 5 分钟调用一次 Dublin Bikes API，持续采集并把站点状态保存到 `data/dublinbike_status/` 的 JSON 文件。
- `bikeinfo/bikeapi_cells/cell02_init_database.py`  
  检查并创建数据库 `COMP30830_SW`（若不存在）。
- `bikeinfo/bikeapi_cells/cell03_import_json_to_database.py`  
  从本地 JSON 文件读取数据，创建 `station` / `availability` 表，并写入数据库（`station` 用 upsert）。
- `bikeinfo/bikeapi_cells/cell04_import_api_to_database.py`  
  直接从 API 拉取一次最新数据并写入数据库，不经过本地 JSON 中间文件。

## bikeSQL 单元拆分脚本
- `bikeinfo/bikeSQL_cells/cell01_db_connection_and_query_helper.py`  
  建立数据库连接，提供查询函数 `q()`（返回 DataFrame）。
- `bikeinfo/bikeSQL_cells/cell02_base_stats_report.py`  
  输出基础统计：`station` 总数、`availability` 总数、按天记录数。
- `bikeinfo/bikeSQL_cells/cell03_daily_feature_report.py`  
  输出按天聚合特征预览：平均可用单车、平均可用车桩、记录数。

## 数据目录
- `bikeinfo/data/dublinbike_status/`  
  本地缓存的站点状态 JSON 历史数据。

## 推荐执行顺序
1. 先配置 `bikeinfo/config.py`。
2. 运行 `bikeinfo/bikeapi_cells/cell02_init_database.py` 初始化数据库。
3. 二选一导入方式：
4. 方式 A：运行 `bikeinfo/bikeapi_cells/cell03_import_json_to_database.py`（从本地 JSON 导入）。
5. 方式 B：运行 `bikeinfo/bikeapi_cells/cell04_import_api_to_database.py`（从 API 直接导入）。
6. 运行 `bikeinfo/bikeSQL_cells/cell02_base_stats_report.py` 和 `bikeinfo/bikeSQL_cells/cell03_daily_feature_report.py` 做统计检查。
