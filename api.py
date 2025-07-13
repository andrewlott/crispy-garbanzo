#!/usr/bin/env python3

import requests
import subprocess
from functools import wraps

API_BASE_URL = "http://127.0.0.1/api"

class PiholeAPI():

    def __init__(self):
        self.sid = None
        self.should_print = False

    def _print(self, s):
        if self.should_print:
            print(s)

    def reauthenticate_on_401():
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                json = func(self, *args, **kwargs)
                if "error" in json and json["error"]["key"] == "unauthorized":
                    self.authenticate()
                    json = func(self, *args, **kwargs)

                return json
            return wrapper
        return decorator

    def authenticate(self):
        url = f"{API_BASE_URL}/auth"
        self._print(f"POST {url}")

        pw, _ = subprocess.Popen(
            ["sudo", "cat", "/etc/pihole/cli_pw"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()

        json = dict(password=str(pw, encoding='utf-8'))
        response = requests.post(
            url, json=json
        )
        self.sid = response.json()["session"]["sid"]
        return response.json()

    @reauthenticate_on_401()
    def get_list(self):
        url = f"{API_BASE_URL}/lists"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = requests.get(
            url, headers=headers
        )
        return response.json()

    @reauthenticate_on_401()
    def get_stats_summary(self):
        url = f"{API_BASE_URL}/stats/summary"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = requests.get(
            url, headers=headers
        )
        return response.json()
