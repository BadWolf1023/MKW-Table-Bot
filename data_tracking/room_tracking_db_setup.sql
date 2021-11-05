BEGIN;
CREATE TABLE Place(
    race_id INT UNSIGNED NOT NULL,
    fc TEXT NOT NULL,
    name TEXT NOT NULL,
    place INT NOT NULL,
    time TIME NULL,
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
    PRIMARY KEY(fc, race_id)
    FOREIGN KEY (race_id)
       REFERENCES Race(race_id)
          ON UPDATE CASCADE
          ON DELETE RESTRICT,
    FOREIGN KEY (fc)
       REFERENCES Player(fc)
          ON UPDATE CASCADE
          ON DELETE RESTRICT
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
           ON DELETE RESTRICT
);

CREATE TABLE Track(
    track_name TEXT NOT NULL,
    url TEXT NULL,
    fixed_track_name INT NOT NULL,
    is_ct TINYINT(1) NOT NULL,
    track_name_lookup TEXT NOT NULL,
    PRIMARY KEY(track_name)
);

CREATE TABLE Player(
    fc TEXT NOT NULL,
    pid INT UNSIGNED NOT NULL,
    player_url TEXT NOT NULL,
    PRIMARY KEY(fc)
);

CREATE TABLE Event_ID(
    event_id INT NOT NULL /*This is a unique ID that table bot generates for each war that is started with ?sw. (Okay, Table Bot doesn''t need to generate it actually! Discord messages all have a unique ID and we''ll use those!)*/,
    PRIMARY KEY(event_id)

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
	ON DELETE RESTRICT

);

CREATE TABLE Tier(
    channel_id INT UNSIGNED NOT NULL,
    tier INT NOT NULL,
    is_ct TINYINT(1) NOT NULL,
    PRIMARY KEY(channel_id)
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
       ON DELETE RESTRICT
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
           ON DELETE RESTRICT
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
    event_name TEXT NOT NULL,
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
COMMIT;