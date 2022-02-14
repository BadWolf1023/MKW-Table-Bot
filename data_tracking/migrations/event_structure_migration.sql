PRAGMA foreign_keys=OFF;

DROP TABLE IF EXISTS Event_Structure_New;

CREATE TABLE Event_Structure_New(
    event_id INT UNSIGNED NOT NULL,
    name_changes JSON NOT NULL,
    removed_races JSON NOT NULL,
    placement_history JSON NOT NULL,
    forced_room_size JSON NOT NULL,
    player_penalties JSON NOT NULL,
    team_penalties JSON NOT NULL,
    manual_dc_placements JSON NOT NULL,
    disconnections_on_results JSON NOT NULL,
    sub_ins JSON NOT NULL,
    teams JSON NOT NULL,
    rxx_list JSON NOT NULL,
    edits JSON NOT NULL,
    ignore_large_times TINYINT(1) NOT NULL,
    missing_player_points INT NOT NULL,
    event_name TEXT NULL,
    number_of_gps INT NOT NULL,
    player_setup_amount INT NOT NULL,
    number_of_teams INT NOT NULL,
    players_per_team INT NOT NULL,
    PRIMARY KEY(event_id),
    FOREIGN KEY (event_id)
       REFERENCES Event_ID(event_id)
       ON UPDATE CASCADE
       ON DELETE RESTRICT
);


INSERT INTO Event_Structure_New(
    event_id,
    name_changes,
    removed_races,
    placement_history,
    forced_room_size,
    player_penalties,
    team_penalties,
    manual_dc_placements,
    disconnections_on_results,
    sub_ins,
    teams,
    rxx_list,
    edits,
    ignore_large_times,
    missing_player_points,
    event_name,
    number_of_gps,
    player_setup_amount,
    number_of_teams,
    players_per_team
)
SELECT event_id, name_changes, removed_races, placement_history, forced_room_size, player_penalties, team_penalties, 
    '{}', disconnections_on_results, sub_ins, teams, rxx_list, edits, ignore_large_times, missing_player_points, event_name, number_of_gps, 
    player_setup_amount, number_of_teams, players_per_team 
FROM Event_Structure;

DROP TABLE Event_Structure;
ALTER TABLE Event_Structure_New RENAME TO Event_Structure;

PRAGMA foreign_keys=ON;
VACUUM;