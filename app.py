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
import logging


# Log to file with timestamp, and console
logging.basicConfig(
    filename="debug.log",
    encoding='utf-8',
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
    )
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

load_dotenv()
WARHORN_CLIENT_ID = os.getenv('WARHORN_CLIENT_ID')
WARHORN_APPLICATION_TOKEN = os.getenv('WARHORN_APPLICATION_TOKEN')
WARHORN_EVENT_SLUG = os.getenv('WARHORN_EVENT_SLUG')
WARHORN_EMAIL = os.getenv('WARHORN_EMAIL')
WARHORN_PASSWORD = os.getenv('WARHORN_PASSWORD')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')


def makeRegQuery(after_cursor=None):
   query = """
    query ($slug: String!) {
      event(slug: $slug) {
        title
        url
        registrations (first:50, after:AFTER) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            registrant {
              id
              activationState
              email
              name
            }
          }
        }
      }
    }
    """.replace("AFTER", '"{}"'.format(after_cursor) if after_cursor else "null")
   return query

def makeSessionQuery(after_cursor=None):
  query = """
  query EventCalendar ($slug: String!, $start: ISO8601DateTime, $end: ISO8601DateTime) {
    eventSessions(
      events: [ $slug]
      startsAfter: $start
      startsBefore: $end
      first: 50
      after: AFTER
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
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
  """.replace("AFTER", '"{}"'.format(after_cursor) if after_cursor else "null")
  return query

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

if __name__ == '__main__':
  try: 
      BEARER_TOKEN
  except NameError:
      BEARER_TOKEN = get_access_token(WARHORN_EMAIL, WARHORN_PASSWORD, WARHORN_CLIENT_ID, WARHORN_APPLICATION_TOKEN)
      logger.debug("New BEARER:"+ BEARER_TOKEN)
      logger.debug("Save this into your .env file on a new line starting with BEARER_TOKEN= to skip auth in the future")

  ##  PREPARE DB
  file = "db.sqlite3"
  try:
    conn = sqlite3.connect(file)
    logger.info("Database Sqlite3.db formed.")
    createTables(conn)
  except:
    logger.error("Database Sqlite3.db not formed.")
    exit()

  ## PREPARE graphql Client
  headers = { "Authorization": "Bearer "+ BEARER_TOKEN}
  client = GraphqlClient(endpoint="https://warhorn.net/graphql", headers=headers)

  ## FIRST QUERY

  epoch_year = date.today().year
  year_start = date(epoch_year, 1, 1).isoformat()
  year_end = date(epoch_year, 12, 31).isoformat()
  variables = {"slug": WARHORN_EVENT_SLUG, "start": year_start, "end": year_end}
  has_next_page = True
  after_cursor = None
  count = 1
  while has_next_page:
    logging.info("Fetching Session graphql page: "+ str(count) +" cursor: "+ str(after_cursor))
    count = count + 1
    data = client.execute(query=makeSessionQuery(after_cursor), variables=variables)
    has_next_page = data['data']['eventSessions']['pageInfo']['hasNextPage']
    after_cursor = data['data']['eventSessions']['pageInfo']['endCursor']
    ### LOOP ND INSERT
    current_slots = data["data"]["eventSessions"]["nodes"]
    for session in current_slots:
      c = conn.cursor()
      logging.info("INSERTING "+ session['scenario']['name'] +" into 'sessions' table")
      try:
        c.execute("INSERT INTO session (id, startsAt, endsAt, name) VALUES (?,?,?,?)", (session['id'], session['startsAt'], session['endsAt'],session['scenario']['name'] ))
        conn.commit()
      except Exception as e:
        logging.error(e)
      for player in session['playerSignups']:
        logging.info("INSERTING "+ player['user']['name'] +" as player in "+ session['scenario']['name'])
        c.execute("INSERT INTO reg_to_session (session_id, reg_id, gm) VALUES (?, ?, ?)", (session['id'], player['user']['id'], 0, ))
      for gm in session['gmSignups']:
        logging.info("INSERTING "+ gm['user']['name'] +" as gm in "+ session['scenario']['name'])
        c.execute("INSERT INTO reg_to_session (session_id, reg_id, gm) VALUES (?, ?, ?)", (session['id'], gm['user']['id'], 1))

  variables = {"slug": WARHORN_EVENT_SLUG}
  has_next_page = True
  after_cursor = None
  count = 1
  while has_next_page:
    logging.info("Fetching Registration graphql page: "+ str(count) +" cursor: "+ str(after_cursor))
    count = count + 1
    data = client.execute(query=makeRegQuery(after_cursor), variables=variables)
    has_next_page = data['data']['event']['registrations']['pageInfo']['hasNextPage']
    after_cursor = data['data']['event']['registrations']['pageInfo']['endCursor']
    current_registrations = data["data"]["event"]["registrations"]['nodes']
    for reg in current_registrations:
      logging.info("INSERTING "+ reg['registrant']['name'] +" into 'registration' table")
      try:
        c.execute("INSERT INTO registration (id, name, email) VALUES (?,?,?)", (reg['registrant']['id'], reg['registrant']['name'], reg['registrant']['email'] ))
        conn.commit()
      except Exception as e:
        logging.error(e)
