# Demand Forecasting & Agentic AI Solution

Candidate: Kushagra Srivastava  
Solution folder: `code`

This document explains the simplified solution in the same structure as the assignment: Part A, Part B, and Part C.

## Executive Summary

The goal is to help distributors plan branded merchandise purchases for the next 8 weeks. The solution uses historical merchandise sales, supplier promotions, SKU metadata, and parent-beverage sales to produce SKU x cluster forecasts. These forecasts are then wrapped in a small agentic decision-support layer that can answer planner questions in natural language.

The implementation is organized as a compact development project:

- One main script: `main.py`
- One model artifact: `artifacts/forecaster.joblib`
- One output folder: `code/outputs/`
- A small LangChain Core tool layer, without API keys or external LLM calls

Key result:

- Full model WAPE: `0.164`
- Baseline WAPE without promotion and parent-beverage signals: `0.170`
- The full model performs better, so the extra business signals add value.

---

# Part A — Demand Forecasting

## A1. Exploration

The data was loaded from the provided `data_package` folder:

- `merch_sales_weekly.csv`
- `sku_master.csv`
- `parent_beverage_sales.csv`
- `promotions.csv`

The final analysis table is at the required grain:

```text
SKU x cluster x week
```

The dataset contains:

- 4,486 weekly sales rows
- 40 SKUs
- 2 clusters: `C-EAST` and `C-WEST`
- History from `2024-11-18` to `2026-05-11`

### Demand Shape

Overall weekly demand is uneven and skewed. Median weekly demand is `23` units, while the 90th percentile is `53` units. This means a flat average forecast would miss important high-demand weeks.

Category-level demand:

| Category | Average Weekly Units | Total Units |
|---|---:|---:|
| Accessories | 20.44 | 22,690 |
| Apparel | 28.76 | 38,194 |
| Drinkware | 41.97 | 41,050 |
| Headwear | 22.93 | 24,539 |

Drinkware has the highest average weekly demand, while Accessories and Headwear are lower-volume categories.

Cluster-level demand:

| Cluster | Average Weekly Units | Total Units |
|---|---:|---:|
| C-EAST | 35.94 | 80,615 |
| C-WEST | 20.44 | 45,858 |

`C-EAST` is materially larger than `C-WEST`, so cluster must be included in the model.

### Representative SKUs

The assignment scenarios mention these SKUs:

| SKU | Cluster | Weeks of History | Average Weekly Units |
|---|---|---:|---:|
| SKU-1042 | C-EAST | 78 | 28.54 |
| SKU-1042 | C-WEST | 78 | 17.59 |
| SKU-2017 | C-EAST | 19 | 27.42 |
| SKU-2017 | C-WEST | 19 | 21.68 |
| SKU-2099 | C-EAST | 21 | 51.95 |
| SKU-2099 | C-WEST | 21 | 19.62 |
| SKU-3008 | C-EAST | 78 | 36.83 |
| SKU-3008 | C-WEST | 78 | 23.67 |

Some SKUs have long histories, while others are newer. The model therefore needs to handle both established and short-history SKUs.

### Parent-Beverage Relationship

The parent-beverage signal has a positive relationship with merchandise demand, especially at short lags.

| Parent Beverage Lag | Median Correlation |
|---:|---:|
| 0 weeks | 0.138 |
| 1 week | 0.295 |
| 2 weeks | 0.197 |
| 3 weeks | 0.061 |
| 4 weeks | 0.057 |

The strongest correlation is at the 1-week lag. This supports the business idea that branded merchandise demand follows parent-beverage demand with a short delay.

### Promotion Impact

Promotion weeks show clear lift across all categories:

| Category | Non-Promo Avg | Promo Avg | Lift |
|---|---:|---:|---:|
| Accessories | 19.89 | 39.09 | 96.6% |
| Apparel | 28.57 | 45.40 | 58.9% |
| Drinkware | 41.10 | 82.00 | 99.5% |
| Headwear | 22.41 | 38.85 | 73.4% |

Promotions are an important demand driver, so the model includes:

- `promo_active`
- `promo_type`

EDA outputs:

- `outputs/eda_summary.md`
- `outputs/plots/eda_demand_distribution.png`
- `outputs/plots/eda_weekly_demand.png`
- `outputs/plots/eda_parent_correlation.png`
- `eda_notebook.ipynb`

## A2. Forecasting Model

### Model Choice

I used a Random Forest regression model.

This choice is practical for this dataset because:

- the dataset is small,
- demand is nonlinear,
- promotions can create jumps,
- several SKUs have short histories,
- it works without heavy tuning,
- it is easier to explain than a more complex neural or time-series model.

### Features Used

The model uses focused, explainable features:

