# COMP30830 项目对话整理（AI Chat Summary）

> Date: 2026-04-14
> Scope: 本文档整理本次项目协作对话中与实现/测试相关的关键结论与执行记录。

## 1. 文档目的

用于提交课程要求中的 "URL to a document in GitHub for Generative AI chats"，并聚焦本项目技术内容，覆盖：

1. ML 模型训练
2. 模型部署与预测流程
3. 单元测试计划与测试过程
4. Flask 功能
5. Database 相关功能
6. 本次新增测试与验证结果

---

## 2. ML 模型训练与产物

基于 `machine_learning/ML.ipynb` 检查结果：

1. Notebook 包含数据读取、特征处理、训练与模型保存流程。
2. 读取数据文件：`final_merged_data.csv.gz`
3. 输出清洗数据：`data_cleaned.csv`
4. 输出模型文件（`joblib`/`pkl`），包括：
   - `linear_regression_lag_model`
   - `decision_tree_model`
   - `random_forest_model`
   - `ridge_regression_model`
   - `svr_model`

结论：Notebook 主要产出模型与元数据文件，供后续预测服务加载。

---

## 3. 模型部署与预测相关

项目预测相关路径（已在对话中核查）：

1. Flask 预测路由：`/predict`、`/predict/by-input`
2. 服务层：`flaskapi/ml_service.py`
3. 模型文件加载与推理依赖 `joblib/pkl` 产物

补充检查：

- `ML.ipynb` **未直接访问**以下同级脚本/页面文件：
  - `0. decision_tree.py`
  - `0. linear_regression.py`
  - `0. random_forest.py`
  - `0. svr.py`
  - `0.ridge_regression.py`
  - `1. predict.py`
  - `2. predict_based_on_weather.py`
  - `3. prediction_flask.py`
  - `4. fetching_results.js`
  - `5. sample-prediction-page.html`
  - `6. example_sktime.py`

---

## 4. Flask 与 Database 功能梳理

### 4.1 `/stations` 逻辑（重点）

当前 `flaskapi/app.py` 中 `/stations` 路由行为：

1. 优先调用 `get_latest_stations_view()` 从 DB 读取站点数据。
2. 若 DB 失败，自动 fallback 调用 `fetch_stations_raw()`（JCDecaux 实时 API）。
3. fallback 成功时，经 `_normalize_station_payload()` 转成前端字段后返回。
4. 若 DB 和 fallback API 都失败，返回 `500` 错误 JSON。

这保证了：

- DB 异常时前端仍有机会拿到站点数组并渲染 marker。
- 双重失败时，接口按错误分支返回 500，便于前端与日志识别故障。

### 4.2 启动阶段 DB 检查覆盖性

已确认：

1. 现有单测不覆盖 Flask `__main__` 启动分支中的 DB 连通性检查。
2. 现有 DB 异常测试主要覆盖请求阶段（route handler）异常处理。

---

## 5. 单元测试计划与执行过程

### 5.1 本次新增测试（`tests/test_flask_app.py`）

新增 2 条针对 `/stations` 的关键测试：

1. `test_stations_db_failure_falls_back_to_live_api_payload`
   - 验证 DB 失败时，fallback API 成功并返回前端所需字段格式。
2. `test_stations_returns_500_when_db_fails_and_fallback_api_unavailable`
   - 验证 DB 失败且 fallback API 不可用时返回 500。

### 5.2 文档同步（`tests/UNIT_TEST_GUIDE.md`）

已同步更新：

1. `/stations` 覆盖说明新增 fallback 成功与 fallback 失败两种分支。
2. 测试清单更新为 11 条，包含上述 2 条新增用例。

### 5.3 执行命令与结果

执行命令：

```bash
pytest -q -p no:debugging tests/test_flask_app.py
```

结果：

- `11 passed`
- 说明：环境下默认 pytest 插件链可能触发 segfault，使用 `-p no:debugging` 可稳定运行。

---

## 6. 本次对话产出清单

代码/文档层面的最终变更（按用户要求保留）：

1. `tests/test_flask_app.py`
   - 新增 2 条 `/stations` fallback 相关测试
2. `tests/UNIT_TEST_GUIDE.md`
   - 更新覆盖说明与测试清单
3. 新增本总结文档：`AI_CHAT_PROJECT_SUMMARY.md`

---

## 7. 可直接提交到 GitHub 的建议

1. 将本文件提交到仓库（每位同学一份独立文档）。
2. 在报告或作业提交处提供该文件的 GitHub URL。
3. 若需要“原始逐轮聊天记录”，可在本文件后追加时间线或附录。

