# August 2026 1% risk — not re-run for cover-only shorts

Cover-only shorts (`action.exit: ma_cross`, no `stop_loss_pct`, no `lock_plus`) have **no stop distance R**. `size.type: risk_pct` cannot size those shorts. The risk YAML now keeps shorts at 10 shares.

This file previously held August 1% A/B/C numbers for shorts that still used a 1.0% fill stop / lock_plus. Those figures **do not apply** to the current cover-only short.

August 10-share cover-only shorts on the same tape are in `artifacts/ema9_long_short_15m.md` (August row: 20 trades, 40.00%, $-159.74). Long-only August 1% (unchanged long rule) last reproduced **15 trades, 73.33%, $5,489.78** and was not needed again for this short-exit change.
