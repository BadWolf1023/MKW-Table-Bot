import common

TEAM_SCORES_HTML_ENDPOINT = "/api/html/team_scores/"
FULL_TABLE_HTML_ENDPOINT = "/api/html/full_scores/"
TEAM_SCORES_JSON_ENDPOINT = "/api/json/team_scores/"
FULL_SCORES_PICTURE_ENDPOINT = "/api/picture/full_scores/"
TABLE_PICTURE_URL_JSON_ENDPOINT = "/api/json/picture/"
INFO_ENDPOINT = "/info/"
STATS_ENDPOINT = "/api/stats"

TABLE_ID_NOT_FOUND_ERR_MSG = "Table ID not found. Either the table has been reset, or the table ID given does not exist. Table Bot gave you a table ID when you started the table. Use that."

def reload_properties():
    global API_URL
    API_URL = common.properties["public_api_url"]
reload_properties()