Historical demand:

- `lag_1`
- `lag_2`
- `lag_4`
- `rolling_4`

Calendar and item features:

- `weekofyear`
- `month`
- `price_avg`
- `category`
- `cluster_id`
- `parent_brand`
- `age_weeks`

Business signals:

- `promo_active`
- `promo_type`
- `parent_units`

### Evaluation

The last 8 historical weeks were used as the holdout period:

```text
2026-03-23 to 2026-05-11
```

Results:

| Model | Overall WAPE | Median SKU WAPE |
|---|---:|---:|
| Full model | 0.164 | 0.156 |
| Baseline without promo/parent signals | 0.170 | 0.171 |

The full model performs better than the baseline, which shows that promotions and parent-beverage sales improve the forecast.

Evaluation outputs:

- `outputs/model_summary.csv`
- `outputs/wape_by_sku.csv`
- `outputs/model_notes.md`

### Uncertainty

The forecast includes an uncertainty interval:

- `lower_80`
- `upper_80`

These are generated from the 10th and 90th percentile residuals in the holdout period. This is not a perfect statistical interval, but it is transparent and appropriate for a prototype.

### Forecast Plot Examples

Example forecast plots are generated for:

- `SKU-1042 / C-EAST`
- `SKU-2017 / C-WEST`
- `SKU-3008 / C-EAST`

Output files:

- `outputs/plots/forecast_SKU-1042_C-EAST.png`
- `outputs/plots/forecast_SKU-2017_C-WEST.png`
- `outputs/plots/forecast_SKU-3008_C-EAST.png`

---

# Part B — Agentic Decision Support

The assignment asks for a three-agent system:

1. Planner Agent
2. Forecasting Agent
3. Knowledge Agent

The simplified implementation keeps this structure but avoids unnecessary complexity.

## Agent Design

```text
Planner Agent
  -> Forecasting Agent / forecast_merchandise_demand tool
  -> Knowledge Agent / retrieve_merchandise_knowledge tool
  -> final answer + short memory update
```

The system uses LangChain Core `StructuredTool` wrappers:

- `forecast_merchandise_demand`
- `retrieve_merchandise_knowledge`

No API key or external LLM is required. The planner uses deterministic routing rules. This makes the project easy to run, debug, and explain.

## Forecasting Tool

The forecasting tool takes:

- `sku_id`
- `cluster_id`
- `horizon`

It returns:

- weekly forecast
- total forecast units
- lower and upper uncertainty bounds
- safety stock
- recommended buy quantity

Bad inputs return an error message instead of crashing.

## Knowledge Tool

The knowledge tool searches the markdown files in:

```text
data_package/knowledge_base/
```

It retrieves useful policy/calendar context from documents such as:

- `supplier_promo_calendar_FY26.md`
- `safety_stock_policy.md`
- `cluster_definitions.md`
- `distributor_onboarding_branded_merch.md`

## Memory

The planner keeps short conversation memory:

- last SKU
- last cluster
- last category

Example:

Turn 1:

```text
How many units of SKU-1042 should I buy for C-EAST for the next 8 weeks?
```

Turn 2:

```text
What if the promotion runs two weeks longer?
```

The second question does not repeat the SKU or cluster, but the system remembers `SKU-1042 / C-EAST` and answers the follow-up.

## Six Scenario Evaluation

The system was run against all six scenarios from Appendix C.

| Scenario | Route Correct | Tool Arguments Reasonable | Quality |
|---:|---|---|---:|
| 1 | True | True | 5 |
| 2 | True | True | 5 |
| 3 | True | True | 5 |
| 4 | True | True | 5 |
| 5 | True | True | 5 |
| 6 | True | True | 5 |

The rubric is:

- `5`: correct route, valid tool call, useful grounded answer
- `3`: partially useful
- `1`: unusable

## Scenario Answers

### Scenario 1

Question:

```text
How many units of SKU-1042 should I buy for C-EAST for the next 8 weeks?
```

Answer:

```text
SKU-1042 / C-EAST: forecast 275 units for the next 8 weeks.
Recommended buy = 318 units, including 43 safety-stock units.
```

### Scenario 2

Question:

```text
What is the forecast for SKU-2017 in C-WEST, and what's driving it?
```

Answer:

```text
SKU-2017 / C-WEST: forecast 192 units for the next 8 weeks.
Recommended buy = 241 units, including 49 safety-stock units.
```

The knowledge context explains that parent-beverage demand matters and that `C-WEST` is more promotion responsive.

### Scenario 3

Question:

```text
If the supplier runs a co-marketing promotion on the parent brand for weeks 3-5,
how should I adjust my buy for headwear in C-EAST?
```

