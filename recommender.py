import psycopg

def get_recommendations(steam_ids): # use steam_ids later for reccomendations
    with psycopg.connect(host='localhost', dbname='postgres', user='main', password='access123', port=5432) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT game_id FROM game_info.games ORDER BY RANDOM() LIMIT 8;")
            game_ids = [row[0] for row in cur.fetchall()]
        return game_ids
    
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
