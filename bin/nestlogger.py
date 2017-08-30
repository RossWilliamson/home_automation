#!/usr/bin/env python
import logging
import sqlite3
import time
from datetime import datetime
from scipy.constants import convert_temperature as ct

import nest

logging.basicConfig()
logger = logging.getLogger("HomeLogger")
logger.setLevel(logging.DEBUG)

SBF_DB = "/home/rw247/smadata/SBFspot.db"

CLIENT_ID = '1bd5b3d7-59da-44ef-a22a-a1c13757a701'
CLIENT_SECRET = 'ERXfykyoNm2D4CJWQ0pJc4GDI'
ACCESS_TOKEN = 'nest.json'

napi = nest.Nest(client_id=CLIENT_ID,
                 client_secret=CLIENT_SECRET,
                 access_token_cache_file=ACCESS_TOKEN)
nest_device = napi.structures[0].thermostats[0]

def get_nest_info():
    napi._bust_cache()
    temperature = nest_device.temperature
    if nest_device.temperature_scale == 'F':
        temperature = ct(temperature, "F", "C")

    humidity = nest_device.humidity

    logger.debug("Temp: %0.1fC" % temperature)
    logger.debug("Humidity: %0.1f%%" % humidity)

    return(temperature, humidity)

def write_to_db():
    n_t, n_h = get_nest_info()
    attic_t = 21.0
    attic_fan = False

    tmp_time = datetime.now()
    unix_time = int(tmp_time.strftime('%s'))

    conn = sqlite3.connect(SBF_DB)
    c = conn.cursor()
    sql_str = "INSERT INTO HomeData VALUES (%i,%f,%f,%f,%i)" % (
        unix_time, n_t, n_h, attic_t, attic_fan
    )
    logger.debug(sql_str)
    c.execute(sql_str)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    write_to_db()
