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