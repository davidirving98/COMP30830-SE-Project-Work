# COMP30830-SE-Project-Work

本仓库包含共享单车可用数量预测的训练、推理与 API 示例代码。

## 目录说明

- `machine_learning/0. linear_regression.py`  
  训练基线线性回归模型：构造时间/天气特征，`station_id` 使用 `OneHotEncoder`，执行时间序列交叉验证与 70/30 时间切分评估，并保存模型文件。
- `machine_learning/1. predict.py`  
  本地单条样本预测示例（读取已保存模型并输出预测值）。
- `machine_learning/2. predict_based_on_weather.py`  
  基于 `station_id + 日期时间 + 天气` 的预测脚本（天气部分当前为 stub，可替换真实天气 API）。
- `machine_learning/3. prediction_flask.py`  
  Flask 接口服务，提供 `/predict` HTTP 预测入口。
- `machine_learning/6. example_sktime.py`  
  `sktime` 时序预测示例脚本（独立 demo，不是当前 bike 模型主流程）。

## 数据文件

- 当前训练数据：`machine_learning/final_merged_data.csv.gz`

## 环境建议

- 推荐 Python 环境：`comp47350py312`（Python 3.12.x）

安装依赖：

```bash
pip install pandas scikit-learn joblib flask
```

## 运行方式

先进入机器学习目录：

```bash
cd /Users/alex/Desktop/COMP30830-David/machine_learning
```

训练模型：

```bash
python "0. linear_regression.py"
```

本地预测示例：

```bash
python "1. predict.py"
```

天气版本预测脚本：

```bash
python "2. predict_based_on_weather.py"
```

启动 Flask API：

```bash
python "3. prediction_flask.py"
```

请求示例：

```bash
curl "http://127.0.0.1:5000/predict?date=2024-12-15&time=09:00&station_id=32"
```

## 常见问题

- 如果报错 `FileNotFoundError: final_merged_data.csv.gz`，通常是终端当前目录不在 `machine_learning/`。
- 当前模型预测目标是 `num_bikes_available`。
- 训练脚本中 `station_id` 按类别特征处理（one-hot），不是连续数值。
