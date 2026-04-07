---
name: nordpool-fi
description: Hourly electricity prices for Finland with optimal EV charging window calculation (3h, 4h, 5h).
metadata: {"tags": ["energy", "finland", "nordpool", "electricity", "ev-charging"]}
---

# Nordpool Finland Energy Prices 🇫🇮

Hourly electricity prices for Finland with optimal EV charging window calculation (3h, 4h, 5h).

This skill fetches hourly electricity prices for Finland using the Porssisahko.net API. It converts timestamps using the real `Europe/Helsinki` timezone, so Finnish summer/winter time shifts are handled correctly.

## Tools

### nordpool-fi

Fetch current prices, daily stats, and optimal charging windows.

**Usage:**
`public-skills/nordpool-fi/bin/nordpool-fi.py`

**Output Format (JSON):**
- `timezone`: Always `Europe/Helsinki`
- `unit`: Always `c/kWh`
- `current_price`: Current 15 min interval price (`c/kWh`)
- `current_hour_avg`: Current hour average (`c/kWh`)
- `best_charging_windows`: Optimal consecutive hours (3h, 4h, 5h) for charging
- `today_stats`: Daily average, min, and max prices, all in `c/kWh`

## Examples

Get optimal 4h window:
```bash
public-skills/nordpool-fi/bin/nordpool-fi.py | jq '.best_charging_windows["4h"]'
```
