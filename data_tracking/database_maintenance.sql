BEGIN;

UPDATE Race
SET track_name = "Sakura Sanctuary"
WHERE Race.track_name = "82e09e8fd5cfb508cb6a32e541482e54edb7c488";

DELETE FROM Track WHERE track.track_name = "82e09e8fd5cfb508cb6a32e541482e54edb7c488";


UPDATE Race
SET track_name = "Yoshi Lagoon"
WHERE Race.track_name = "bdd740698e60f8c388d78dba17449c3efa661776";

DELETE FROM Track WHERE track.track_name = "bdd740698e60f8c388d78dba17449c3efa661776";


UPDATE Race
SET track_name = "SNES Dount Plains 3 "
WHERE Race.track_name = "3dbd5e5e3084972aa3fefc0ffc06d7d02253cde9";

DELETE FROM Track WHERE track.track_name = "3dbd5e5e3084972aa3fefc0ffc06d7d02253cde9";


UPDATE Race
SET track_name = "Waluigi's Motocross"
WHERE Race.track_name = "9f09ddb05bc5c7b04bb7aa120f6d0f21774143eb";

DELETE FROM Track WHERE track.track_name = "9f09ddb05bc5c7b04bb7aa120f6d0f21774143eb";


UPDATE Race
SET track_name = "Magmatic Sanctuary"
WHERE Race.track_name = "8fb80a10b8b1bcdc89d1395eecf332769e4d233b";

DELETE FROM Track WHERE track.track_name = "8fb80a10b8b1bcdc89d1395eecf332769e4d233b";


UPDATE Race
SET track_name = "Icepeak Mountain"
WHERE Race.track_name = "a1e5087b9951410f9b590fd1d6d831357167a3b6";

DELETE FROM Track WHERE track.track_name = "a1e5087b9951410f9b590fd1d6d831357167a3b6";


UPDATE Race
SET track_name = "GCN Wario Colosseum"
WHERE Race.track_name = "511ba4d7f0d79cc2ac3e6834c552a81ae95f1475";

DELETE FROM Track WHERE track.track_name = "511ba4d7f0d79cc2ac3e6834c552a81ae95f1475";


UPDATE Race
SET track_name = "Daisy's Palace"
WHERE Race.track_name = "8c9a6275d7dc12d5644e7261bf4fff42597c0b1a";

DELETE FROM Track WHERE track.track_name = "8c9a6275d7dc12d5644e7261bf4fff42597c0b1a";


UPDATE Race
SET track_name = "Fishdom Island"
WHERE Race.track_name = "2d5d297545c80e0d5e714c8e8b0d0aa6e3db1cbc";

DELETE FROM Track WHERE track.track_name = "2d5d297545c80e0d5e714c8e8b0d0aa6e3db1cbc";


COMMIT;

DROP VIEW IF EXISTS room_sizes;
VACUUM; /*Shrink Database, necessary to keep Database minimal size, especially if the scripts in the migration folder just ran (and doubled the DB size)*/