---
name: wisegolf
description: Work with WiseGolf tee times, player lookup, bookings, and reservation management. Use when checking available tee times, estimating how busy a tee time looks, searching player details needed for booking, creating or canceling bookings, inspecting a user's own golf reservations, or mapping a club's WiseGolf API and AJAX endpoints.
---

# WiseGolf

Use this skill for clubs that expose WiseGolf-style golf booking APIs.

Keep club-specific domains, credentials, app IDs, product IDs, entitlement mappings, and regular player lists outside the skill in local configuration.

On first real use for a club:

1. Look for local config and secrets.
2. If required values are missing, ask the user for them explicitly.
3. Store durable non-secret settings in local config.
4. Store secrets separately from the skill and from version-controlled public content.

Typical values needed:

- API domain
- AJAX domain
- club ID
- login username
- login password
- app ID
- API/app version
- `appauth`
- preferred default booking product
- important entitlement/category mappings

## Product discovery and defaults

Do not hardcode tee-time `productId` values when the club exposes product discovery.

Fetch reservation-capable products with:

```bash
curl -s 'https://api.CLUB_DOMAIN/api/1.0/products/?type=6'
```

Use this to discover the club's current booking products before tee-time queries or booking flows.

Practical guidance:

- fetch products when product IDs are not already known with confidence
- cache stable mappings in local config if useful, but prefer re-fetching over guessing
- filter the returned list to the golf booking products relevant to the task
- do not assume every `type=6` product is a golf tee-time product; some clubs may expose other reservation products such as padel

For Hirsala-like naming, typical golf booking products may include names such as:

- `Ajanvaraus 18r`
- `Ajanvaraus 9r`
- `Aamulähdöt 9r`

Default interpretation for ambiguous booking requests:

- if the user says only "book a tee time" / "varaa aika" and does not specify 9 holes vs 18 holes, default to the club's normal 18-hole booking product when one clearly exists
- if there is no clear normal default, ask a clarifying question before booking
- if the requested time appears to belong only to a specific product, treat that as a hint, but avoid silent assumptions for destructive or state-changing booking actions

## Tee time search

Fetch a day's departures with:

```bash
curl -s 'https://api.CLUB_DOMAIN/api/1.0/reservations/?productid=PRODUCT_ID&date=YYYY-MM-DD&golf=1'
```

Inputs needed:

- API domain
- `productid`
- date

Before calling this endpoint, choose the correct booking product:

- if the user explicitly says 18r / 18 holes, use the 18-hole booking product
- if the user explicitly says 9r / 9 holes, use the 9-hole booking product
- if the user gives no type and the club has a clear default, use that default
- otherwise ask a clarifying question

Use this to inspect how full the day is, how many players are in a specific departure, and what groups are ahead of the user's tee time.

## Reading the tee-time response

Key arrays:

- `rows`: reserved tee-time slots for the day, including `start`, `end`, `status`, and `reservationTimeId`
- `reservationsGolfPlayers`: individual players linked to `reservationTimeId`, often with handicap and club info

To inspect a specific departure time:

1. Find `rows` entries whose `start` matches the tee time.
2. Count matching `reservationTimeId` values.
3. Match those IDs against `reservationsGolfPlayers` to estimate how many players are in that departure.

## Interpreting traffic ahead

When the user asks whether there are many players ahead of a departure:

1. Check several preceding start times, not just the target slot.
2. Count group sizes in the departures before the user's tee time.
3. Use handicap (`handicapActive`) only as a rough pace hint:
   - lower handicap often means faster play
   - higher handicap often means slower play
   - treat this only as directional, not certain

A useful answer should mention:

- how many groups are immediately ahead
- whether nearby departures look sparse, normal, or crowded
- whether the handicap profile suggests likely normal or slower pace

## Player lookup for booking

Use the player search API when a booking requires player details.

Pattern:

```bash
curl -s 'https://api.CLUB_DOMAIN/api/1.0/golf/player/?memberno=&clubid=CLUB_ID&firstname=FIRST&familyname=LAST'
```

Typical usage:

- search by `firstname` + `familyname`
- leave `memberno` empty when unknown
- use returned player details for booking requests
- use `clubid` when the relevant club is known

## Access rights interpretation

