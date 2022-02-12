'''
Created on Oct 29, 2021

@author: willg
'''
PLAYER_TABLE_NAMES = ["fc", "pid", "player_url"]
RACE_TABLE_NAMES = ["race_id", "rxx", "time_added", "match_time", "race_number", "room_name", "track_name", "room_type", "cc", "region", "is_wiimmfi_race", "num_players", "first_place_time", "last_place_time", "avg_time"]
TRACK_TABLE_NAMES = ["track_name", "url", "fixed_track_name", "is_ct", "track_name_lookup"]
PLACE_TABLE_NAMES = ["race_id", "fc", "name", "place", "time", "lag_start", "ol_status", "room_position", "region", "connection_fails", "role", "vr", "character", "vehicle", "discord_name", "lounge_name", "mii_hex", "is_wiimmfi_place"]
EVENT_RACES_TABLE_NAMES = ["event_id", "race_id"]
EVENT_FCS_TABLE_NAMES = ["event_id", "fc", "mii_hex"]
TIER_TABLE_NAMES = ["channel_id", "tier"]
EVENT_ID_TABLE_NAMES = ["event_id"]
EVENT_TABLE_NAMES = ["event_id", "channel_id", "time_added", "last_updated", "number_of_updates", "region", "set_up_user_discord_id", "set_up_user_display_name", "player_setup_amount"]
EVENT_STRUCTURE_TABLE_NAMES = ["event_id", "name_changes", "removed_races", "placement_history", "forced_room_size", "player_penalties", "team_penalties", "disconnections_on_results", "sub_ins", "teams", "rxx_list", "edits", "ignore_large_times", "missing_player_points", "event_name", "number_of_gps", "player_setup_amount", "number_of_teams", "players_per_team"]

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

def build_race_sql_args_list_comma_separated(races):
    result_list = []
    for race in races:
        result_list.append(f"({', '.join('?'*2)}, (SELECT strftime('%Y-%m-%d %H:%M:%f', 'now')), {', '.join('?'*len(RACE_TABLE_NAMES[3:]))})")
    return f"{', '.join(result_list)}"


def build_sql_args_list(iterable):
    return f"({', '.join('?'*len(iterable))})"

def build_data_names(data_names):
    return f"({', '.join(data_names)})"


def update_mii_hex_script_event_fcs():
    return f"""UPDATE Event_FCs
SET {EVENT_FCS_TABLE_NAMES[2]} = ?
WHERE {EVENT_FCS_TABLE_NAMES[0]} = ? AND {EVENT_FCS_TABLE_NAMES[1]} = ? AND {EVENT_FCS_TABLE_NAMES[2]} IS NULL;"""

