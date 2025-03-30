import psycopg
import json
import re
import os


class GameRecord:
    def __init__(self, **kwargs):
        self.game_id = kwargs.get("game_id")
        self.game_type = kwargs.get("game_type")
        self.game_name = kwargs.get("game_name")
        self.is_free = kwargs.get("is_free")
        self.descrip_detail = kwargs.get("descrip_detail")
        self.descrip_short = kwargs.get("descrip_short")
        self.developer = kwargs.get("developer")
        self.publisher = kwargs.get("publisher")
        self.price = kwargs.get("price")
        self.platforms = kwargs.get("platforms", [])  # Default to empty list
        self.metacritic_score = kwargs.get("metacritic_score")
        self.metacritic_review = kwargs.get("metacritic_review")
        self.categories = kwargs.get("categories", [])  # Default to empty list
        self.genres = kwargs.get("genres", [])  # Default to empty list
        self.recommendations = kwargs.get("recommendations")
        self.release_date = kwargs.get("release_date")

    def __repr__(self):
        return (f"Game(game_id={self.game_id}, game_type='{self.game_type}', "
                f"game_name='{self.game_name}', is_free={self.is_free}, "
                f"developer='{self.developer}', publisher='{self.publisher}', "
                f"price='{self.price}', platforms={self.platforms}, "
                f"metacritic_score={self.metacritic_score}, genres={self.genres}, "
                f"release_date='{self.release_date}')")

    def to_tuple(self):
        return (self.game_id, self.game_type, self.game_name, self.is_free, self.descrip_detail,
                self.descrip_short, self.developer, self.publisher, self.price, self.platforms,
                self.metacritic_score, self.metacritic_review, self.categories, self.genres,
                self.recommendations, self.release_date)

class GameReview:
    def __init__(self, **kwargs):
        self.rec_id = kwargs.get("rec_id")
        self.game_id = kwargs.get("game_id")
        self.author_id = kwargs.get("author_id")
        self.author_playtime = kwargs.get("author_playtime")
        self.review = kwargs.get("review")
        self.voted_up = kwargs.get("voted_up")
        self.votes_up = kwargs.get("votes_up")
        self.votes_funny = kwargs.get("votes_funny")
        self.weighted_vote_score = kwargs.get("weighted_vote_score")

    def __repr__(self):
        return (f"Review(rec_id='{self.rec_id}', game_id={self.game_id}, author_id='{self.author_id}', "
                f"author_playtime={self.author_playtime}, voted_up={self.voted_up}, "
                f"votes_up={self.votes_up}, votes_funny={self.votes_funny}, "
                f"weighted_vote_score={self.weighted_vote_score})")

    def to_tuple(self):
        return (self.rec_id, self.game_id, self.author_id, self.author_playtime, self.review,
                self.voted_up, self.votes_up, self.votes_funny, self.weighted_vote_score)


def bulk_insert_games(conn, games):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE game_info.games CASCADE")
        query = """
        INSERT INTO game_info.games (
            game_id, game_type, game_name, is_free, descrip_detail, descrip_short,
            developer, publisher, price, platforms, metacritic_score, metacritic_review,
            categories, genres, recommendations, release_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.executemany(query, [game.to_tuple() for game in games])
        conn.commit()
        print(f"{len(games)} games inserted successfully!")

def bulk_insert_reviews(conn, reviews):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE game_info.reviews CASCADE")
        query = """
        INSERT INTO game_info.reviews (
            rec_id, game_id, author_id, author_playtime, review, voted_up,
            votes_up, votes_funny, weighted_vote_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.executemany(query, [review.to_tuple() for review in reviews])
        conn.commit()
        print(f"{len(reviews)} reviews inserted successfully!")

def parse_game_file(filepath):
    with open(filepath, 'r') as file:
        gf_json = json.load(file)
        game_record = GameRecord()
        game_key = list(gf_json.keys())[0]
        data_json = gf_json[game_key]
        # Loading game json into class to make database insertion easy
        game_record.game_id = data_json['data']['steam_appid']
        game_record.game_type = data_json['data']['type']
        game_record.game_name = data_json['data']['name']
        game_record.is_free = data_json['data']['is_free']
        game_record.descrip_detail = data_json['data']['detailed_description']
        game_record.descrip_short = data_json['data']['short_description']
        game_record.developer = data_json['data']['developers'][0]
        game_record.publisher = data_json['data']['publishers'][0]
        game_record.price = data_json['data']['price_overview']['final_formatted']
        game_platforms = data_json['data']['platforms']
        for key in game_platforms:
            if game_platforms[key] == True:
                game_record.platforms.append(key)
        try:
            game_record.metacritic_score = data_json['data']['metacritic']['score']
            game_record.metacritic_review = data_json['data']['metacritic']['url']
        except KeyError:
            game_record.metacritic_score = None
            game_record.metacritic_review = None
        game_categories = data_json['data']['categories']
        for value in game_categories:
            game_record.categories.append(value['description'])
        game_genres = data_json['data']['genres']
        for value in game_genres:
            game_record.genres.append(value['description'])
        game_record.recommendations = data_json['data']['recommendations']['total']
        game_record.release_date = data_json['data']['release_date']['date']
    return game_record

def parse_review_file(filepath):
    with open(filepath,'r') as file:
        file_name = re.search(r'app_\d+\.json', filepath).group(0)
        game_id = int(re.search(r'\d+',file_name).group(0))
        rf_json = json.load(file)
        review_records = []
        for review in rf_json:
            game_review = GameReview(game_id=game_id)
            game_review.rec_id = review['recommendationid']
            game_review.author_id = review['author']['steamid']
            game_review.author_playtime = review['author']['playtime_forever']
            game_review.review = review['review']
            game_review.voted_up = review['voted_up']
            game_review.votes_up = review['votes_up']
            game_review.votes_funny = review['votes_funny']
            game_review.weighted_vote_score = review['weighted_vote_score']
            review_records.append(game_review)
        return review_records



def main():
    # This is a cardinal sin when it comes to security, but who gives a damn its a local db!
    with psycopg.connect(host='localhost', dbname='game_reviews', user='main', password='access123', port=5432) as conn:
        game_dir = '../steam_apps/'
        review_dir = '../steam_reviews/'
        game_data = []
        for file in os.listdir(game_dir):
            game_data.append(parse_game_file(game_dir+file))
        print(len(game_data))
        review_data = []
        for file in os.listdir(review_dir):
            review_data = review_data + parse_review_file(review_dir+file)
        print(len(review_data))
        bulk_insert_games(conn, game_data)
        bulk_insert_reviews(conn, review_data)

if __name__ == '__main__':
    main()
