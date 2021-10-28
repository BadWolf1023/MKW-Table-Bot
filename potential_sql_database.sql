CREATE TABLE `Place`(
    `race_id` INT UNSIGNED NOT NULL,
    `fc` TEXT NOT NULL,
    `name` TEXT NOT NULL,
    `place` INT NOT NULL,
    `time` TIME NULL,
    `lag_start` DOUBLE(8, 2) NULL,
    `ol_status` TEXT NOT NULL,
    `room_position` INT NOT NULL,
    `room_type` TEXT NOT NULL,
    `connection_fails` DOUBLE(8, 2) NULL,
    `role` TEXT NOT NULL,
    `vr` INT NULL,
    `character` TEXT NULL,
    `vehicle` TEXT NULL,
    `discord_name` TEXT NULL,
    `lounge_name` TEXT NULL,
    `mii_hex` TEXT NULL
);
ALTER TABLE
    `Place` ADD INDEX `place_race_id_fc_index`(`race_id`, `fc`);
ALTER TABLE
    `Place` ADD UNIQUE `place_race_id_unique`(`race_id`);
ALTER TABLE
    `Place` ADD UNIQUE `place_fc_unique`(`fc`);
CREATE TABLE `Race`(
    `race_id` INT UNSIGNED NOT NULL,
    `rxx` TEXT NOT NULL,
    `time_added` TIMESTAMP NOT NULL,
    `match_time` TEXT NOT NULL,
    `race_number` INT NOT NULL COMMENT 'Should be the race number of the local room, not the race number of a specific table (because ?mergeroom can be done which would throw this value off)',
    `room_name` TEXT NOT NULL COMMENT 'This is \"roomID\", but is actually the room name on mkwx which are recycled (eg BH40)',
    `track_name` TEXT NOT NULL,
    `room_type` TEXT NOT NULL,
    `cc` TEXT NOT NULL,
    `region` TEXT NULL
);
ALTER TABLE
    `Race` ADD INDEX `race_race_id_index`(`race_id`);
ALTER TABLE
    `Race` ADD PRIMARY KEY `race_race_id_primary`(`race_id`);
ALTER TABLE
    `Race` ADD UNIQUE `race_rxx_unique`(`rxx`);
CREATE TABLE `Track`(
    `track_name` TEXT NOT NULL,
    `url` TEXT NULL,
    `fixed_track_name` INT NOT NULL,
    `is_ct` TINYINT(1) NOT NULL
);
ALTER TABLE
    `Track` ADD INDEX `track_track_name_index`(`track_name`);
ALTER TABLE
    `Track` ADD PRIMARY KEY `track_track_name_primary`(`track_name`);
CREATE TABLE `Player`(
    `fc` TEXT NOT NULL,
    `pid` INT UNSIGNED NOT NULL,
    `player_url` TEXT NOT NULL
);
ALTER TABLE
    `Player` ADD INDEX `player_fc_index`(`fc`);
ALTER TABLE
    `Player` ADD PRIMARY KEY `player_fc_primary`(`fc`);
CREATE TABLE `Event`(
    `event_id` INT NOT NULL COMMENT 'This is a unique ID that table bot generates for each war that is started with ?sw. (Okay, Table Bot doesn\'t need to generate it actually! Discord messages all have a unique ID and we\'ll use those!)',
    `channel_id` INT NOT NULL,
    `time_added` TIMESTAMP NOT NULL,
    `last_updated` TIMESTAMP NOT NULL,
    `number_of_updates` INT UNSIGNED NOT NULL,
    `room_type` TEXT NOT NULL,
    `set_up_user_discord_id` INT NULL,
    `set_up_user_display_name` TEXT NULL
);
ALTER TABLE
    `Event` ADD INDEX `event_event_id_index`(`event_id`);
ALTER TABLE
    `Event` ADD PRIMARY KEY `event_event_id_primary`(`event_id`);
ALTER TABLE
    `Event` ADD UNIQUE `event_channel_id_unique`(`channel_id`);
