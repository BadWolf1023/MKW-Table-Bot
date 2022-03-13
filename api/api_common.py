import common

TEAM_SCORES_HTML_ENDPOINT = "/api/html/team_scores/"
FULL_TABLE_HTML_ENDPOINT = "/api/html/full_scores/"
TEAM_SCORES_JSON_ENDPOINT = "/api/json/team_scores/"
INFO_ENDPOINT = "/info/"

def reload_properties():
    global API_URL
    API_URL = common.properties["public_api_url"]
reload_properties()