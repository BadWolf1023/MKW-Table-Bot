'''
Created on Oct 29, 2021

@author: willg
'''
PLAYER_TABLE_NAMES = ["fc", "pid", "player_url"]
RACE_TABLE_NAMES = ["race_id", "rxx", "time_added", "match_time", "race_number", "room_name", "track_name", "room_type", "cc", "region", "is_wiimmfi_race"]
TRACK_TABLE_NAMES = ["track_name", "url", "fixed_track_name", "is_ct", "track_name_lookup"]
PLACE_TABLE_NAMES = ["race_id", "fc", "name", "place", "time", "lag_start", "ol_status", "room_position", "region", "connection_fails", "role", "vr", "character", "vehicle", "discord_name", "lounge_name", "mii_hex", "is_wiimmfi_place"]
EVENT_RACES_TABLE_NAMES = ["event_id", "race_id"]
EVENT_FCS_TABLE_NAMES = ["event_id", "fc", "mii_hex"]
TIER_TABLE_NAMES = ["channel_id", "tier"]
EVENT_ID_TABLE_NAMES = ["event_id"]
EVENT_TABLE_NAMES = ["event_id", "channel_id", "time_added", "last_updated", "number_of_updates", "region", "set_up_user_discord_id", "set_up_user_display_name"]
EVENT_STRUCTURE_TABLE_NAMES = ["channel_id", "name_changes", "removed_races", "placement_history", "forced_room_size", "player_penalties", "team_penalties", "disconnections_on_results", "sub_ins", "teams", "rxx_list", "edits", "ignore_large_times", "missing_player_points", "event_name", "number_of_gps", "player_setup_amount", "number_of_teams", "players_per_team"]

def get_existing_race_fcs_in_Place_table(race_id_fcs):
    return f"""SELECT {PLACE_TABLE_NAMES[0]}, {PLACE_TABLE_NAMES[1]}
FROM Place
WHERE {build_multiple_coniditional_operators([PLACE_TABLE_NAMES[0], PLACE_TABLE_NAMES[1]], ['=','='], race_id_fcs)};"""

def get_existing_race_fcs_in_Place_table_with_null_mii_hex(race_id_fcs):
    return f"""SELECT {PLACE_TABLE_NAMES[0]}, {PLACE_TABLE_NAMES[1]}
FROM Place
WHERE {build_multiple_coniditional_operators([PLACE_TABLE_NAMES[0], PLACE_TABLE_NAMES[1], PLACE_TABLE_NAMES[16]], ['=','=', 'IS'], race_id_fcs)};"""

def get_existing_event_fcs_in_with_null_mii_hex(event_id_fcs):
    return f"""SELECT {EVENT_FCS_TABLE_NAMES[0]}, {EVENT_FCS_TABLE_NAMES[1]}
FROM Event_FCs
WHERE {build_multiple_coniditional_operators([EVENT_FCS_TABLE_NAMES[0], EVENT_FCS_TABLE_NAMES[1], EVENT_FCS_TABLE_NAMES[2]], ['=','=', 'IS'], event_id_fcs)};"""

def get_fcs_in_Player_table(fcs):
    return f"""SELECT {PLAYER_TABLE_NAMES[0]}
FROM Player
WHERE {PLAYER_TABLE_NAMES[0]} in {build_sql_args_list(fcs)};"""

def get_existing_tracks_in_Track_table(track_names):
    return f"""SELECT {TRACK_TABLE_NAMES[0]}
FROM Track
WHERE {TRACK_TABLE_NAMES[0]} in {build_sql_args_list(track_names)};"""

def get_existing_race_ids_in_Race_table(race_ids):
        return f"""SELECT {RACE_TABLE_NAMES[0]}
FROM Race
WHERE {RACE_TABLE_NAMES[0]} in {build_sql_args_list(race_ids)};"""


def build_multiple_coniditional_operators(column_names, operators, iterable):
    result = []
    for item in iterable:
        temp_result = []
        for column_name, operator, _ in zip(column_names, operators, item):
            temp_result.append(f"{column_name} {operator} ?")
        result.append(" AND ".join(temp_result))
    return '(' + ")\nOR (".join(result) + ')'


def build_sql_args_list_comma_separated(iterable):
    result_list = []
    for iterable_lower in iterable:
        result_list.append(f"({', '.join('?'*len(iterable_lower))})")
    return f"{', '.join(result_list)}"


def build_sql_args_list(iterable):
    return f"({', '.join('?'*len(iterable))})"

def build_data_names(data_names):
    return f"({', '.join(data_names)})"


