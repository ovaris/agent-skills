#!/usr/bin/env python3
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

def get_data():
    url = "https://api.porssisahko.net/v2/latest-prices.json"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def to_local(utc_str):
    # Finland: UTC+2 (Winter), UTC+3 (Summer)
    # This detects the offset automatically based on the system or fixed offset
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    return dt.astimezone(timezone(timedelta(hours=2)))

def find_best_window(prices, window_size):
    if len(prices) < window_size:
        return None
    
    best_avg = float('inf')
    best_window = None
    
    for i in range(len(prices) - window_size + 1):
        window = prices[i:i+window_size]
        avg = sum(p['price'] for p in window) / window_size
        if avg < best_avg:
            best_avg = avg
            best_window = {
                "start": window[0]['time'],
                "end": (datetime.strptime(window[-1]['time'], '%Y-%m-%d %H:00') + timedelta(hours=1)).strftime('%Y-%m-%d %H:00'),
                "avg_price": round(avg, 2)
            }
    return best_window

def main():
    try:
        data = get_data()
        now = datetime.now(timezone(timedelta(hours=2)))
        
        # Group and calculate hourly averages (Finland time)
        hourly = {}
        for p in data['prices']:
            local_dt = to_local(p['startDate'])
            hour_key = local_dt.strftime('%Y-%m-%d %H:00')
            if hour_key not in hourly:
                hourly[hour_key] = []
            hourly[hour_key].append(p['price'])

        averages = []
        for h, prices in hourly.items():
            averages.append({"time": h, "price": sum(prices)/len(prices)})
        averages.sort(key=lambda x: x['time'])

        # Filter only future prices (from current hour onwards)
        now_hour = now.replace(minute=0, second=0, microsecond=0)
        future_prices = [a for a in averages if datetime.strptime(a['time'], '%Y-%m-%d %H:00').replace(tzinfo=timezone(timedelta(hours=2))) >= now_hour]

        today_str = now.strftime('%Y-%m-%d')
        tomorrow_str = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        current_price = next((a['price'] for a in averages if a['time'] == now.strftime('%Y-%m-%d %H:00')), None)
        
        result = {
            "current_price": current_price,
            "best_charging_windows": {
                "3h": find_best_window(future_prices, 3),
                "4h": find_best_window(future_prices, 4),
                "5h": find_best_window(future_prices, 5)
            },
            "today_stats": {
                "average": sum(a['price'] for a in averages if today_str in a['time']) / len([a for a in averages if today_str in a['time']]) if any(today_str in a['time'] for a in averages) else None,
                "min": min([a for a in averages if today_str in a['time']], key=lambda x: x['price']) if any(today_str in a['time'] for a in averages) else None,
                "max": max([a for a in averages if today_str in a['time']], key=lambda x: x['price']) if any(today_str in a['time'] for a in averages) else None
            }
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
