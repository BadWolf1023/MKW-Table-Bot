
BEGIN;

/* Sakura Sanctuary SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("Sakura Sanctuary", "No Track Page", "Sakura Sanctuary", 1, "sakurasanctuary");

UPDATE Race
SET track_name = "Sakura Sanctuary"
WHERE Race.track_name = "82e09e8fd5cfb508cb6a32e541482e54edb7c488";

DELETE FROM Track WHERE track.track_name = "82e09e8fd5cfb508cb6a32e541482e54edb7c488";



/* Yoshi Lagoon SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("Yoshi Lagoon", "No Track Page", "Yoshi Lagoon", 1, "yoshilagoon");

UPDATE Race
SET track_name = "Yoshi Lagoon"
WHERE Race.track_name = "bdd740698e60f8c388d78dba17449c3efa661776";

DELETE FROM Track WHERE track.track_name = "bdd740698e60f8c388d78dba17449c3efa661776";



/* SNES Donut Plains 3 SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("SNES Dount Plains 3", "No Track Page", "SNES Dount Plains 3", 1, "snesdountplains3");

UPDATE Race
SET track_name = "SNES Dount Plains 3"
WHERE Race.track_name = "3dbd5e5e3084972aa3fefc0ffc06d7d02253cde9";

DELETE FROM Track WHERE track.track_name = "3dbd5e5e3084972aa3fefc0ffc06d7d02253cde9";



/* Waluigi's Motocross SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("Waluigi's Motocross", "No Track Page", "Waluigi's Motocross", 1, "waluigi'smotocross");

UPDATE Race
SET track_name = "Waluigi's Motocross"
WHERE Race.track_name = "9f09ddb05bc5c7b04bb7aa120f6d0f21774143eb";

DELETE FROM Track WHERE track.track_name = "9f09ddb05bc5c7b04bb7aa120f6d0f21774143eb";



/* Magmatic Sanctuary SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("Magmatic Sanctuary", "No Track Page", "Magmatic Sanctuary", 1, "magmaticsanctuary");

UPDATE Race
SET track_name = "Magmatic Sanctuary"
WHERE Race.track_name = "8fb80a10b8b1bcdc89d1395eecf332769e4d233b";

DELETE FROM Track WHERE track.track_name = "8fb80a10b8b1bcdc89d1395eecf332769e4d233b";



/* Icepeak Mountain SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("Icepeak Mountain", "No Track Page", "Icepeak Mountain", 1, "icepeakmountain");

UPDATE Race
SET track_name = "Icepeak Mountain"
WHERE Race.track_name = "a1e5087b9951410f9b590fd1d6d831357167a3b6";

DELETE FROM Track WHERE track.track_name = "a1e5087b9951410f9b590fd1d6d831357167a3b6";



/* GCN Wario Colosseum SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("GCN Wario Colosseum", "No Track Page", "GCN Wario Colosseum", 1, "gcnwariocolosseum");

UPDATE Race
SET track_name = "GCN Wario Colosseum"
WHERE Race.track_name = "511ba4d7f0d79cc2ac3e6834c552a81ae95f1475";

DELETE FROM Track WHERE track.track_name = "511ba4d7f0d79cc2ac3e6834c552a81ae95f1475";



/* Daisy's Palace SHA Retroactive Fix */
INSERT OR IGNORE INTO Track VALUES("Daisy's Palace", "No Track Page", "Daisy's Palace", 1, "daisy'spalace");

UPDATE Race
SET track_name = "Daisy's Palace"
WHERE Race.track_name = "8c9a6275d7dc12d5644e7261bf4fff42597c0b1a";

DELETE FROM Track WHERE track.track_name = "8c9a6275d7dc12d5644e7261bf4fff42597c0b1a";


UPDATE Race
SET track_name = "Fishdom Island"
WHERE Race.track_name = "2d5d297545c80e0d5e714c8e8b0d0aa6e3db1cbc";

DELETE FROM Track WHERE track.track_name = "2d5d297545c80e0d5e714c8e8b0d0aa6e3db1cbc";


COMMIT;


VACUUM; /*Shrink Database, necessary to keep Database minimal size, especially if the scripts in the migration folder just ran (and doubled the DB size)*/