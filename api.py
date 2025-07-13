#!/usr/bin/env python3

import requests
import subprocess
from functools import wraps

API_BASE_URL = "http://127.0.0.1/api"

class PiholeAPI():

    def __init__(self):
        self.sid = None
        self.should_print = False
        self.session = requests.Session()

    def _print(self, s):
        if self.should_print:
            print(s)

    def reauthenticate_on_401():
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                json = func(self, *args, **kwargs)
                if (
                    json is False
                    or (
                        json not in [True, False]
                        and "error" in json
                        and json["error"]["key"] == "unauthorized"
                    )
                ):
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
        response = self.session.post(
            url, json=json
        )
        self._print(response.json())
        self.sid = response.json()["session"]["sid"]
        return response.json()

    @reauthenticate_on_401()
    def get_list(self):
        url = f"{API_BASE_URL}/lists"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = self.session.get(
            url, headers=headers
        )
        self._print(response.json())
        return response.json()

    @reauthenticate_on_401()
    def get_stats_summary(self):
        url = f"{API_BASE_URL}/stats/summary"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = self.session.get(
            url, headers=headers
        )
        self._print(response.json())
        return response.json()

    @reauthenticate_on_401()
    def get_stats_database_summary(self, start_time, end_time):
        url = f"{API_BASE_URL}/stats/database/summary"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        params = {
            "from": start_time,
            "until": end_time
        }
        response = self.session.get(
            url, headers=headers, params=params,
        )
        self._print(response.json())
        return response.json()

    @reauthenticate_on_401()
    def get_info_system(self):
        url = f"{API_BASE_URL}/info/system"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = self.session.get(
            url, headers=headers
        )
        self._print(response.json())
        return response.json()

    @reauthenticate_on_401()
    def get_info_sensors(self):
        url = f"{API_BASE_URL}/info/sensors"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = self.session.get(
            url, headers=headers
        )
        self._print(response.json())
        return response.json()

    @reauthenticate_on_401()
    def get_dns_blocking(self):
        url = f"{API_BASE_URL}/dns/blocking"
        self._print(f"GET {url}")

        headers = dict(sid=self.sid)
        response = self.session.get(
            url, headers=headers
        )
        self._print(response.json())
        return response.json()

    @reauthenticate_on_401()
    def post_action_gravity(self):
        url = f"{API_BASE_URL}/action/gravity"
        self._print(f"POST {url}")

        headers = dict(sid=self.sid)
        response = self.session.post(url, headers=headers)
        # No JSON in response
        return response.status_code == 200

    @reauthenticate_on_401()
    def post_dns_blocking(self, blocking=True, duration=None):
        url = f"{API_BASE_URL}/dns/blocking"
        self._print(f"POST {url}")

        body = dict(
            blocking=blocking,
            timer=duration,
        )
        headers = dict(sid=self.sid)
        response = self.session.post(
            url,
            headers=headers,
            json=body
        )
        self._print(response.json())
        return response.json()
