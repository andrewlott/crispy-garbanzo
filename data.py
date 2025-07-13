#!/usr/bin/env python3

from api import PiholeAPI

api = PiholeAPI()

def get_stats_summary():
    json = api.get_stats_summary()
    queries = json["queries"]
    gravity = json["gravity"]
    return dict(
        total_queries=queries["total"],
        queries_blocked=queries["blocked"],
        percent_blocked=queries["percent_blocked"],
        domains_on_list=gravity['domains_being_blocked'],
    )

print(get_stats_summary())
