#!/usr/bin/env python3
import argparse
import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def http_json(url, method='GET', headers=None, data=None):
    req = Request(url, method=method, headers=headers or {}, data=data)
    with urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return json.loads(body) if body else {}


parser = argparse.ArgumentParser(description='Cancel a WiseGolf tee time row by reservationTimeId.')
parser.add_argument('--api-domain', required=True)
parser.add_argument('--ajax-domain', required=True)
parser.add_argument('--username', required=True)
parser.add_argument('--password', required=True)
parser.add_argument('--app-id', required=True)
parser.add_argument('--version', required=True)
parser.add_argument('--appauth', required=True)
parser.add_argument('--reservation-time-id', required=True, type=int)
args = parser.parse_args()

api_base = f'https://{args.api_domain}/api/1.0'
ajax_base = f'https://{args.ajax_domain}/'

login = http_json(
    f'{api_base}/auth',
    method='POST',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'username': args.username,
        'password': args.password,
        'appId': args.app_id,
        'version': args.version,
    }).encode(),
)
headers = {'Authorization': f"token {login['access_token']}"}

query = urlencode({
    'reservations': 'deactivatereservationtime',
    'reservationtimeid': args.reservation_time_id,
    'appauth': args.appauth,
})
result = http_json(f'{ajax_base}?{query}', headers=headers)
json.dump(result, sys.stdout, ensure_ascii=False)
print()
