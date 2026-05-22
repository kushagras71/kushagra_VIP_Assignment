# Validation Checklist

| Requirement | Simple v2 output |
|---|---|
| A1 EDA | `eda_summary.md`, `plots/eda_*.png`, `eda_notebook.ipynb` |
| A2 8-week forecasts | `main.py` function `forecast_sku`, `artifacts/simple_forecaster.joblib` |
| A2 promotions + parent beverage signals | `model_summary.csv` compares full model vs baseline |
| A2 uncertainty | forecast rows include `lower_80` and `upper_80` from holdout residual percentiles |
| A2 WAPE by SKU | `wape_by_sku.csv` |
| A2 forecast plots | `plots/forecast_*.png` |
| B1 three agents | `SimplePlanner`, forecasting tool, knowledge tool in `main.py` |
| B2 LangChain tools | `StructuredTool.from_function(...)` in `main.py` |
| B3 memory | memory demo in `agent_answers.md` |
| B4 six scenarios | `agent_evaluation.csv`, `agent_answers.md` |
| C production thinking | `production_design.md` |
