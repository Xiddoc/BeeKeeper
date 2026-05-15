# DateRange Semantics

`DateRange` is generic over `T: date = datetime`. The default is datetime granularity; subclass with `DateRange[date]` for whole-day ranges.

## Inclusive on both ends

A `DateRange` is **inclusive on both ends**. A range from June 1 to June 3 covers June 1, June 2, *and* June 3. This matches how shifts and unavailabilities are typically described in scheduling domains ("I'm out from the 1st to the 3rd" usually means three days, not two).

The two day-count properties make this explicit:

```python
r = DateRange(start_date=date(2025, 6, 1), end_date=date(2025, 6, 3))
r.inclusive_day_count   # 3 — counts June 1, 2, 3
r.days                  # 2 — matches stdlib (end - start).days, exclusive
```

Use `inclusive_day_count` when "active days on duty" is what you mean. Use `days` when you want elapsed time, matching standard library conventions.

## Validation

`DateRange` validates two things at construction:

1. **`end_date >= start_date`.** A reversed range raises `ValueError` rather than producing a negative day count.
2. **Timezone consistency.** When `T` is `datetime`, `start_date` and `end_date` must agree on tz-awareness — both naïve, or both aware. Mixing the two makes comparisons raise `TypeError` at unpredictable times in your code; failing at construction surfaces the problem at the boundary.

## Tz-aware vs. tz-naïve

The framework doesn't care which you pick — both are valid — but be consistent across your domain. JSON fixtures with ISO timestamps like `2025-06-01T00:00:00` deserialize as naïve `datetime`s. Add `+00:00` or `Z` to make them aware.

## When to choose `date` over `datetime`

If your domain's allocations are whole-day shifts (no time-of-day), `DateRange[date]` (and `Unavailability[date]`) is more honest about what's modeled. A 9-to-5 schedule with hour granularity wants `datetime`. The default keeps the most-common `datetime` path frictionless.
