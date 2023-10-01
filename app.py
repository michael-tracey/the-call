import os
from python_graphql_client import GraphqlClient
from dotenv import load_dotenv
import requests
from oauthlib.oauth2 import BackendApplicationClient
import requests
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
import webbrowser
import json
from datetime import date
import sqlite3

load_dotenv()
WARHORN_CLIENT_ID = os.getenv('WARHORN_CLIENT_ID')
WARHORN_APPLICATION_TOKEN = os.getenv('WARHORN_APPLICATION_TOKEN')
WARHORN_EVENT_SLUG = os.getenv('WARHORN_EVENT_SLUG')
WARHORN_EMAIL = os.getenv('WARHORN_EMAIL')
WARHORN_PASSWORD = os.getenv('WARHORN_PASSWORD')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')



def createTables(conn):
   try:
      c=conn.cursor()
      c.execute("DROP TABLE IF EXISTS session")
      c.execute("""CREATE TABLE IF NOT EXISTS session (
                id TEXT, 
                startsAt TEXT, 
                endsAt TEXT, 
                name TEXT,
                PRIMARY KEY (id)
                )""")
      
      c.execute("DROP TABLE IF EXISTS reg_to_session")
      c.execute("""CREATE TABLE IF NOT EXISTS reg_to_session (
                session_id TEXT, 
                reg_id TEXT, 
                gm BOOLEAN NOT NULL CHECK (gm IN (0, 1)))""")
      c.execute("DROP TABLE IF EXISTS registration")
      c.execute("""CREATE TABLE IF NOT EXISTS registration (
                id TEXT, 
                name TEXT, 
                email TEXT)""")
      conn.commit()
   except Exception as e:
      print(e)
      exit


def get_access_token(client_id, client_secret, app_client_id, app_client_secret):
    authorization_base_url = 'https://warhorn.net/oauth/authorize'
    token_url = 'https://warhorn.net/oauth/token'
    redirect_uri = 'https://avlscarefest.com/custom-api/oauth'
    scope = [ 'openid', 'email', 'profile']
    warhorn = OAuth2Session(app_client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = warhorn.authorization_url(authorization_base_url)
    print('Please go here and authorize: ', authorization_url)
    webbrowser.open(authorization_url)
    redirect_response = input('\n\nPaste the code from the URL here:')

    response = requests.post(
        token_url,
        data = {
            'grant_type':'authorization_code',
            'client_id': app_client_id,
            'code': redirect_response,
            'redirect_uri': redirect_uri
        }

    )
    if response.status_code == 200:
        output = response.json()
        return output['access_token']


try: 
    BEARER_TOKEN
except NameError:
    BEARER_TOKEN = get_access_token(WARHORN_EMAIL, WARHORN_PASSWORD, WARHORN_CLIENT_ID, WARHORN_APPLICATION_TOKEN)
    print("New BEARER:"+ BEARER_TOKEN)
    print("Save this into your .env file on a new line starting with BEARER_TOKEN= to skip auth in the future")

##  PREPARE DB
file = "db.sqlite3"
try:
  conn = sqlite3.connect(file)
  print("Database Sqlite3.db formed.")
  createTables(conn)
except:
  print("Database Sqlite3.db not formed.")

## PREPARE graphql Client
headers = { "Authorization": "Bearer "+ BEARER_TOKEN}
client = GraphqlClient(endpoint="https://warhorn.net/graphql", headers=headers)

## FIRST QUERY
query = """
query EventCalendar ($slug: String!, $start: ISO8601DateTime, $end: ISO8601DateTime) {
  eventSessions(
    events: [ $slug]
    startsAfter: $start
    startsBefore: $end
  ) {
    nodes {
      id
      status
      startsAt
      endsAt
      scenario {
        name
        campaign {
          name
        }
      }
      uuid
      playerSignups {
        user {
          name
          id
        
        }
      }
      gmSignups {
        user {
          name
          id
        }
      }
    }
  }
}
"""
epoch_year = date.today().year
year_start = date(epoch_year, 1, 1).isoformat()
year_end = date(epoch_year, 12, 31).isoformat()
variables = {"slug": WARHORN_EVENT_SLUG, "start": year_start, "end": year_end}
data = client.execute(query=query, variables=variables)

### LOOP ND INSERT
current_slots = data["data"]["eventSessions"]["nodes"]
for session in current_slots:
  c = conn.cursor()
  print("INSERTING "+ session['scenario']['name'] +" into 'sessions' table")
  try:
    c.execute("INSERT INTO session (id, startsAt, endsAt, name) VALUES (?,?,?,?)", (session['id'], session['startsAt'], session['endsAt'],session['scenario']['name'] ))
    conn.commit()
  except Exception as e:
     print("FAIL")
     print(e)
  for player in session['playerSignups']:
     print("\tINSERTING "+ player['user']['name'] +" as player")
     c.execute("INSERT INTO reg_to_session (session_id, reg_id, gm) VALUES (?, ?, ?)", (session['id'], player['user']['id'], 0, ))
  for gm in session['gmSignups']:
     print("\tINSERTING "+ gm['user']['name'] +" as gm")
     c.execute("INSERT INTO reg_to_session (session_id, reg_id, gm) VALUES (?, ?, ?)", (session['id'], gm['user']['id'], 1))
  print("INSERTING "+ session['scenario']['name'] +" into 'sessions' table")


query = """
query ($slug: String!) {
  event(slug: $slug) {
    title
    url
    registrations {
      nodes {
        registrant {
          activationState
          email
          name
        }
      }
    }
  }
}
"""
