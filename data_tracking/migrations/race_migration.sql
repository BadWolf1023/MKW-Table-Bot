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
       room_sizes.num_players,
       room_sizes.first_place_time,
       room_sizes.last_place_time,
       room_sizes.avg_time
FROM Race
         JOIN room_sizes ON Race.race_id = room_sizes.race_id
;

DROP TABLE Race;
ALTER TABLE Race2 RENAME TO Race;

PRAGMA foreign_keys= ON;