def update_mii_hex_script_event_fcs():
    return f"""UPDATE Event_FCs
SET {EVENT_FCS_TABLE_NAMES[2]} = ?
WHERE {EVENT_FCS_TABLE_NAMES[0]} = ? AND {EVENT_FCS_TABLE_NAMES[1]} = ? AND {EVENT_FCS_TABLE_NAMES[2]} IS NULL"""

def update_mii_hex_script():
    return f"""UPDATE Place
SET {PLACE_TABLE_NAMES[16]} = ?
WHERE {PLACE_TABLE_NAMES[0]} = ? AND {PLACE_TABLE_NAMES[1]} = ? AND {PLACE_TABLE_NAMES[16]} IS NULL"""

'''
def get_insert_into_race_table_script():
    return f"""INSERT INTO Race {build_data_names(RACE_TABLE_NAMES)}
VALUES{build_sql_args_list(RACE_TABLE_NAMES)}"""

def get_insert_into_player_table_script():
    return f"""INSERT INTO Player {build_data_names(PLAYER_TABLE_NAMES)}
VALUES{build_sql_args_list(PLAYER_TABLE_NAMES)}"""

def get_insert_into_track_table_script():
    return f"""INSERT INTO Track {build_data_names(TRACK_TABLE_NAMES)}
VALUES{build_sql_args_list(TRACK_TABLE_NAMES)}"""

def get_insert_into_place_table_script():
    return f"""INSERT INTO Place {build_data_names(PLACE_TABLE_NAMES)}
VALUES{build_sql_args_list(PLACE_TABLE_NAMES)}"""
'''

def build_insert_missing_races_script(races):
        return f"""INSERT OR IGNORE INTO Race {build_data_names(RACE_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(races)}
RETURNING {RACE_TABLE_NAMES[0]}"""

def build_insert_missing_placement_script(placements):
    return f"""INSERT OR IGNORE INTO Place {build_data_names(PLACE_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(placements)}
RETURNING {PLACE_TABLE_NAMES[0]}, {PLACE_TABLE_NAMES[1]}"""

def build_insert_missing_players_script(players):
    return f"""INSERT OR IGNORE INTO Player {build_data_names(PLAYER_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(players)}
RETURNING {PLAYER_TABLE_NAMES[0]}"""

def build_insert_missing_tracks_script(track_infos):
    return f"""INSERT OR IGNORE INTO Track {build_data_names(TRACK_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(track_infos)}
RETURNING {TRACK_TABLE_NAMES[0]}"""
    
def surround_script_begin_commit(script):
    return f"""BEGIN;
{script.rstrip(';')};
COMMIT;"""

def build_missing_event_ids_race_ids_script(event_id_race_ids):
    return f"""INSERT OR IGNORE INTO Event_Races {build_data_names(EVENT_RACES_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(event_id_race_ids)}
RETURNING *"""

def build_missing_event_id_table_script(event_ids):
    return f"""INSERT OR IGNORE INTO Event_ID {build_data_names(EVENT_ID_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(event_ids)}
RETURNING *"""

def build_missing_event_fcs_table_script(event_fcs):
    return f"""INSERT OR IGNORE INTO Event_FCs {build_data_names(EVENT_FCS_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(event_fcs)}
RETURNING *"""

def build_event_upsert_script(was_real_update):
    on_real_update_sql = f" {EVENT_TABLE_NAMES[3]}=(SELECT strftime('%Y-%m-%d %H:%M:%f000+00:00', 'now')), {EVENT_TABLE_NAMES[4]}={EVENT_TABLE_NAMES[4]} + 1," if was_real_update else ""
    on_real_update_sql_2 = f"RETURNING {EVENT_TABLE_NAMES[0]}"
    return f"""INSERT INTO Event {build_data_names(EVENT_TABLE_NAMES)}
VALUES {build_sql_args_list(EVENT_TABLE_NAMES)}
ON CONFLICT ({EVENT_TABLE_NAMES[0]}) DO
UPDATE SET {EVENT_TABLE_NAMES[1]}=excluded.{EVENT_TABLE_NAMES[1]},{on_real_update_sql} {EVENT_TABLE_NAMES[5]}=excluded.{EVENT_TABLE_NAMES[5]}, {EVENT_TABLE_NAMES[6]}=excluded.{EVENT_TABLE_NAMES[6]}, {EVENT_TABLE_NAMES[7]}=excluded.{EVENT_TABLE_NAMES[7]}
{on_real_update_sql_2}"""

    




#print(get_fcs_not_in_Player_table([1, 2, 3]))