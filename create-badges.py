import os, time
from dotenv import load_dotenv
import requests
import webbrowser
import datetime
import pytz
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
LOCAL_TIMEZONE = os.getenv('LOCAL_TIMEZONE')


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        logging.error(e)
        exit()
    return conn

def formatTimes(start, end):
    new_tz = pytz.timezone(LOCAL_TIMEZONE)
    startsAt = datetime.datetime.fromisoformat(start)
    startsAt = startsAt.astimezone(new_tz)
    endsAt = datetime.datetime.fromisoformat(end)
    endsAt = endsAt.astimezone(new_tz)
    day = startsAt.strftime("%A")
    shour = startsAt.strftime('%I')
    smin = startsAt.strftime('%M')
    if smin != '00':
        shour = shour + ":" + smin
    ehour = endsAt.strftime("%I")
    emin = endsAt.strftime("%M")
    if emin != '00':
        ehour = ehour + ":" +emin
    sampm = startsAt.strftime("%p")
    eampm = endsAt.strftime('%p')
    ehour = ehour.lstrip("0")
    shour = shour.lstrip("0")
    if sampm == eampm:
        output = day +", "+ shour +" - "+ ehour + eampm
    else:
        output = day +", "+ shour + sampm +" - "+ ehour + eampm
    return output

if __name__ == '__main__':
    ##  PREPARE DB
    file = "db.sqlite3"
    conn = create_connection(file)
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM registration ORDER BY name ASC")
    except sqlite3.Error as e:
        logging.error(e)
        exit()
    registrations = cur.fetchall()
    logging.debug('Total registrations are '+ str(len(registrations)))
    for reg in registrations:
        logging.debug('Finding sessions for '+ reg[1])
        try:
            cur.execute("SELECT session.name, session.startsAt, session.endsAt, reg_to_session.gm FROM reg_to_session,session WHERE reg_to_session.session_id = session.id AND reg_to_session.reg_id = '"+ reg[0] +"' ORDER BY startsAt ASC")
        except sqllite3.Error as e:
            logging.error(e)
            exit()
        sessions = cur.fetchall()
        logging.debug(reg[1] +" has "+ str(len(sessions)))
        count = 0
   
        for session in sessions:
            count = count +1

            formatedDate = formatTimes(session[1], session[2])
            if session[3]:
                logging.debug(str(count) +") "+ reg[1] +" is a GM in "+ str(session[0]) +" at "+ formatedDate)
            else:
                logging.debug(str(count) +") "+ reg[1] +" is a player in "+ str(session[0]) +" at "+ formatedDate)
  