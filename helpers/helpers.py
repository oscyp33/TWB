import logging
import time
import datetime
import requests


def internet_online():
    try:
        requests.get("https://github.com/stefan2200/TWB", timeout=(10, 60))
        return True
    except requests.Timeout:
        return False


def print_sleep_info( sleep_time):
    dtn = datetime.datetime.now()
    dt_next = dtn + datetime.timedelta(0, sleep_time)
    logging.info(
        f"Dead for {sleep_time / 60:.2f} minutes (next run at: {dt_next.time()})"
    )