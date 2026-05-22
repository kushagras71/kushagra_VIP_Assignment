# EDA Summary

- Data contains 4,486 rows, 40 SKUs, and 2 clusters.
- Date range: 2024-11-18 to 2026-05-11.
- The grain is SKU x cluster x week, exactly as requested in the brief.

## Demand Distribution
| index | units_sold |
| ----- | ---------- |
| count | 4486.0     |
| mean  | 28.19      |
| std   | 19.05      |
| min   | 0.0        |
| 25%   | 15.0       |
| 50%   | 23.0       |
| 75%   | 35.0       |
| 90%   | 53.0       |
| max   | 157.0      |

## Category Demand
| category    | count | mean  | median | sum   |
| ----------- | ----- | ----- | ------ | ----- |
| Accessories | 1110  | 20.44 | 19.0   | 22690 |
| Apparel     | 1328  | 28.76 | 23.0   | 38194 |
| Drinkware   | 978   | 41.97 | 37.0   | 41050 |
| Headwear    | 1070  | 22.93 | 20.0   | 24539 |

## Cluster Demand
| cluster_id | mean  | median | sum   |
| ---------- | ----- | ------ | ----- |
| C-EAST     | 35.94 | 30.0   | 80615 |
| C-WEST     | 20.44 | 17.0   | 45858 |

## Representative SKU Intermittency
| sku_id   | cluster_id | weeks | avg_units | zero_weeks |
| -------- | ---------- | ----- | --------- | ---------- |
| SKU-1042 | C-EAST     | 78    | 28.54     | 0          |
| SKU-1042 | C-WEST     | 78    | 17.59     | 0          |
| SKU-2017 | C-EAST     | 19    | 27.42     | 0          |
| SKU-2017 | C-WEST     | 19    | 21.68     | 0          |
| SKU-2099 | C-EAST     | 21    | 51.95     | 0          |
| SKU-2099 | C-WEST     | 21    | 19.62     | 0          |
| SKU-3008 | C-EAST     | 78    | 36.83     | 0          |
| SKU-3008 | C-WEST     | 78    | 23.67     | 0          |

## Parent Beverage Relationship
Median lagged correlation between merchandise units and parent-beverage units:
| lag_weeks | corr  |
| --------- | ----- |
| 0         | 0.138 |
| 1         | 0.295 |
| 2         | 0.197 |
| 3         | 0.061 |
| 4         | 0.057 |

## Promotion Impact
| category    | non_promo_avg | promo_avg | lift_pct |
| ----------- | ------------- | --------- | -------- |
| Accessories | 19.89         | 39.09     | 96.6     |
| Apparel     | 28.57         | 45.4      | 58.9     |
| Drinkware   | 41.1          | 82.0      | 99.5     |
| Headwear    | 22.41         | 38.85     | 73.4     |

Key observations:
- Demand is not flat: C-EAST is materially larger than C-WEST and categories differ a lot.
- Parent beverage sales have a positive but imperfect relationship with merchandise demand, strongest around short lags.
- Promotion weeks show clear lift, so promotion features belong in the model.