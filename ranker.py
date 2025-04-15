import psycopg
import numpy as np
import nimfa
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

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
    return review_matrix, reviewer_to_idx, game_to_idx


def compute_baselines(R):
    mu = R.data.mean()
    user_means = np.array(R.mean(axis=1)).flatten()
    item_means = np.array(R.mean(axis=0)).flatten()

    b_u = user_means - mu
    b_i = item_means - mu
    return mu, b_u, b_i


def compute_item_similarities(R):
    item_matrix = R.T.tocsr()
    sim = cosine_similarity(item_matrix)
    return sim


def predict_all(R, sim, mu, b_u, b_i, k=5):
    num_users, num_items = R.shape
    P = np.zeros((num_users, num_items))

    for u in range(num_users):
        user_rated_items = R[u].indices
        for i in range(num_items):
            # Skip if already rated (optional)
            # if i in user_rated_items:
            #     P[u, i] = R[u, i]
            #     continue

            similarities = sim[i, user_rated_items]
            if len(similarities) == 0:
                baseline_ui = mu + b_u[u] + b_i[i]
                P[u, i] = baseline_ui
                continue

            top_k_idx = np.argsort(similarities)[-k:]
            top_items = user_rated_items[top_k_idx]
            top_sims = similarities[top_k_idx]

            numer = 0.0
            denom = 0.0
            for j, s_ij in zip(top_items, top_sims):
                r_uj = R[u, j]
                baseline_uj = mu + b_u[u] + b_i[j]
                numer += s_ij * (r_uj - baseline_uj)
                denom += abs(s_ij)

            baseline_ui = mu + b_u[u] + b_i[i]
            if denom == 0:
                P[u, i] = baseline_ui
            else:
                P[u, i] = baseline_ui + numer / denom
    return P

def perform_nmf(R, rank=10, max_iter=100):
    """
    Perform NMF on a CSR user-item matrix using nimfa.
    Returns the full predicted matrix as a NumPy ndarray.
    """
    R = R.astype(np.float32)

    nmf = nimfa.Nmf(R, rank=rank, max_iter=max_iter, update='euclidean', objective='fro')
    nmf_fit = nmf()

    # Convert factor matrices to numpy arrays
    W = np.array(nmf_fit.basis())
    H = np.array(nmf_fit.coef())

    # Reconstruct and return the dense user-item prediction matrix
    R_hat = np.dot(W, H)  # shape: (num_users, num_items)
    return R_hat.toarray()

if __name__=="__main__":
    with psycopg.connect(host='localhost', dbname='game_reviews', user='main', password='access123', port=5432) as conn:
        ratings_matrix, reviewer_map, game_map = build_ratings_matrix(conn)
        # mu, b_u, b_i = compute_baselines(ratings_matrix)
        # sim = compute_item_similarities(ratings_matrix)
        # P = predict_all(ratings_matrix, sim, mu, b_u, b_i, k=5)
        # np.save('item-cf.npy',P)
        # P = np.load('item-cf.npy')
        # print(P)
        # P = perform_nmf(ratings_matrix,5,1000)
        # print(P)
        # np.save('mf-matrix.npy', P)
        # P = np.load('mf-matrix.npy')
        # print(P)




