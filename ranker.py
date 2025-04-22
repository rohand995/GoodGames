import psycopg
import numpy as np
import nimfa
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


# Want to use collaborative filtering and matrix factorization
# ARCHFLAGS="-arch arm64" SDKROOT=$(xcrun --sdk macosx --show-sdk-path) pip install scikit-surprise
# Convoluted pip install for Apple Silicon

# For CF
# Assemble the matrix
# Use the weighted vote score

mf_matrix = np.load('mf-matrix.npy')
item_cf_matrix = np.load('item-cf.npy')



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

def funk_svd(csr_data, k=20, steps=50, alpha=0.005, reg=0.02, verbose=True):
    n_users, n_items = csr_data.shape
    P = np.random.normal(scale=1./k, size=(n_users, k))
    Q = np.random.normal(scale=1./k, size=(n_items, k))

    csr_data = csr_data.tocoo()  # Efficient iteration

    for step in range(steps):
        total_loss = 0
        for u, i, r_ui in zip(csr_data.row, csr_data.col, csr_data.data):
            pred = np.dot(P[u], Q[i])
            error = r_ui - pred
            total_loss += error ** 2

            # Gradient Descent update
            P[u] += alpha * (error * Q[i] - reg * P[u])
            Q[i] += alpha * (error * P[u] - reg * Q[i])

        if verbose and (step % 5 == 0 or step == steps - 1):
            rmse = np.sqrt(total_loss / len(csr_data.data))
            print(f"Step {step+1}/{steps}: RMSE = {rmse:.4f}")

    return P @ Q.T  # Final predicted matrix

with psycopg.connect(host='localhost', dbname='game_reviews', user='main', password='access123', port=5432) as conn:
    ratings_matrix, reviewer_map, game_map = build_ratings_matrix(conn)

alpha = .6
combined_rank = alpha * mf_matrix + (1-alpha) * mf_matrix

if __name__=="__main__":
    with psycopg.connect(host='localhost', dbname='game_reviews', user='main', password='access123', port=5432) as conn:
        ratings_matrix, reviewer_map, game_map = build_ratings_matrix(conn)
        # Uncomment for item-item CF
        # mu, b_u, b_i = compute_baselines(ratings_matrix)
        # sim = compute_item_similarities(ratings_matrix)
        # P = predict_all(ratings_matrix, sim, mu, b_u, b_i, k=5)
        # np.save('item-cf.npy',P)
        # P = np.load('item-cf.npy')
        # print(P)
        # Uncomment for MF model
        # P = funk_svd(ratings_matrix,25, steps=2000)
        # print(P)
        # np.save('mf-matrix.npy', P)
        # print(combined_rank)
        # P = np.load('mf-matrix.npy')
        # print(P)