CREATE TABLE `Tier`(
    `channel_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `tier` INT NULL
);
ALTER TABLE
    `Tier` ADD INDEX `tier_channel_id_index`(`channel_id`);
ALTER TABLE
    `Tier` ADD PRIMARY KEY `tier_channel_id_primary`(`channel_id`);
CREATE TABLE `Event_Races`(
    `event_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `race_id` INT NOT NULL
);
ALTER TABLE
    `Event_Races` ADD UNIQUE `event_races_event_id_unique`(`event_id`);
ALTER TABLE
    `Event_Races` ADD UNIQUE `event_races_race_id_unique`(`race_id`);
CREATE TABLE `Event_FCs`(
    `event_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `fc` INT NOT NULL,
    `mii_hex` TEXT NULL
);
ALTER TABLE
    `Event_FCs` ADD UNIQUE `event_fcs_event_id_unique`(`event_id`);
ALTER TABLE
    `Event_FCs` ADD UNIQUE `event_fcs_fc_unique`(`fc`);
CREATE TABLE `Event_Structure`(
    `event_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name_changes` JSON NOT NULL,
    `removed_races` JSON NOT NULL,
    `placement_history` JSON NOT NULL,
    `forced_room_size` JSON NOT NULL,
    `player_penalties` JSON NOT NULL,
    `team_penalties` JSON NOT NULL,
    `disconnections_on_results` JSON NOT NULL,
    `sub_ins` JSON NOT NULL,
    `teams` JSON NOT NULL,
    `rxx_list` JSON NOT NULL,
    `edits` JSON NOT NULL,
    `ignore_large_times` TINYINT(1) NOT NULL,
    `missing_player_points` INT NOT NULL,
    `event_name` TEXT NOT NULL,
    `number_of_gps` INT NOT NULL,
    `player_setup_amount` INT NOT NULL,
    `number_of_teams` INT NOT NULL,
    `players_per_team` INT NOT NULL
);
ALTER TABLE
    `Event_Structure` ADD PRIMARY KEY `event_structure_event_id_primary`(`event_id`);
ALTER TABLE
    `Race` ADD CONSTRAINT `race_track_name_foreign` FOREIGN KEY(`track_name`) REFERENCES `Track`(`track_name`);
ALTER TABLE
    `Place` ADD CONSTRAINT `place_race_id_foreign` FOREIGN KEY(`race_id`) REFERENCES `Race`(`race_id`);
ALTER TABLE
    `Place` ADD CONSTRAINT `place_fc_foreign` FOREIGN KEY(`fc`) REFERENCES `Player`(`fc`);
ALTER TABLE
    `Event` ADD CONSTRAINT `event_channel_id_foreign` FOREIGN KEY(`channel_id`) REFERENCES `Tier`(`channel_id`);
ALTER TABLE
    `Event_Races` ADD CONSTRAINT `event_races_event_id_foreign` FOREIGN KEY(`event_id`) REFERENCES `Event`(`event_id`);
ALTER TABLE
    `Event_Races` ADD CONSTRAINT `event_races_race_id_foreign` FOREIGN KEY(`race_id`) REFERENCES `Race`(`race_id`);
ALTER TABLE
    `Event_FCs` ADD CONSTRAINT `event_fcs_event_id_foreign` FOREIGN KEY(`event_id`) REFERENCES `Event`(`event_id`);
ALTER TABLE
    `Event_FCs` ADD CONSTRAINT `event_fcs_fc_foreign` FOREIGN KEY(`fc`) REFERENCES `Player`(`fc`);
ALTER TABLE
    `Event_Races` ADD CONSTRAINT `event_races_event_id_foreign` FOREIGN KEY(`event_id`) REFERENCES `Event_Structure`(`event_id`);
ALTER TABLE
    `Event_FCs` ADD CONSTRAINT `event_fcs_event_id_foreign` FOREIGN KEY(`event_id`) REFERENCES `Event_Structure`(`event_id`);