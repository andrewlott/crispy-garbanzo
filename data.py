#!/usr/bin/env python3

from api import PiholeAPI
from datetime import datetime, timedelta
import subprocess

api = PiholeAPI()

def get_stats_summary():
    json = api.get_stats_summary()
    queries = json["queries"]
    gravity = json["gravity"]

    return dict(
        total_queries=str(queries["total"]),
        queries_blocked=str(queries["blocked"]),
        percent_blocked=str(queries["percent_blocked"]),
        domains_on_list=str(gravity['domains_being_blocked']),
    )

def get_daily_stats_summary():
    stats_json = api.get_stats_summary()
    gravity = stats_json["gravity"]

    now = datetime.now()
    lookback = timedelta(days=1)
    database_json = api.get_stats_database_summary(
        start_time=int((now - lookback).timestamp()),
        end_time=int(now.timestamp()),
    )

    return dict(
        total_queries=str(database_json["sum_queries"]),
        queries_blocked=str(database_json["sum_blocked"]),
        percent_blocked=str(database_json["percent_blocked"]),
        domains_on_list=str(gravity['domains_being_blocked']),
        gravity_update=format_last_update_time(now - datetime.fromtimestamp(gravity['last_update'])),
    )

def get_status():
    stats_json = api.get_stats_summary()
    queries = stats_json["queries"]

    info_system_json = api.get_info_system()
    ram = info_system_json["system"]["memory"]["ram"]

    ram_string = f"{ram['%used']:.1f}%"
    load = info_system_json["system"]["cpu"]["load"]
    load_string = " / ".join(
        [f"{value:.1f}" for value in load["raw"]]
    )

    dns_blocking_json = api.get_dns_blocking()
    blocking = dns_blocking_json["blocking"]
    timer = dns_blocking_json["timer"]
    timer_string = f" ({timer:.0f}s)" if timer is not None else ""
    active_string = f"{blocking.title()}{timer_string}"

    info_sensors_json = api.get_info_sensors()
    cpu_temp = info_sensors_json["sensors"]["cpu_temp"] or 0.0
    hot_limit = info_sensors_json["sensors"]["hot_limit"]
    temp_unit = info_sensors_json["sensors"]["unit"]
    temperature_string = f"{cpu_temp:.2f} / {hot_limit} °{temp_unit}"
    return {
        "active": active_string,
        "queries_/_s": str(queries["frequency"]),
        "load": load_string,
        "memory": ram_string,
        "temperature": temperature_string,
    }

def update_gravity():
    api.post_action_gravity()

def disable_blocking_for_duration(duration=None):
    api.post_dns_blocking(
        blocking=False,
        duration=duration.seconds if duration is not None else None,
    )

def enable_blocking():
    api.post_dns_blocking(blocking=True)

def update_version():
    subprocess.run(["sudo", "pihole", "-up"])

def format_last_update_time(td):
    total_seconds = td.seconds
    minutes = (total_seconds % 3600) // 60
    hours = total_seconds // 3600
    return f"{td.days}d {hours:02d}h {minutes:02d}m"
