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