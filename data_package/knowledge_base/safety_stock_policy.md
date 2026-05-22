# Safety Stock Policy — Branded Merchandise

This policy defines the safety stock methodology for branded merchandise SKUs in distributor inventory.

## Definitions

**Safety stock** is the buffer inventory held above expected demand to absorb forecast error, supply variability, and unexpected demand spikes.

**Service level** is the probability of not running out of stock during the lead time. For branded merchandise, the target service level varies by category and SKU status.

## Service level targets

| Category | New SKU (first 12 wks) | Established SKU |
|---|---|---|
| Headwear | 92% | 95% |
| Apparel | 90% | 95% |
| Drinkware | 95% | 97% (98% Q4) |
| Accessories | 90% | 92% |

New SKU targets are intentionally lower. We do not yet know the demand distribution well enough to justify a high service level — the safety stock would be guesswork and the cost of carrying it is real.

## Calculation method

Safety stock should be computed as:

```
SS = z * sigma_LT
```

where `z` is the service-level multiplier (1.65 for 95%, 1.96 for 97.5%, 2.33 for 99%) and `sigma_LT` is the standard deviation of demand during the lead time period.

For new SKUs without enough data to estimate `sigma_LT` directly, use the parent-category historical sigma adjusted by a 1.5x multiplier to account for launch variability.

## Lead times by category

Default lead times to assume for safety-stock sizing:

- Apparel: 6 weeks
- Headwear: 4 weeks
- Drinkware: 5 weeks (8 weeks Q4)
- Accessories: 3 weeks

## When safety stock is suspended

Safety stock requirements are suspended in two situations:

1. The SKU is in its launch ramp (first 4 weeks since launch date). Stock to expected demand only.
2. The SKU is end-of-life and you have an EOL notice from the supplier. Run the inventory down.

## Q4 over-stock guidance

During the Q4 drinkware window, safety stock multipliers are elevated due to the cost of stockout in the holiday period. However, this is balanced by an EOL writedown risk in January if the drinkware is holiday-themed. The current guidance is: target a 98% service level through Week 50, then begin actively drawing down inventory.

## Promotion windows

Safety stock targets apply to baseline demand only. Promotion-driven demand is treated as known incremental — distributors should commit to the supplier-published promo quantities through the promo PO process, not absorb them via safety stock.
