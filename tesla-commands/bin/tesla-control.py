#!/usr/bin/env python3
import json
import sys
import argparse
import urllib.request
import os
import asyncio
import websockets
from datetime import datetime

# Configuration should come from Environment Variables
TOKEN = os.environ.get("TESLA_MATE_TOKEN")
DEFAULT_VIN = os.environ.get("TESLA_VIN")
API_BASE = "https://api.myteslamate.com/api/1/vehicles"
STREAM_URI = "wss://streaming.myteslamate.com/streaming/"

def call_api(path, method="GET", data=None, vin=None):
    if not TOKEN:
        print(json.dumps({"error": "Missing TESLA_MATE_TOKEN environment variable."}))
        sys.exit(1)
    
    target_vin = vin or DEFAULT_VIN
    url = f"{API_BASE}/{target_vin}/{path}" if path else API_BASE
    
    # MyTeslaMate needs token in query for some endpoints or headers for others.
    # We'll use query parameter and a custom User-Agent to avoid 403s.
    separator = "&" if "?" in url else "?"
    url += f"{separator}token={TOKEN}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "curl/8.0.1"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        if data is not None:
            body = json.dumps(data).encode('utf-8')
            with urllib.request.urlopen(req, data=body) as response:
                return json.loads(response.read().decode())
        else:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return {"error": f"HTTP {e.code}", "message": json.loads(e.read().decode())}
        except:
            return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}

async def listen_stream(vin, limit=5, timeout=30):
    if not TOKEN or not vin:
        print(json.dumps({"error": "Missing token or VIN"}))
        return

    headers = {"User-Agent": "curl/8.0.1"}
    try:
        async with websockets.connect(STREAM_URI, additional_headers=headers) as websocket:
            auth_msg = {
                "msg_type": "data:subscribe_all",
                "tag": vin,
                "token": TOKEN
            }
            await websocket.send(json.dumps(auth_msg))
            
            count = 0
            start_time = datetime.now()
            while count < limit:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    break
                
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(msg)
                    count += 1
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        print(json.dumps({"error": str(e)}))

def main():
    parser = argparse.ArgumentParser(description="Tesla Control via MyTeslaMate API")
    parser.add_argument("--vin", help="Specify vehicle VIN")
    parser.add_argument("--list", action="store_true", help="List all vehicles")
    parser.add_argument("--status", action="store_true", help="Get vehicle status")
    parser.add_argument("--telemetry-config", action="store_true", help="Get telemetry configuration")
    parser.add_argument("--stream", type=int, nargs='?', const=5, help="Listen to telemetry stream (default 5 messages)")
    parser.add_argument("--wake", action="store_true", help="Wake up the vehicle")
    parser.add_argument("--climate", choices=["on", "off"], help="Turn climate on or off")
    parser.add_argument("--charge-limit", type=int, help="Set charge limit (50-100)")
    parser.add_argument("--set-schedule", help="Set charging start time (HH:MM)")
    parser.add_argument("--clear-schedule", action="store_true", help="Clear charging schedule")
    parser.add_argument("--remove-schedules", action="store_true", help="Completely remove all charge schedules")
    
    args = parser.parse_args()
    target_vin = args.vin or DEFAULT_VIN

    if args.list:
        print(json.dumps(call_api("")))
    elif args.wake:
        print(json.dumps(call_api("wake_up", method="POST", vin=args.vin)))
    elif args.status:
        # vehicle_data is the most reliable endpoint now
        print(json.dumps(call_api("vehicle_data", vin=args.vin)))
    elif args.telemetry_config:
        print(json.dumps(call_api("fleet_telemetry_config", vin=args.vin)))
    elif args.stream:
        asyncio.run(listen_stream(target_vin, limit=args.stream))
    elif args.climate:
        action = "auto_conditioning_start" if args.climate == "on" else "auto_conditioning_stop"
        print(json.dumps(call_api(f"command/{action}", method="POST", vin=args.vin)))
    elif args.charge_limit:
        print(json.dumps(call_api("command/set_charge_limit", method="POST", data={"percent": args.charge_limit}, vin=args.vin)))
    elif args.set_schedule:
        try:
            h, m = map(int, args.set_schedule.split(":"))
            minutes = h * 60 + m
            payload = {"enable": True, "time": minutes}
            print(json.dumps(call_api("command/set_scheduled_charging", method="POST", data=payload, vin=args.vin)))
        except ValueError:
            print(json.dumps({"error": "Invalid time format. Use HH:MM"}))
    elif args.clear_schedule:
        print(json.dumps(call_api("command/set_scheduled_charging", method="POST", data={"enable": False}, vin=args.vin)))
    elif args.remove_schedules:
        print(json.dumps(call_api("command/remove_charge_schedule", method="POST", data={}, vin=args.vin)))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