If player data includes an `accessRights` item like:

```json
{"categoryId":46,"personId":744,"name":"Some entitlement name","usableQuantity":null}
```

interpret it as:

- the player has the right to use the product/access type named in `name`
- `categoryId` is the identifier to use when a booking must consume that entitlement

Use `accessRights` to judge whether a player can be booked under a specific entitlement/product.

Keep club- or user-specific entitlement mappings outside this skill.

## Authentication flow

Login uses:

```http
POST https://api.CLUB_DOMAIN/api/1.0/auth
```

Body shape:

```json
{"username":"...","password":"...","appId":"...","version":"..."}
```

Observed notes:

- `username` can be a member number at some clubs
- login returns the auth token in `access_token`
- use it as:
  - `Authorization: token <access_token>`

This auth token is required for at least:

- booking creation
- fetching the user's golf reservations
- removing reservation rows
- logout

Logout uses:

```http
POST https://api.CLUB_DOMAIN/api/1.0/logout
```

and requires the auth token.

Some AJAX reservation endpoints also require a separate `appauth` query parameter.

## Booking request shape

Create a booking with:

```http
POST https://api.CLUB_DOMAIN/api/1.0/reservations/order/2
```

The request body contains a `products` array. In observed flows, there can be one product entry per booked player for the same tee time.

Important fields commonly seen in working requests:

- `productId`: booking product
- `productVariantId`: often `0`
- `reservation.start` / `reservation.end`: tee time window
- `reservation.price`: effective price for that slot
- `reservation.resources`: resource metadata for the tee time/product
- `golfPlayers`: player object for the specific player attached to that product row
- `golfPersonIds`: all golfers included in the booking
- `golfPlayersTotal`: total number of golfers in the booking
- `golfPlayersHandicapTotal`: summed handicap value used by the API/client flow
- `addCategoryId`: include when a specific access right/product is used for that player

Practical interpretation:

- first identify the correct booking product for the user's request
- then identify the tee time and reservation resource details for that product
- then identify each player and their eligible `accessRights`
- when a player uses a named right/product, include the matching category as `addCategoryId`
- include all booked golfers in `golfPersonIds`, even if each product row only carries one `golfPlayers` object

For ambiguous booking requests, do not silently pick an unusual product. Use the default 18-hole product only when that default is explicitly established for the club or local config.

When a club returns HTTP 500 for a minimal booking payload, do not keep guessing field-by-field. Use the richer payload shape and supporting script in this skill:

- `scripts/book_tee_time.py` for a reusable booking flow
- `references/hirsala.md` for an example of a club that requires a fuller request body

Fields that are especially worth preserving from working web-app traffic at stricter clubs:

- product-level `quantity`
- `reservation.reservationId`
- `reservation.title`
- `reservation.duration` and `reservation.fullDuration`
- `reservation.quantity`
- `reservation.recurringReservation`
- resource-level `quantity`
- `golfPlayers` as an array
- player `age` when available or derivable
- `checkedComments` as an empty array when nothing is selected

## User reservations

Fetch the user's golf reservations with:

```http
https://ajax.CLUB_DOMAIN/?reservations=getusergolfreservations&appauth=APPAUTH
```

This endpoint requires authentication:

- `Authorization: token ...`

Practical use:

- list the user's current golf bookings
- identify tee times, grouped bookings, and `reservationTimeId` values before changes
- rows sharing the same `orderId` and time usually belong to the same booking/group

## Removing a booked reservation time

Remove a booked reservation row with:

```http
GET https://ajax.CLUB_DOMAIN/?reservations=deactivatereservationtime&reservationtimeid=RESERVATION_TIME_ID&appauth=APPAUTH
```

This endpoint requires authentication:

- `Authorization: token ...`

Interpretation:

- `reservationtimeid` identifies the booked slot/player row to deactivate
- this is used to remove a player from an existing tee time booking
- `appauth` is required request context for this AJAX endpoint

Be careful: removing by `reservationtimeid` is destructive. Double-check the target player and tee time before using it.

Use `scripts/cancel_tee_time.py` when you want a reusable cancellation flow instead of reconstructing the AJAX call by hand.

## Privacy note

The API may return hidden/public-name flags. Do not try to expose private player identities unless clearly appropriate and already visible.