Answer:

```text
Headwear in C-EAST: baseline 8-week forecast is 3,280 units.
With co-marketing in weeks 3-5, forecast is 4,162 units.
Add about 883 units.
```

### Scenario 4

Question:

```text
Compare the forecast for SKU-3008 in C-EAST versus C-WEST.
Why are they different?
```

Answer:

```text
SKU-3008 / C-EAST: forecast 122 units.
Recommended buy = 187 units, including 65 safety-stock units.

SKU-3008 / C-WEST: forecast 104 units.
Recommended buy = 155 units, including 50 safety-stock units.
```

The difference is driven by cluster behavior and historical demand. `C-EAST` has higher overall volume, while `C-WEST` has different retailer and promotional characteristics.

### Scenario 5

Question:

```text
What is the supplier promotion calendar telling me to expect in Q3?
```

Answer:

The calendar highlights:

- Weeks 26-29: Maple Hollow Ale, Apparel, Co-Marketing, C-EAST
- Weeks 27-30: Solano Tequila, Drinkware, Display, C-WEST
- Weeks 35-37: Crestmark Bourbon, Drinkware/Apparel, Co-Marketing, ALL
- Weeks 32-34: tentative Northwind x Solano collaboration

### Scenario 6

Question:

```text
What is the safety stock policy for new SKUs, and how does it affect my buy for SKU-2099?
```

Answer:

```text
SKU-2099 / C-EAST: forecast 697 units for the next 8 weeks.
Recommended buy = 786 units, including 88 safety-stock units.
```

The safety-stock policy adds buffer inventory above expected demand. For Apparel, the lead time is 6 weeks. New SKUs use lower service-level targets and parent/category volatility when needed.

Agent outputs:

- `outputs/agent_evaluation.csv`
- `outputs/agent_answers.md`

---

# Part C — Production Thinking

## Proposed Production Architecture

```text
Weekly sales + promotions + parent-beverage sales
        |
        v
Data checks -> feature table -> nightly forecast batch
        |                         |
        v                         v
Planner API/UI -> planning agent -> forecast tool + knowledge retrieval
```

## Forecast Computation

Forecasts should be computed in two ways:

1. Nightly batch forecasts
2. On-demand what-if forecasts

Nightly forecasts are useful because the planning UI can load results quickly and teams can work from a stable forecast snapshot. On-demand forecasts are useful when a planner changes assumptions, such as extending a promotion or adjusting the cluster scope.

## Retraining

The model should retrain weekly after the newest sales week is finalized. Before replacing the current model, the new model should be tested on a recent holdout period. If WAPE or bias gets worse, the model should not be promoted automatically.

## Monitoring

Model monitoring:

- SKU-level WAPE
- forecast bias by category and cluster
- interval coverage

Agent monitoring:

- planner route accuracy
- tool error rate
- user acceptance or override rate

This separation helps the team understand whether a problem is caused by the forecast model, the source data, or the agent/retrieval layer.

Production output:

- `outputs/production_design.md`

---

# How to Run the Solution

From the project root:

```bash
.vip_venv/bin/pip install -r code/requirements.txt
.vip_venv/bin/python code/main.py
```

Expected final console output:

```text
Solution complete. See code/outputs.
Full model WAPE: 0.164
Baseline WAPE: 0.170
```

---

# Important Files

Code:

- `code/main.py`
- `code/README.md`
- `code/requirements.txt`

Model artifact:

- `code/artifacts/forecaster.joblib`

Outputs:

- `outputs/eda_summary.md`
- `outputs/model_notes.md`
- `outputs/model_summary.csv`
- `outputs/wape_by_sku.csv`
- `outputs/agent_evaluation.csv`
- `outputs/agent_answers.md`
- `outputs/production_design.md`
- `outputs/validation_checklist.md`

---

# Assumptions and Simplifications

1. The planner is deterministic rather than LLM-driven. This keeps the project runnable without API keys.
2. The Random Forest is chosen for simplicity and robustness, not because it is the only possible model.
3. Forecast intervals use holdout residual percentiles, which are transparent and explainable.
4. The agentic layer is a prototype. In production, the planner could be replaced with a stronger LangGraph or LLM-based router.
5. The safety-stock calculation is simplified but follows the provided policy direction.

---

# Final Recommendation

This version is intentionally practical. It demonstrates that:

- demand was explored before modeling,
- promotions and parent-beverage demand are useful signals,
- an 8-week SKU x cluster forecast can be generated,
- uncertainty and WAPE evaluation are included,
- a small three-agent decision-support system can answer planner questions,
- and the production path is clear.

For the assessment, the root-level `code` folder is the recommended version to present because it is easier to understand and explain end to end.
