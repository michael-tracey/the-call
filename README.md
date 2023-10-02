# the-call
Heed the call from Warhorn (https://warhorn.net): Pull event data from Warhorn's GraphQL api and create PDF badges for attendees, including their schedule

The process is two steps:

* Run `hydrate-local-db.py` to get the data from Warhorn into the local sqlite3 database.  Rerun this to flush the DB and pull a fresh copy.
* Run `create-badges.py` to create the PDF file for printing badges.

## hydrate-local-db.py

Empties the local db.sqlite3 database and imports new entries from your Warhorn event.  

Place the following values in your .env file:

Env Variable | Value
---|---
WARHORN_CLIENT_ID | Client ID from the *Warhorn for Developers* page for your app. 
WARHORN_APPLICATION_TOKEN | Application Token from the *Warhorn for Developers* page for your app
WARHORN_EVENT_SLUG | The slug for your event, viewable in "Settings" -> Title page, under Event Slug (or in your event's URL)
WARHORN_EMAIL | Your private user (owner of the event) email
WARHORN_PASSWORD | Your private user (owner of the event) password

The process will connect your app (the copy of this code) to your warhorn account and let it access your event data instead of having just public warhorn data.  You will get a BEARER_TOKEN for oauth2 from these steps to put in your .env file from these steps.  The next time you run `hydrate-local-db.py` it will use the BEARER_TOKEN to query warhorn via graphql and store the needed event data in a local Sqlite3 database file (`db.sqlite3` in your application directory).  You are now ready to create your badges.

## create-badges.py

### Requriements

This must be in your local .env file, and you must have previously run hydrate-local-db.py successfully.

Env Variable | Value
---|---
LOCAL_TIMEZONE | Your local timezone, as warhorn uses Pacific time (-7UTC), dates will be converted to this timezone on your badges.  Example: `America/New_York` 
WARHORN_EVENT_SLUG | The slug for your event, viewable in "Settings" -> Title page, under Event Slug (or in your event's URL)

You must also have [wkhtmltopdf|https://wkhtmltopdf.org/downloads.html] installed.

### Operation

This will read from your local sqlite3 database created with `hydrate-local-db.py` and using the jinga2 templates in the `/templates` folder, create badge backs for 4x3 horizontal badge holders, individually customized for each attendee.  The program could easily be adjusted for other sized documents.

The 4.3 badges are sized to print 6 pages to a single 8.5x11 sheet, then cut and placed in the convention badge, so the attendees know their schedule

### Note about table number

This program is using the Virtual Tabletop name field to hold "Table Number" for the default 2nd column of the sheets. I choose the type of VTT as `Other`, put the Table number in the "name field" ( `Table 3` for example), and put "This game is held physically at ______ convention, tickets can be purchased ________" in the description as to not confuse any people browsing on warhorn.

#### Example Output

4x3 prepared for horizontal badge holder:

![2023-10-02_16-35](https://github.com/michael-tracey/the-call/assets/53870997/59c09f53-1a0e-48cb-bee2-db5c1b976af6)


