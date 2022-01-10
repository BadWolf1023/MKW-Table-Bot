CREATE TABLE IF NOT EXISTS Player_FCs(
    fc TEXT NOT NULL,
    discord_id INT,
    PRIMARY KEY(fc)
);

CREATE TABLE IF NOT EXISTS Score_Matrix(
    size INT,
    place INT,
    pts INT,
    PRIMARY KEY (size, place)
);

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

DELETE FROM Event_ID WHERE event_id IN
							(SELECT event_id FROM Event_ID WHERE event_id NOT IN (
																			SELECT event_id FROM Event
																			INTERSECT SELECT event_id FROM Event_Structure
																			INTERSECT SELECT event_id FROM Event_FCs
																			INTERSECT SELECT event_id FROM Event_Races)
							);


/* WARNING WARNING WARNING

   WARNING WARNING WARNING
   WARNING WARNING WARNING
   WARNING WARNING WARNING
   WARNING WARNING WARNING:
- BEFORE YOU RUN THIS FILE, CREATE A SAFE BACKUP (a backup created while software has the database open [eg Table Bot or a DB viewing software] is NOT a safe backup)
- DO NOT RUN THIS FILE UNLESS YOU KNOW EXACTLY WHAT YOU ARE DOING
- MAKE SURE THE DATABASE SCHEMA IN THIS FILE OF THE TABLES BEING CREATED MATCHES THE SCHEMA OF THE TABLES IN THE DATABASE YOU WILL BE RUNNING IT ON WITH THE EXCEPTION OF THE "ON DELETE" STATEMENTS
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

create table Place2
(
	race_id INT UNSIGNED not null
		references Race
			on update cascade on delete restrict,
	fc TEXT not null
		references Player
			on update cascade on delete restrict,
	name TEXT not null,
	place INT not null,
	time DOUBLE(8,3),
	lag_start DOUBLE(8,2),
	ol_status TEXT not null,
	room_position INT not null,
	region TEXT not null,
	connection_fails DOUBLE(8,2),
	role TEXT not null,
	vr INT,
	character TEXT,
	vehicle TEXT,
	discord_name TEXT,
	lounge_name TEXT,
	mii_hex TEXT,
	is_wiimmfi_place TINYINT(1) not null,
	primary key (fc, race_id)
);


insert into Place2(race_id, fc, name, place, time, lag_start, ol_status, room_position, region, connection_fails, role, vr, character, vehicle, discord_name, lounge_name, mii_hex, is_wiimmfi_place)
select race_id, fc, name, place,
       substr(time, 0, instr(time, ':')) * 60 + substr(time, instr(time, ':')+1, length(time)), lag_start, ol_status, room_position, region, connection_fails, role, vr, character, vehicle, discord_name, lounge_name, mii_hex, is_wiimmfi_place from Place;

drop table Place;
alter table Place2 rename to Place;

PRAGMA foreign_keys= OFF;

DROP TABLE IF EXISTS Race2;
CREATE TABLE Race2
(
    race_id          INT UNSIGNED NOT NULL
        PRIMARY KEY,
    rxx              TEXT         NOT NULL,
    time_added       TIMESTAMP    NOT NULL,
    match_time       TEXT         NOT NULL,
    race_number      INT          NOT NULL,
    room_name        TEXT         NOT NULL,
    track_name       TEXT         NOT NULL
        REFERENCES Track
            ON UPDATE CASCADE ON DELETE RESTRICT,
    room_type        TEXT         NOT NULL,
    cc               TEXT         NOT NULL,
    region           TEXT,
    is_wiimmfi_race  TINYINT(1)   NOT NULL,
    num_players      int,
    first_place_time DOUBLE(8, 3),
    last_place_time  DOUBLE(8, 3),
    avg_time         DOUBLE(8, 3)
);

DROP VIEW IF EXISTS room_sizes;

CREATE VIEW room_sizes AS
SELECT race_id,
       COUNT(*)                               AS num_players,
       MIN(time) FILTER (WHERE time < 6 * 60) AS first_place_time,
       MAX(time) FILTER (WHERE time < 6 * 60) AS last_place_time,
       AVG(time) FILTER (WHERE time < 6 * 60) AS avg_time
FROM Place
GROUP BY race_id;

INSERT INTO Race2(race_id, rxx, time_added, match_time, race_number, room_name, track_name, room_type, cc, region,
                  is_wiimmfi_race, num_players, first_place_time, last_place_time, avg_time)
SELECT Race.race_id,
       rxx,
       time_added,
       match_time,
       race_number,
       room_name,
       track_name,
       room_type,
       cc,
       region,
       is_wiimmfi_race,
       num_players,
       room_sizes.first_place_time,
       room_sizes.last_place_time,
       room_sizes.avg_time
FROM Race
         JOIN room_sizes ON Race.race_id = room_sizes.race_id
;

DROP TABLE Race;
ALTER TABLE Race2 RENAME TO Race;
DROP VIEW IF EXISTS room_sizes;

PRAGMA foreign_keys= ON;

PRAGMA foreign_keys= OFF;

DROP TABLE IF EXISTS Event2;
CREATE TABLE Event2(
    event_id INT NOT NULL /*This is a unique ID that table bot generates for each war that is started with ?sw. (Okay, Table Bot doesn''t need to generate it actually! Discord messages all have a unique ID and we''ll use those!)*/,
    channel_id INT NOT NULL,
    time_added TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    number_of_updates INT UNSIGNED NOT NULL,
    region TEXT NOT NULL,
    set_up_user_discord_id INT NULL,
    set_up_user_display_name TEXT NULL,
    player_setup_amount INT NOT NULL,
    PRIMARY KEY(event_id),
    FOREIGN KEY (event_id)
	REFERENCES Event_ID(event_id)
	ON UPDATE CASCADE
	ON DELETE RESTRICT
);


INSERT INTO Event2(event_id, channel_id, time_added, last_updated, number_of_updates, region, set_up_user_discord_id, set_up_user_display_name, player_setup_amount)
SELECT Event.event_id, Event.channel_id, Event.time_added, Event.last_updated, Event.number_of_updates, Event.region, Event.set_up_user_discord_id, Event.set_up_user_display_name, Event_Structure.player_setup_amount
FROM Event LEFT JOIN Event_Structure USING(event_id)
;

DROP TABLE Event;
ALTER TABLE Event2 RENAME TO Event;

PRAGMA foreign_keys= ON;

VACUUM;
