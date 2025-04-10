import psycopg

import random #temporary

#TODO: this function uses MF/CF to get the scores of each game for a single user
#the return value is a dictionary of [game id] -> recommendation score
def recommend_single(steam_id: str) -> dict[str, float]:
    with psycopg.connect(host='localhost', dbname='postgres', user='main', password='access123', port=5432) as conn:
        with conn.cursor() as cur:
            # cur.execute("SELECT game_id FROM game_info.games ORDER BY RANDOM() LIMIT 8;")
            cur.execute("SELECT game_id FROM game_info.games ORDER BY RANDOM() LIMIT 32;")
            game_ids = [row[0] for row in cur.fetchall()]
        return {game_id: random.random() for game_id in game_ids}

#a function that combines each user's score for a game into a single group score
#currently we'll combine by multiplication
def combine_scores(scores: list[float]):
    val = 1
    for s in scores:
        val = val * s
    return val

#similar to the above, but this function combines multiple ranking dictionaries to get a combined ranking for a whole group of users
def recommend_multiple(steam_ids: list[str]) -> dict[str, float]:
    per_user_lists = [recommend_single(id) for id in steam_ids]
    #get the list of game ids that have scores
    game_ids = {game_id for user_list in per_user_lists for game_id in user_list}
    #collect the user scores for each game (default 0 if a game is somehow missing a score for some user)
    per_game_score_lists = {game_id: [user_list.get(game_id, 0.0) for user_list in per_user_lists] for game_id in game_ids}
    #combine somehow
    per_game_scores = {game_id: combine_scores(scores) for game_id, scores in per_game_score_lists.items()}
    #done!
    return per_game_scores
    #the caller just has to take the dict and sort descending by score

def get_recommendations(steam_ids): # use steam_ids later for reccomendations
    per_game_scores = recommend_multiple(steam_ids)
    game_list = sorted([(game_id, score) for game_id, score in per_game_scores.items() if score > 0], key = lambda x: -x[1])
    #round down length of list to nearest multiple of 4, unless fewer than 4 games were returned
    N = len(game_list)
    if N > 4:
        N = N - (N % 4)
    #
    recommendations = [game_id for game_id, _ in game_list][:N]
    #
    return recommendations
    
def get_game_info(game_ids):
    with psycopg.connect(host='localhost', dbname='postgres', user='main', password='access123', port=5432) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT game_id, game_name, genres, price, release_date, metacritic_score, capsule_image, descrip_short
                FROM game_info.games
                WHERE game_id = ANY(%s);
            """, (game_ids,))
            
            rows = cur.fetchall()
            games = []
            for row in rows:
                game = {
                    "game_id": row[0],
                    "name": row[1],
                    "genres": row[2],
                    "price": row[3],
                    "release_date": row[4],
                    "rating": row[5],
                    "image_url": row[6],
                    "description": row[7],
                    "store_url": f"https://store.steampowered.com/app/{row[0]}"
                }
                games.append(game)
            return games    

def main():
    # for testing purposes
    game_ids = get_recommendations([])
    print(game_ids)
    game_info = get_game_info(game_ids)
    print(game_info[0])

if __name__ == '__main__':
    main()
