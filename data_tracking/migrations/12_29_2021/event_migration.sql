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
