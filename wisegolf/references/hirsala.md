# Hirsala Golf booking notes

Use these notes when a WiseGolf booking works at Hirsala in the web app but a minimal API payload fails with HTTP 500.

## Observed working flow

1. Authenticate:

```http
POST https://api.hirsalagolf.fi/api/1.0/auth
```

2. Fetch tee-time settings for the requested product/date:

```http
GET https://api.hirsalagolf.fi/api/1.0/reservations/calendarsettings/?productid=7&date=2026-03-23
```

3. Fetch the booking player:

```http
GET https://api.hirsalagolf.fi/api/1.0/golf/player/?memberno=4322&clubid=111&firstname=Olli&familyname=Varis
```

4. Create the booking:

```http
POST https://api.hirsalagolf.fi/api/1.0/reservations/order/2
```

## Hirsala payload quirks

At Hirsala, a minimal booking payload may return HTTP 500. Use the richer payload shape below.

Important details observed in a working request:

- `productId` as a string such as `"7"`
- top-level product `quantity: 1`
- `reservation.reservationId`
- `reservation.title`
- `reservation.duration`
- `reservation.fullDuration`
- `reservation.price` as a compact string such as `"39"`
- `reservation.quantity: 1`
- `reservation.recurringReservation: false`
- `reservation.resources[0].quantity: 1`
- `golfPlayers` as an array
- player object includes `age`
- `checkedComments: []`

## Working example body

```json
{
  "products": [
    {
      "productId": "7",
      "productVariantId": 0,
      "quantity": 1,
      "reservation": {
        "reservationId": 1,
        "title": "Lähtötii 1",
        "duration": 10,
        "fullDuration": 10,
        "price": "39",
        "start": "2026-03-23 18:50:00",
        "end": "2026-03-23 19:00:00",
        "quantity": 1,
        "resources": [
          {
            "reservationId": 1,
            "resourceId": 1,
            "quantity": 1,
            "productId": 7,
            "resourceCategory": "golf18",
            "clubId": 111
          }
        ],
        "recurringReservation": false
      },
      "golfPlayers": [
        {
          "personId": 745,
          "firstName": "Olli",
          "familyName": "Varis",
          "playerId": "10363444",
          "handicapActive": 7.9,
          "memberNO": "4322",
          "clubId": "111",
          "teeTimeSignature": "...",
          "age": 26
        }
      ],
      "golfPersonIds": [745],
      "golfPlayersTotal": 1,
      "golfPlayersHandicapTotal": 7.9,
      "checkedComments": []
    }
  ]
}
```

## Cancellation and verification

List current bookings:

```http
GET https://ajax.hirsalagolf.fi/?reservations=getusergolfreservations&appauth=APPAUTH
Authorization: token <access_token>
```

Cancel one reservation row:

```http
GET https://ajax.hirsalagolf.fi/?reservations=deactivatereservationtime&reservationtimeid=RESERVATION_TIME_ID&appauth=APPAUTH
Authorization: token <access_token>
```

## Recommendation for the generic scripts

For Hirsala-like clubs:

- start from `calendarsettings.resource[0]`
- force `resource.quantity = 1` for a single-player booking row
- add player `age` when available or derivable
- prefer the richer request body over a minimal reconstruction
