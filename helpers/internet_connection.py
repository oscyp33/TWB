import requests


def internet_online():
    try:
        requests.get("https://github.com/stefan2200/TWB", timeout=(10, 60))
        return True
    except requests.Timeout:
        return False