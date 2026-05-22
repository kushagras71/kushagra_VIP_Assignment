# Model Notes

I used a Random Forest regression model with a compact feature set:

- recent SKU x cluster demand lags: 1, 2, and 4 weeks,
- a 4-week rolling average,
- price, calendar week, month, category, cluster, and parent brand,
- supplier promotion flag/type,
- parent-beverage weekly units.

Why this model: the history is short, demand is seasonal and promotion-driven, and several SKUs are new. A Random Forest handles nonlinear relationships without requiring a lot of tuning.

Holdout evaluation uses the last 8 historical weeks: 2026-03-23 to 2026-05-11.

- Full model WAPE: 0.164
- Baseline WAPE without promotion and parent-beverage signals: 0.170

The full model is better, so the available signals are useful.

Uncertainty: forecast intervals use the 10th and 90th percentile residuals from the holdout period. This is transparent, explainable, and appropriate for a prototype.
