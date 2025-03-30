CREATE SCHEMA IF NOT EXISTS game_info;

CREATE TABLE IF NOT EXISTS game_info.games (
	game_id int,
	game_type text,
	game_name text,
	is_free bool,
	descrip_detail text,
	descrip_short text,
	developer text,
	publisher text,
	price text,
	platforms text[],
	metacritic_score int,
	metacritic_review text,
	categories text[],
	genres text[],
	recommendations int,
	release_date text,
	PRIMARY KEY (game_id, game_type, game_name)
);

ALTER TABLE game_info.games ADD CONSTRAINT unique_game_id UNIQUE (game_id);


CREATE TABLE IF NOT EXISTS game_info.reviews(
	rec_id text,
	game_id int REFERENCES game_info.games (game_id), 
	author_id text,
	author_playtime int,
	review text,
	voted_up bool,
	votes_up int,
	votes_funny int,
	weighted_vote_score numeric,
	PRIMARY KEY (rec_id, game_id, author_id)
);


