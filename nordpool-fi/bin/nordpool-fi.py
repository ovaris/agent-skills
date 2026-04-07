#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HELSINKI_TZ = ZoneInfo("Europe/Helsinki")
UNIT = "c/kWh"


def get_data():
    url = "https://api.porssisahko.net/v2/latest-prices.json"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def parse_utc(utc_str):
    return datetime.fromisoformat(utc_str.replace("Z", "+00:00"))


def to_local(dt):
    return dt.astimezone(HELSINKI_TZ)


def round_price(value):
    return round(value, 2) if value is not None else None


def serialize_hour(entry):
    return {
        "time": entry["time"],
        "price": round_price(entry["price"]),
        "unit": UNIT,
    }


def find_best_window(prices, window_size):
    if len(prices) < window_size:
        return None

    best_avg = float("inf")
    best_window = None

    for i in range(len(prices) - window_size + 1):
        window = prices[i:i + window_size]
        avg = sum(p["price"] for p in window) / window_size
        if avg < best_avg:
            best_avg = avg
            best_window = {
                "start": window[0]["time"],
                "end": (window[-1]["dt"] + timedelta(hours=1)).strftime("%Y-%m-%d %H:00"),
                "avg_price": round_price(avg),
                "unit": UNIT,
            }
    return best_window


def main():
    try:
        data = get_data()
        now_utc = datetime.now(timezone.utc)
        now_local = to_local(now_utc)
        now_hour = now_local.replace(minute=0, second=0, microsecond=0)

        current_interval_price = None
        for price_row in data["prices"]:
            start = parse_utc(price_row["startDate"])
            end = parse_utc(price_row["endDate"])
            if start <= now_utc < end:
                current_interval_price = price_row["price"]
                break

        hourly = {}
        for price_row in data["prices"]:
            local_dt = to_local(parse_utc(price_row["startDate"]))
            hour_dt = local_dt.replace(minute=0, second=0, microsecond=0)
            hourly.setdefault(hour_dt, []).append(price_row["price"])

        averages = []
        for hour_dt, prices in sorted(hourly.items()):
            averages.append(
                {
                    "dt": hour_dt,
                    "time": hour_dt.strftime("%Y-%m-%d %H:00"),
                    "price": sum(prices) / len(prices),
                }
            )

        future_prices = [entry for entry in averages if entry["dt"] >= now_hour]
        today_prices = [entry for entry in averages if entry["dt"].date() == now_local.date()]
        current_hour_avg = next(
            (entry["price"] for entry in averages if entry["dt"] == now_hour),
            None,
        )

        result = {
            "timezone": "Europe/Helsinki",
            "unit": UNIT,
            "current_price": round_price(current_interval_price),
            "current_hour_avg": round_price(current_hour_avg),
            "best_charging_windows": {
                "3h": find_best_window(future_prices, 3),
                "4h": find_best_window(future_prices, 4),
                "5h": find_best_window(future_prices, 5),
            },
            "today_stats": {
                "average": round_price(
                    sum(entry["price"] for entry in today_prices) / len(today_prices)
                ) if today_prices else None,
                "min": serialize_hour(min(today_prices, key=lambda x: x["price"])) if today_prices else None,
                "max": serialize_hour(max(today_prices, key=lambda x: x["price"])) if today_prices else None,
            },
        }

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
