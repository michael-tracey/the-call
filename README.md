# the-call
Heed the call from Warhorn (https://warhorn.net): Pull event data from Warhorn's GraphQL api and create PDF badges for attendees, including their schedule

## hydrate-loal-db.py

Empties the local db.sqlite3 database and imports new entries from your Warhorn event.  

Place the following values in your .env file:

WARHORN_CLIENT_ID=
WARHORN_APPLICATION_TOKEN=
WARHORN_EVENT_SLUG=
WARHORN_EMAIL=
WARHORN_PASSWORD=

## create-badges

This must be in your local .env file, and you must have previously run hydrate-local-db.py successfully.

LOCAL_TIMEZONE=America/New_York
