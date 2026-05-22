# Demand Forecasting Solution

This folder contains the assessment solution.

Everything important is in one file:

```text
main.py
```

The flow is:

1. Load the CSV files.
2. Build a SKU x cluster x week feature table.
3. Run EDA and save short notes/plots.
4. Train a Random Forest model.
5. Compare the full model against a baseline without promotion and parent-beverage signals.
6. Wrap forecasting and knowledge retrieval as LangChain Core tools.
7. Run the six planner scenarios.
8. Write production notes and a validation checklist.

## Run

From the project root:

```bash
.vip_venv/bin/pip install -r code/requirements.txt
.vip_venv/bin/python code/main.py
```

## Main Outputs

All outputs are written to:

```text
code/outputs/
```

Main explanation document:

- `SOLUTION_PARTS_ABC.md`

Important files:

- `eda_summary.md`
- `model_notes.md`
- `model_summary.csv`
- `wape_by_sku.csv`
- `agent_evaluation.csv`
- `agent_answers.md`
- `production_design.md`
- `validation_checklist.md`
- `plots/*.png`

Model artifact:

```text
code/artifacts/forecaster.joblib
```

## Model Choice

I used a Random Forest because it works well for short, noisy, promotion-driven weekly sales data. Features are intentionally focused:

- lag demand: 1, 2, and 4 weeks
- 4-week rolling average
- price
- week/month
- category, cluster, parent brand
- promotion flag/type
- parent-beverage units

Uncertainty uses the 10th and 90th percentile holdout residuals.

## Agent Design

The agent system is deliberately small:

```text
Planner Agent
  -> Forecasting Agent/tool
  -> Knowledge Agent/tool
  -> final answer + short memory update
```

The tools use LangChain Core `StructuredTool`, but there is no API key or LLM dependency. This keeps the project runnable and explainable.
