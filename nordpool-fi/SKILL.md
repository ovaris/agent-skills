# Nordpool Finland Energy Prices 🇫🇮

This skill fetches hourly electricity prices for Finland using the Porssisahko.net API. It handles UTC conversions to Finland time and provides helpful summaries for energy-intensive tasks like EV charging.

## Tools

### nordpool-fi

Fetch current prices, daily stats, and optimal charging windows.

**Usage:**
`public-skills/nordpool-fi/bin/nordpool-fi.py`

**Output Format (JSON):**
- `current_price`: Current hour price (snt/kWh)
- `best_charging_windows`: Optimal consecutive hours (3h, 4h, 5h) for charging.
- `today_stats`: Daily average, min, and max prices.

## Examples

Get optimal 4h window:
```bash
public-skills/nordpool-fi/bin/nordpool-fi.py | jq .best_charging_windows.4h
```