def update_mii_hex_script():
    return f"""UPDATE Place
SET {PLACE_TABLE_NAMES[16]} = ?
WHERE {PLACE_TABLE_NAMES[0]} = ? AND {PLACE_TABLE_NAMES[1]} = ? AND {PLACE_TABLE_NAMES[16]} IS NULL;"""

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
VALUES{build_race_sql_args_list_comma_separated(races)}
RETURNING {RACE_TABLE_NAMES[0]};"""

def build_insert_missing_placement_script(placements):
    return f"""INSERT OR IGNORE INTO Place {build_data_names(PLACE_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(placements)}
RETURNING {PLACE_TABLE_NAMES[0]}, {PLACE_TABLE_NAMES[1]};"""

def build_insert_missing_players_script(players):
    return f"""INSERT OR IGNORE INTO Player {build_data_names(PLAYER_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(players)}
RETURNING {PLAYER_TABLE_NAMES[0]};"""

def build_insert_missing_tracks_script(track_infos):
    return f"""INSERT OR IGNORE INTO Track {build_data_names(TRACK_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(track_infos)}
RETURNING {TRACK_TABLE_NAMES[0]};"""
    
def surround_script_begin_commit(script):
    return f"""BEGIN;
{script.rstrip(';')};
COMMIT;"""

def build_missing_event_ids_race_ids_script(event_id_race_ids):
    return f"""INSERT OR IGNORE INTO Event_Races {build_data_names(EVENT_RACES_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(event_id_race_ids)}
RETURNING *;"""

def build_missing_event_id_table_script(event_ids):
    return f"""INSERT OR IGNORE INTO Event_ID {build_data_names(EVENT_ID_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(event_ids)}
RETURNING *;"""

def build_missing_event_fcs_table_script(event_fcs):
    return f"""INSERT OR IGNORE INTO Event_FCs {build_data_names(EVENT_FCS_TABLE_NAMES)}
VALUES{build_sql_args_list_comma_separated(event_fcs)}
RETURNING *;"""


def build_event_upsert_script(was_real_update):
    on_real_update_sql = f" {EVENT_TABLE_NAMES[3]}=(SELECT strftime('%Y-%m-%d %H:%M:%f', 'now')), {EVENT_TABLE_NAMES[4]}={EVENT_TABLE_NAMES[4]} + 1," if was_real_update else ""
    on_real_update_sql_2 = f"RETURNING {EVENT_TABLE_NAMES[0]}"
    return f"""INSERT INTO Event {build_data_names(EVENT_TABLE_NAMES)}
VALUES (?, ?, (SELECT strftime('%Y-%m-%d %H:%M:%f', 'now')), (SELECT strftime('%Y-%m-%d %H:%M:%f', 'now')), ?, ?, ?, ?, ?)
ON CONFLICT ({EVENT_TABLE_NAMES[0]}) DO
UPDATE SET {EVENT_TABLE_NAMES[1]}=excluded.{EVENT_TABLE_NAMES[1]},{on_real_update_sql} {EVENT_TABLE_NAMES[5]}=excluded.{EVENT_TABLE_NAMES[5]}, {EVENT_TABLE_NAMES[6]}=excluded.{EVENT_TABLE_NAMES[6]}, {EVENT_TABLE_NAMES[7]}=excluded.{EVENT_TABLE_NAMES[7]}, {EVENT_TABLE_NAMES[8]}=excluded.{EVENT_TABLE_NAMES[8]}
{on_real_update_sql_2};"""


def build_excluded_list(name_list):
    return ",\n".join(f"{n}=excluded.{n}" for n in name_list)

def build_event_structure_script():
    return f"""INSERT INTO Event_Structure {build_data_names(EVENT_STRUCTURE_TABLE_NAMES)}
VALUES {build_sql_args_list(EVENT_STRUCTURE_TABLE_NAMES)}
ON CONFLICT ({EVENT_STRUCTURE_TABLE_NAMES[0]}) DO
UPDATE SET {build_excluded_list(EVENT_STRUCTURE_TABLE_NAMES[1:])}
RETURNING {EVENT_STRUCTURE_TABLE_NAMES[0]}"""

    


class SQL_Search_Query_Builder(object):
    @staticmethod
    def get_sql_tier_filter(tier, is_ct):
        return f"""Race.race_id in (SELECT DISTINCT Race.race_id
                FROM Race
                WHERE Race.rxx in (
                                SELECT DISTINCT Race.rxx
                                FROM Tier JOIN Event USING(channel_id) /*Immediately discard events without a tier*/
                                    JOIN Event_Races USING(event_id) /*All events with a tier allowed, allow duplicate events*/
                                    JOIN Race USING(race_id)
                                    JOIN Track USING(track_name)
                                WHERE
                                Tier.tier = {tier} /*Only get events with the desired tier*/
                                AND Tier.is_ct = {1 if is_ct else 0}
                                AND Track.is_ct = {1 if is_ct else 0}
                                {SQL_Search_Query_Builder.get_event_valid_filter()}
                                )
)"""

    @staticmethod
    def get_sql_days_filter(days):
        return f"Race.time_added > date('now','-{days} days')"

    @staticmethod
    def get_event_valid_filter():
        return """
            AND ROUND((JULIANDAY(Event.last_updated) - JULIANDAY(Event.time_added)) * 86400) > 600 /*10 minutes is 600 seconds*/
            AND Event.number_of_updates > 2 /*Events should have at least 3 room updates, otherwise the table was likely not created during the event*/
            AND Event.region = 'priv'
            """

    @staticmethod
    def get_tracks_played_query(is_ct, tier, last_x_days):
        tier_filter_clause = ""
        days_filter_clause = ""
        if tier is not None:
            tier_filter_clause = "AND " + SQL_Search_Query_Builder.get_sql_tier_filter(tier, is_ct)
        if last_x_days is not None:
            days_filter_clause = "AND " + SQL_Search_Query_Builder.get_sql_days_filter(last_x_days)
            
        return f"""SELECT
        Race.track_name,
        Track.fixed_track_name,
        COUNT(Race.race_id) as times_played
    FROM
        Race LEFT JOIN Track ON Race.track_name = Track.track_name
    WHERE
        Track.is_ct = {1 if is_ct else 0}
        AND Race.region = "priv"
        {tier_filter_clause}
        {days_filter_clause}
    GROUP BY
        Track.fixed_track_name
    ORDER BY
        3 DESC, 1 ASC;"""

    @staticmethod
    def get_best_tracks(fcs, is_ct, tier, last_x_days, min_count):
        tier_filter_clause = f"""
        AND Place.race_id IN (
            SELECT race_id
            FROM Event_Races
                     JOIN Event ON Event_Races.event_id = Event.event_id
                     JOIN Tier ON Event.channel_id = Tier.channel_id
                
                WHERE Event.player_setup_amount = 12
                {f"AND tier = {tier}" if (tier is not None) else ""}
                {SQL_Search_Query_Builder.get_event_valid_filter()}
        )
        """

        days_filter_clause = ""
        if last_x_days is not None:
            days_filter_clause = "AND " + SQL_Search_Query_Builder.get_sql_days_filter(last_x_days)

        #fcs = ['1509-2420-6937']
        fc_filter = '(' + ','.join([f'\'{fc}\'' for fc in fcs]) + ')'

        return f"""
            SELECT Track.fixed_track_name,
                   AVG(pts)         AS avg_pts,
                   AVG(Place.place) AS avg_place,
                   MIN(time) AS avg_delta,
                   COUNT(*)         AS count
            FROM Place
                     JOIN Race ON Place.race_id = Race.race_id
                     JOIN Score_Matrix
                          ON (Place.place = Score_Matrix.place AND num_players = Score_Matrix.size)
                     JOIN Track ON Race.track_name = Track.track_name
            WHERE Track.is_ct = {1 if is_ct else 0}
                AND Race.track_name != ''
                AND Place.fc in {fc_filter}
                AND time < 6 * 60
                {days_filter_clause}
                {tier_filter_clause}
            GROUP BY Track.fixed_track_name
            HAVING COUNT(*) >= {min_count}
            ORDER BY avg_pts DESC
        """

    @staticmethod
    def get_top_players_query(tier, last_x_days, min_count):
        tier_filter_clause = ""
        days_filter_clause = ""
        if tier is not None:
            tier_filter_clause = f"AND tier = {tier}"
        if last_x_days is not None:
            days_filter_clause = "AND " + SQL_Search_Query_Builder.get_sql_days_filter(last_x_days)

        return f"""
        SELECT
               discord_id,
               AVG(pts)         AS avg_pts,
               AVG(Place.place) AS avg_place,
               MIN(time) AS avg_delta,
               COUNT(*) AS count
        FROM Place
                 JOIN Race ON Place.race_id = Race.race_id
                 JOIN Score_Matrix
                      ON (Place.place = Score_Matrix.place AND num_players = Score_Matrix.size)
                 JOIN Player_FCs ON Place.fc = Player_FCs.fc
                 
        WHERE Place.race_id IN (
            SELECT Race.race_id
            FROM Race
                    JOIN Event_Races ER ON Race.race_id = ER.race_id
                    JOIN Event ON ER.event_id = Event.event_id
                    JOIN Tier ON Event.channel_id = Tier.channel_id
                    JOIN Track ON Race.track_name = Track.track_name
        
            WHERE Event.player_setup_amount = 12
                AND Track.fixed_track_name = ?
                {tier_filter_clause}
                {SQL_Search_Query_Builder.get_event_valid_filter()}
        )
            AND time < 6 * 60
            
        {days_filter_clause}
        GROUP BY discord_id
        
        HAVING COUNT(*) >= {min_count}
        ORDER BY avg_pts DESC
        LIMIT 100
        """

    @staticmethod
    def get_player_races(did, days):
        days_filter_clause = f"AND Event.time_added > date('now','-{days} days')" if (days is not None) else ""

        return f"""
        SELECT race_id, place
                 FROM Place
                     JOIN Player_FCs ON Place.fc = Player_FCs.fc
                 WHERE Place.race_id IN (
                     SELECT race_id
                     FROM Event_Races
                              JOIN Event ON Event_Races.event_id = Event.event_id
                              JOIN Tier ON Event.channel_id = Tier.channel_id
                     WHERE player_setup_amount == 12
                       {days_filter_clause}
                       {SQL_Search_Query_Builder.get_event_valid_filter()}
                 )
                   AND discord_id = {did}
                   AND time < 6 * 60
        """

    @staticmethod
    def get_record_query(player_did, opponent_did, days):
        return f"""
        SELECT COUNT(*), SUM(CASE WHEN a.place < b.place THEN 1 ELSE 0 END) as wins
        FROM ({SQL_Search_Query_Builder.get_player_races(player_did, days)}) as a 
        JOIN ({SQL_Search_Query_Builder.get_player_races(opponent_did, days)}) as b 
        ON a.race_id = b.race_id
        """


