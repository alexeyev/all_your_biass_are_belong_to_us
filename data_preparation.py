# -*- coding: utf-8 -*-

import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors.approximate import LSHForest


def user2type(d):
    """
        Mapping users' names to user types: Bot/Human
        :param d:
        :return:
    """
    types = {item["id"]: item["userType"] for item in d["users"]}
    types["system"] = "Bot"
    return types


def build_replies_list(d):
    """
        Building a list of replies and corresponding user types (Bot/Human) for each reply
    :param d:  dialog as JSON
    :return: replies, usertypes
    """

    fixed_replies = []
    corresp_users = []

    json_replies = d["thread"]

    u2t = user2type(d)

    curr_user = "system"
    curr_reply = d["context"]
    i = 0

    # concatenation of consecutive one user's replies

    while i < len(json_replies):
        if json_replies[i]["userId"] == curr_user:
            curr_reply += " " + json_replies[i]["text"]
            curr_user = json_replies[i]["userId"]
        else:
            fixed_replies.append(curr_reply)
            corresp_users.append(u2t[curr_user])
            curr_user = json_replies[i]["userId"]
            curr_reply = json_replies[i]["text"]
        i += 1

    fixed_replies.append(curr_reply)
    corresp_users.append(u2t[curr_user])

    return fixed_replies, corresp_users


def embed_all_in_dir(neighbours_count, dir="data/"):
    """
        Turning all replies preceding user's replies into tf-idf-weighted BoW vectors
        and fitting the LSH forest for doing approximate nearest neighbours search afterwards
    :param dir: json data directory
    :return: vectorizer, LSHForest, replies pairs
    """

    all_dialogs = []

    # reading data as JSON

    for f in os.listdir(dir):
        if f.endswith(".json"):
            all_dialogs += json.loads(open(dir + f).read())

    print("a total of", len(all_dialogs), "humane interactions")

    replies_pairs = []

    for d in all_dialogs:
        if d["thread"]:
            replies, users = build_replies_list(d)
            replies_pairs.extend(
                [(replies[i], replies[i + 1]) for i in range(len(replies) - 1) if users[i + 1] == "Human"])

    print("Replies pairs with human the second", len(replies_pairs))

    v = TfidfVectorizer(ngram_range=(1, 3), max_features=70000)
    embedded = v.fit_transform([r[0] for r in replies_pairs])
    lsh = LSHForest(n_neighbors=5, random_state=2)
    lsh.fit(embedded)

    return v, lsh, replies_pairs


def find_closest_responses(text, v, lsh, pairs, neighbours_count, min_cutoff_distance=0.4):
    """
        Finding a reply going in response to the similar one found
        (+ a filtering heuristic)
    :param text: user reply
    :param v: vectorizer
    :param lsh: lsh tree for looking for the similar reply
    :param pairs: pairs of replies for fetching bot's new reply reply
    """
    # distances and neighbours labels
    dist, ns = (lsh.kneighbors(v.transform([text]), neighbours_count))

    # take first element if all distances are too big
    filt = [True] if np.sum(dist < min_cutoff_distance) == 0 else dist < min_cutoff_distance
    ns = ns[filt].flatten()

    res = []

    for i in ns:
        res.append(pairs[i])

    return res