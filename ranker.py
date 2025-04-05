import psycopg
import itertools
from scipy.sparse import csr_matrix

# Want to use collaborative filtering and matrix factorization

# For CF
# Assemble the matrix
# Use the weighted vote score

def get_all_game_ids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT game_id FROM game_info.games")
        results = cur.fetchall()
        ids = [x[0] for x in results]
        return ids

def get_all_reviewers(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT author_id FROM game_info.reviews")
        results = cur.fetchall()
        reviewers = [x[0] for x in results]
        return reviewers

def get_game_review(conn, author_id, game_id):
    with conn.cursor() as cur:
        cur.execute(f"SELECT weighted_vote_score FROM game_info.reviews WHERE author_id='{author_id}' AND game_id='{game_id}' ")
        result = cur.fetchone()
        if result is not None:
            return result[0]
        return result

def get_review_attributes(conn):
    with conn.cursor() as cur:
        cur.execute(f"SELECT game_id, author_id, weighted_vote_score FROM game_info.reviews")
        results = cur.fetchall()
        return results


def build_ratings_matrix(conn):
    game_ids = get_all_game_ids(conn)
    reviewer_ids = get_all_reviewers(conn)
    reviewer_to_idx = {r: i for i, r in enumerate(reviewer_ids)}
    game_to_idx = {g: i for i, g in enumerate(game_ids)}
    game_idx = []
    review_idx = []
    data_cell = []
    db_reviews = get_review_attributes(conn)
    for review in db_reviews:
        data_cell.append(float(review[2]))
        game_idx.append(game_to_idx[review[0]])
        review_idx.append(reviewer_to_idx[review[1]])

    review_matrix = csr_matrix((data_cell, (review_idx, game_idx)), shape=(len(reviewer_ids), len(game_ids)))
    return review_matrix


if __name__=="__main__":
    with psycopg.connect(host='localhost', dbname='game_reviews', user='main', password='access123', port=5432) as conn:
        ratings_matrix = build_ratings_matrix(conn)


