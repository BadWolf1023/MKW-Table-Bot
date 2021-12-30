/* WARNING WARNING WARNING
	
   WARNING WARNING WARNING 
   WARNING WARNING WARNING 
   WARNING WARNING WARNING 
   WARNING WARNING WARNING:
- BEFORE YOU RUN THIS FILE, CREATE A SAFE BACKUP (a backup created while software has the database open [eg Table Bot or a DB viewing software] is NOT a safe backup)
- DO NOT RUN THIS FILE UNLESS YOU KNOW EXACTLY WHAT YOU ARE DOING
- MAKE SURE THE DATABASE SCHEMA IN THIS FILE OF THE TABLES BEING CREATED MATCHES THE SCHEMA OF THE TABLES IN THE DATABASE YOU WILL BE RUNNING IT ON WITH THE EXCEPTION OF THE "ON DELETE" STATEMENTS
- AFTER RUNNING THIS FILE, AND AFTER YOU DELETE THE MINIMAL INFORMATION FROM THE DATABASE, MAKE SURE YOU READ THE INSTRUCTIONS IN "database_restrict_delete.sql" AND THEN RUN IT
*/







/* WARNING: DID YOU READ THE ABOVE WARNING? YOU RISK PERMANENT DATA LOSS IF YOU ARE NOT READING CAREFULLY. */
PRAGMA foreign_keys=off;
BEGIN;
ALTER TABLE Place RENAME TO _Place_old;
ALTER TABLE Race RENAME TO _Race_old;
ALTER TABLE Event RENAME TO _Event_old;
ALTER TABLE Event_Races RENAME TO _Event_Races_old;
ALTER TABLE Event_FCs RENAME TO _Event_FCs_old;
ALTER TABLE Event_Structure RENAME TO _Event_Structure_old;

CREATE TABLE Place(
    race_id INT UNSIGNED NOT NULL,
    fc TEXT NOT NULL,
    name TEXT NOT NULL,
    place INT NOT NULL,
    time DOUBLE(8, 3) NULL,
    lag_start DOUBLE(8, 2) NULL,
    ol_status TEXT NOT NULL,
    room_position INT NOT NULL,
    region TEXT NOT NULL,
    connection_fails DOUBLE(8, 2) NULL,
    role TEXT NOT NULL,
    vr INT NULL,
    character TEXT NULL,
    vehicle TEXT NULL,
    discord_name TEXT NULL,
    lounge_name TEXT NULL,
    mii_hex TEXT NULL,
    is_wiimmfi_place TINYINT(1) NOT NULL,
    PRIMARY KEY(fc, race_id),
    FOREIGN KEY (race_id)
       REFERENCES Race(race_id)
          ON UPDATE CASCADE
          ON DELETE RESTRICT,
    FOREIGN KEY (fc)
       REFERENCES Player(fc)
          ON UPDATE CASCADE
          ON DELETE CASCADE
);

CREATE TABLE Race(
    race_id INT UNSIGNED NOT NULL,
    rxx TEXT NOT NULL,
    time_added TIMESTAMP NOT NULL,
    match_time TEXT NOT NULL,
    race_number INT NOT NULL /*Should be the race number of the local room, not the race number of a specific table (because ?mergeroom can be done which would throw this value off*/,
    room_name TEXT NOT NULL /*This is ''roomID'', but is actually the room name on mkwx which are recycled (eg BH40)*/,
    track_name TEXT NOT NULL,
    room_type TEXT NOT NULL,
    cc TEXT NOT NULL,
    region TEXT NULL,
    is_wiimmfi_race TINYINT(1) NOT NULL,
    PRIMARY KEY(race_id),
    FOREIGN KEY (track_name)
       REFERENCES Track(track_name)
          ON UPDATE CASCADE
           ON DELETE CASCADE
);

CREATE TABLE Event(
    event_id INT NOT NULL /*This is a unique ID that table bot generates for each war that is started with ?sw. (Okay, Table Bot doesn''t need to generate it actually! Discord messages all have a unique ID and we''ll use those!)*/,
    channel_id INT NOT NULL,
    time_added TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    number_of_updates INT UNSIGNED NOT NULL,
    region TEXT NOT NULL,
    set_up_user_discord_id INT NULL,
    set_up_user_display_name TEXT NULL,
    PRIMARY KEY(event_id),
    FOREIGN KEY (event_id)
	REFERENCES Event_ID(event_id)
	ON UPDATE CASCADE
	ON DELETE CASCADE

);


CREATE TABLE Event_Races(
    event_id INT UNSIGNED NOT NULL,
    race_id INT UNSIGNED NOT NULL,
    PRIMARY KEY(event_id, race_id),
    FOREIGN KEY (race_id)
    REFERENCES Race(race_id)
       ON UPDATE CASCADE
       ON DELETE RESTRICT,
    FOREIGN KEY (event_id)
    REFERENCES Event_ID(event_id)
       ON UPDATE CASCADE
       ON DELETE CASCADE
);

CREATE TABLE Event_FCs(
    event_id INT UNSIGNED NOT NULL,
    fc TEXT NOT NULL,
    mii_hex TEXT NULL,
    PRIMARY KEY(event_id, fc),
    FOREIGN KEY (fc)
       REFERENCES Player(fc)
          ON UPDATE CASCADE
           ON DELETE RESTRICT,
    FOREIGN KEY (event_id)
       REFERENCES Event_ID(event_id)
          ON UPDATE CASCADE
           ON DELETE CASCADE
);

CREATE TABLE Event_Structure(
    event_id INT UNSIGNED NOT NULL,
    name_changes JSON NOT NULL,
    removed_races JSON NOT NULL,
    placement_history JSON NOT NULL,
    forced_room_size JSON NOT NULL,
    player_penalties JSON NOT NULL,
    team_penalties JSON NOT NULL,
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
           ON DELETE CASCADE
);


INSERT INTO Place SELECT * FROM _Place_old;
INSERT INTO Race SELECT * FROM _Race_old;
INSERT INTO Event SELECT * FROM _Event_old;
INSERT INTO Event_Races SELECT * FROM _Event_Races_old;
INSERT INTO Event_FCs SELECT * FROM _Event_FCs_old;
INSERT INTO Event_Structure SELECT * FROM _Event_Structure_old;

DROP TABLE _Place_old;
DROP TABLE _Race_old;
DROP TABLE _Event_old;
DROP TABLE _Event_Races_old;
DROP TABLE _Event_FCs_old;
DROP TABLE _Event_Structure_old;


COMMIT;

PRAGMA foreign_keys=on;

VACUUM;