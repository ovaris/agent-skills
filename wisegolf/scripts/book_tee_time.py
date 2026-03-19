#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import date, datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def http_json(url, method='GET', headers=None, data=None):
    req = Request(url, method=method, headers=headers or {}, data=data)
    with urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return json.loads(body) if body else {}


def compact_price(value):
    text = str(value)
    if text.endswith('.00'):
        return text[:-3]
    return text


parser = argparse.ArgumentParser(description='Create a WiseGolf tee time booking with the richer payload shape used by some clubs.')
parser.add_argument('--api-domain', required=True)
parser.add_argument('--ajax-domain', required=True)
parser.add_argument('--username', required=True)
parser.add_argument('--password', required=True)
parser.add_argument('--app-id', required=True)
parser.add_argument('--version', required=True)
parser.add_argument('--product-id', required=True, type=int)
parser.add_argument('--date', required=True, help='YYYY-MM-DD')
parser.add_argument('--start', required=True, help='YYYY-MM-DD HH:MM:SS')
parser.add_argument('--end', required=True, help='YYYY-MM-DD HH:MM:SS')
parser.add_argument('--club-id', required=True, type=int)
parser.add_argument('--firstname', required=True)
parser.add_argument('--familyname', required=True)
parser.add_argument('--memberno', default='')
parser.add_argument('--price', default=None)
parser.add_argument('--resource-index', type=int, default=0)
parser.add_argument('--add-category-id', type=int, default=None)
parser.add_argument('--title', default=None)
args = parser.parse_args()

api_base = f'https://{args.api_domain}/api/1.0'

# auth
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
access_token = login['access_token']
auth_headers = {'Authorization': f'token {access_token}'}

# settings
settings = http_json(
    f"{api_base}/reservations/calendarsettings/?{urlencode({'productid': args.product_id, 'date': args.date})}",
    headers=auth_headers,
)
reservation = settings['reservationSettings']
resource = dict(reservation['resources'][args.resource_index])
resource['quantity'] = 1

# player
player_query = urlencode({
    'memberno': args.memberno,
    'clubid': args.club_id,
    'firstname': args.firstname,
    'familyname': args.familyname,
})
player_data = http_json(f'{api_base}/golf/player/?{player_query}', headers=auth_headers)
player = dict(player_data['rows'][0])
if 'age' not in player and login.get('dateOfBirth'):
    dob = datetime.strptime(login['dateOfBirth'], '%Y-%m-%d').date()
    on_date = date.fromisoformat(args.date)
    player['age'] = on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))

price = args.price or reservation.get('price') or resource.get('productPrice')
body = {
    'products': [{
        'productId': str(args.product_id),
        'productVariantId': 0,
        'quantity': 1,
        'reservation': {
            'reservationId': reservation['reservationId'],
            'title': args.title or resource.get('resourceName') or 'Tee time',
            'duration': reservation['duration'],
            'fullDuration': reservation['duration'],
            'price': compact_price(price),
            'start': args.start,
            'end': args.end,
            'quantity': 1,
            'resources': [resource],
            'recurringReservation': False,
        },
        'golfPlayers': [player],
        'golfPersonIds': [player['personId']],
        'golfPlayersTotal': 1,
        'golfPlayersHandicapTotal': player['handicapActive'],
        'checkedComments': [],
    }]
}
if args.add_category_id is not None:
    body['products'][0]['addCategoryId'] = args.add_category_id

result = http_json(
    f'{api_base}/reservations/order/2',
    method='POST',
    headers={'Content-Type': 'application/json', **auth_headers},
    data=json.dumps(body).encode(),
)
json.dump(result, sys.stdout, ensure_ascii=False)
print()
