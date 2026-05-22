# Take-Home Assessment — Data Package

This package contains the synthetic data referenced in the take-home assessment brief. It is generated for the purpose of this evaluation only.

## Contents

```
data_package/
├── merch_sales_weekly.csv        Primary sell-in table, weekly grain
├── sku_master.csv                SKU metadata (40 SKUs)
├── parent_beverage_sales.csv     Parent-brand weekly sales by cluster
├── promotions.csv                Supplier-funded promotion events
└── knowledge_base/               8 markdown documents for the Knowledge Agent
    ├── supplier_promo_calendar_FY26.md
    ├── planogram_policy_apparel.md
    ├── planogram_policy_drinkware.md
    ├── seasonal_buy_windows.md
    ├── distributor_onboarding_branded_merch.md
    ├── safety_stock_policy.md
    ├── cluster_definitions.md
    └── price_pass_through_policy.md
```

## Time window

The data covers 78 weeks of history ending 11 May 2026 (a Monday). Treat 11 May 2026 as "today" for forecasting purposes — the next 8 weeks would be the forecast horizon.

## SKUs referenced in the evaluation scenarios

The evaluation scenarios in Appendix C reference these specific SKUs:

- `SKU-1042` — Headwear, long history
- `SKU-2017` — Apparel, short history (launched January 2026)
- `SKU-3008` — Drinkware, long history, present in both clusters
- `SKU-2099` — Apparel, recently launched (December 2025)

## Notes

- All identifiers (SKUs, brands, distributors) are fictional.
- The data is synthetic and does not represent any real company or product line.
- The schemas match what's described in Appendix A of the brief.
