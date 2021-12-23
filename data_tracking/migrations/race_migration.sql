DROP TABLE IF EXISTS  Race2;
create table Race2
(
	race_id2 INT UNSIGNED not null
		primary key,
	rxx TEXT not null,
	time_added TIMESTAMP not null,
	match_time TEXT not null,
	race_number INT not null,
	room_name TEXT not null,
	track_name TEXT not null
		references Track
			on update cascade on delete restrict,
	room_type TEXT not null,
	cc TEXT not null,
	region TEXT,
	is_wiimmfi_race TINYINT(1) not null,
	num_players int
);

DROP VIEW IF EXISTS room_sizes;
CREATE VIEW room_sizes AS
    SELECT Place.race_id, count(*) as num_players
    from Place
    group by Place.race_id;

insert into Race2(race_id2, rxx, time_added, match_time, race_number, room_name, track_name, room_type, cc, region, is_wiimmfi_race, num_players)
select Race.race_id, rxx, time_added, match_time, race_number, room_name, track_name, room_type, cc, region, is_wiimmfi_race, num_players
from Race
join room_sizes on Race.race_id = room_sizes.race_id
;

drop table Race;
alter table Race2 rename to Race;