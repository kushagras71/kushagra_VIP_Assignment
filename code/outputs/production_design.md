# Production Design

```text
Weekly sales + promotions + parent-beverage sales
        |
        v
Data checks -> feature table -> nightly forecast batch
        |                         |
        v                         v
Planner API/UI -> simple agent -> forecast tool + knowledge retrieval
```

I would compute forecasts nightly after weekly data is finalized, and also allow on-demand what-if forecasts for planner scenarios such as promotion changes. Nightly batch forecasts keep the planning UI fast and give teams a stable forecast snapshot. The model should retrain weekly after the newest sales week lands, with a holdout backtest check before replacing the current model.

Model monitoring should track SKU-level WAPE, forecast bias by category/cluster, and interval coverage. Agent monitoring should track route accuracy, tool error rate, and whether users accept or override recommendations. If quality drops, the team can tell whether the issue is the demand model, the source data, or the planner/knowledge retrieval layer.
