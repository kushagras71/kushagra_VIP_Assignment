# Agent Evaluation

## Graph
```text
Planner Agent -> Forecasting Agent -> forecast_merchandise_demand tool
              -> Knowledge Agent   -> retrieve_merchandise_knowledge tool
              -> answer + short memory update
```

## Rubric
5 = correct route, valid tool call, useful grounded answer; 3 = partially useful; 1 = unusable.

## Scenario 1
How many units of SKU-1042 (the co-branded headwear) should I buy for C-EAST for the next 8 weeks?

SKU-1042 / C-EAST: forecast 275 units for the next 8 weeks. Recommended buy = 318 units, including 43 safety-stock units.

## Scenario 2
What is the forecast for SKU-2017 in C-WEST, and what's driving it?

SKU-2017 / C-WEST: forecast 192 units for the next 8 weeks. Recommended buy = 241 units, including 49 safety-stock units.

Knowledge context: [distributor_onboarding_branded_merch.md] **The parent beverage signal matters.** Co-branded merchandise demand is partially driven by parent-brand beverage demand. If Crestmark Bourbon is having a strong quarter, expect Crestmark drinkware to follow. The lag varies by category — drinkware tends to be near-simultaneous, apparel and headwear lag the beverage by a few weeks. This is not always intuitive and is best discovered by examining your own historical data.  ## Onboarding checklist  In your first cycle:  - Start with at most 6–8 SKUs per cluster. Do not try to carry the full range. - Commit to a 90% sell-through target, not a coverage target. - Tag every PO with the parent brand [cluster_definitions.md] ## C-WEST  States: CA, OR, WA, NV, AZ, NM, CO, UT, ID, MT, WY.  Distribution centres: Stockton CA (primary), Portland OR (secondary), Phoenix AZ (secondary).  Retailer count: approximately 2,800 active outlets.  Profile: lower overall volume than C-EAST but higher per-store. Tequila and craft beer programs are notably stronger. The cluster is more responsive to promotional activity — historical lift on co-marketing windows runs 20–25% higher in C-WEST than in C-EAST.  

## Scenario 3
If the supplier runs a co-marketing promotion on the parent brand for weeks 3-5, how should I adjust my buy for headwear in C-EAST?

Headwear in C-EAST: baseline 8-week forecast is 3280 units. With co-marketing in weeks 3-5, forecast is 4162. Add about 883 units.

Knowledge context: [supplier_promo_calendar_FY26.md] # Supplier Promotion Calendar — FY26 [distributor_onboarding_branded_merch.md] # Distributor Onboarding — Branded Merchandise

## Scenario 4
Compare the forecast for SKU-3008 in C-EAST versus C-WEST. Why are they different?

SKU-3008 / C-EAST: forecast 122 units for the next 8 weeks. Recommended buy = 187 units, including 65 safety-stock units.

SKU-3008 / C-WEST: forecast 104 units for the next 8 weeks. Recommended buy = 155 units, including 50 safety-stock units.

Knowledge context: [cluster_definitions.md] ## C-WEST  States: CA, OR, WA, NV, AZ, NM, CO, UT, ID, MT, WY.  Distribution centres: Stockton CA (primary), Portland OR (secondary), Phoenix AZ (secondary).  Retailer count: approximately 2,800 active outlets.  Profile: lower overall volume than C-EAST but higher per-store. Tequila and craft beer programs are notably stronger. The cluster is more responsive to promotional activity — historical lift on co-marketing windows runs 20–25% higher in C-WEST than in C-EAST.   [distributor_onboarding_branded_merch.md] **The parent beverage signal matters.** Co-branded merchandise demand is partially driven by parent-brand beverage demand. If Crestmark Bourbon is having a strong quarter, expect Crestmark drinkware to follow. The lag varies by category — drinkware tends to be near-simultaneous, apparel and headwear lag the beverage by a few weeks. This is not always intuitive and is best discovered by examining your own historical data.  ## Onboarding checklist  In your first cycle:  - Start with at most 6–8 SKUs per cluster. Do not try to carry the full range. - Commit to a 90% sell-through target, not a coverage target. - Tag every PO with the parent brand

## Scenario 5
What is the supplier promotion calendar telling me to expect in Q3?

Knowledge context: [supplier_promo_calendar_FY26.md] | Wk 26–29 (Jul) | Maple Hollow Ale | Apparel | Co-Marketing | 60% | C-EAST | | Wk 27–30 (Jul) | Solano Tequila | Drinkware | Display | 25% | C-WEST | | Wk 35–37 (Sep) | Crestmark Bourbon | Drinkware, Apparel | Co-Marketing | 50% | ALL | - Wk 32–34 (Aug 2026): possible cross-brand collaboration (Northwind × Solano) — drinkware and apparel. [distributor_onboarding_branded_merch.md] # Distributor Onboarding — Branded Merchandise

## Scenario 6
What is the safety stock policy for new SKUs, and how does it affect my buy for SKU-2099?

SKU-2099 / C-EAST: forecast 697 units for the next 8 weeks. Recommended buy = 786 units, including 88 safety-stock units.

Knowledge context: [safety_stock_policy.md] | Apparel | 90% | 95% | SS = z * sigma_LT - Apparel: 6 weeks 1. The SKU is in its launch ramp (first 4 weeks since launch date). Stock to expected demand only. [distributor_onboarding_branded_merch.md] # Distributor Onboarding — Branded Merchandise

## Memory Demo
Turn 1:
SKU-1042 / C-EAST: forecast 275 units for the next 8 weeks. Recommended buy = 318 units, including 43 safety-stock units.

Turn 2:
Using remembered context SKU-1042/C-EAST: extending promo weeks 3-7 changes forecast from 275 to 394. Add about 119 units before safety stock.

Knowledge context: [distributor_onboarding_branded_merch.md] # Distributor Onboarding — Branded Merchandise [cluster_definitions.md] # Cluster Definitions
