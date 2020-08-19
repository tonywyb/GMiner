import sys
import json
from googleapiclient.discovery import build
from math import log
import re
from collections import defaultdict


def get_stop_words():
    with open("stop_words.txt", "r") as f:
        words = f.readlines()
    return [w[:-1] for w in words]


def err_msg(str):
    print(str)
    sys.exit()


def parse_input():
    # prompt user input for a list of words and precision value
    if len(sys.argv) < 5:
        err_msg("Usage: <google api key> <google engine id> <precision> <query>")

    words = sys.argv[4:]
    precision = sys.argv[3]
    my_search_engine_id = sys.argv[2]
    my_api_key = sys.argv[1]

    try:
        float(precision)
    except ValueError:
        err_msg("Incorrect prompt, Usage: <google api key> <google engine id> <precision> <query>")

    return words, precision, my_search_engine_id, my_api_key


def search(query, precision, my_search_engine_id, my_api_key):
    # Build a service object for interacting with the API
    service = build("customsearch", "v1",
                    developerKey=my_api_key)

    res = service.cse().list(
        q=query,
        cx=my_search_engine_id,
        num=10,
    ).execute()

    websites_info = []
    site_id = 0
    for item in res["items"]:
        if "htmlTitle" in item and item["title"] != "":
            info = {
                "id": site_id,
                "title": item["title"],
                "url": item["formattedUrl"],
                "description": item["snippet"].rstrip()
            }
            websites_info.append(info)
            site_id += 1

    return websites_info


def generate_doc_vec(docs, query, stop_words, param, N=10):
    def preprocess(term):
        return re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", term)

    raw_title_lis = [doc['title'] for doc in docs]
    raw_title_lis = [d.strip().split(' ') for d in raw_title_lis if d.strip()]
    raw_doc_lis = [doc['description'] + doc['title']  for doc in docs]
    raw_doc_lis = [d.strip().split(' ') for d in raw_doc_lis if d.strip()]
    
    doc_lis = []
    for doc in raw_doc_lis:
        tmp = [preprocess(w) for w in doc if preprocess(w.lower()) not in stop_words 
        and preprocess(w.lower()) != "" 
        and not preprocess(w.lower()).isnumeric()]
        doc_lis.append(tmp)
    title_lis = []
    for title in raw_title_lis:
        tmp = [preprocess(w) for w in title if preprocess(w.lower()) not in stop_words and preprocess(w.lower()) != "" and not preprocess(w.lower()).isnumeric()]
        title_lis += tmp

    doc_lis.append(query)
    assert len(doc_lis) == 11, "should have ten sentences + one query each round"

    tf = defaultdict(lambda: defaultdict(int))
    df_lis = defaultdict(list)
    idf = defaultdict(float)
    weight = defaultdict(lambda: defaultdict(float))

    terms = []
    for d_idx in range(len(doc_lis)):
        for term in doc_lis[d_idx]:
            terms.append(term)
            if term in title_lis:
                tf[d_idx][term] += param['title']
            if all(t.isupper() for t in term):
                tf[d_idx][term] += param['all_cap']
            tf[d_idx][term] += 1
            df_lis[term].append(d_idx)

    for (k, v) in df_lis.items():
        idf[k] = log(N * 1.0 / len(set(v)))

    for t in terms:
        for d_idx in range(len(doc_lis)):
            if tf[d_idx][t] == 0:
                weight[d_idx][t] = 0.
            else:
                weight[d_idx][t] = (1 + log(tf[d_idx][t])) * idf[t]

    return weight, terms


# strategy for adding new words to query
# if the score of second term is 20% lower than the first term, we only add first term into query
def score_metric(hi, lo, threshold=0.2):
    if (hi - lo) * 1.0 / lo > threshold:
        return True
    else:
        return False

def Rocchio(weight, relevant_lis, params, terms, query_terms, topK=2, flexible=True, reorder=False, N=10):
    R = len(relevant_lis)
    NR = N - R
    q_vec = weight[N]
    r_vecs = [weight[i] for i in relevant_lis]
    nr_vecs = [weight[i] for i in range(N) if i not in relevant_lis]
    for t in terms:
        q_vec[t] = params['alpha'] * q_vec[t]
        for r in r_vecs:
            q_vec[t] += (params['beta'] * r[t]) / R
        for nr in nr_vecs:
            q_vec[t] -= (params['gamma'] * nr[t]) / NR
    term_scores = sorted(list(q_vec.items()), key=lambda t: t[1], reverse=True)
    new_term_score = []
    cnt = 0
    for (t, s) in term_scores:
        if t not in query_terms:
            if cnt < topK:
                new_term_score.append((t, s))
                cnt += 1
            else:
                break
    if topK > 1 and flexible:
        if score_metric(new_term_score[-1][1], new_term_score[-2][1], threshold=params['threshold']):
            new_term_score.pop(-1)
    new_term_score += [t for t in term_scores if t[0] in query_terms]
    res = [r for (r, _) in new_term_score]
    if reorder:
        new_term_score = sorted(new_term_score, key=lambda t: t[1], reverse=True)
        res = [r for (r, _) in new_term_score]
    return res


def main():
    query, precision, my_search_engine_id, my_api_key = parse_input()
    stop_words = get_stop_words()
    results = search(" ".join(query), precision, my_search_engine_id, my_api_key)
    prompt(query, precision, my_search_engine_id, my_api_key)
    if len(results) < 10:
        early_stop_print(results)
    while True:
        user_precision = []
        for news_id in range(len(results)):
            print("Result: " + str(news_id))
            res = round_print(results[news_id]['url'], results[news_id]['title'], results[news_id]['description'])
            if res:
                user_precision.append(news_id)
        
        cur_precision = len(user_precision) / (len(results) * 1.0)
        if cur_precision >= float(precision):
            print("FEEDBACK SUMMARY\n")
            print("Query: " + " ".join(query) + "\n")
            print("Current precision %.1f \n" % cur_precision )
            print("Target precision " + precision + " achieved, done")
            break
        elif cur_precision == 0.:
            print("FEEDBACK SUMMARY\n")
            print("Query: " + " ".join(query) + "\n")
            print("Current precision %.1f" % (cur_precision))
            break
        weight, terms = generate_doc_vec(results, query, stop_words, params, N=len(results))
        user_precision = [int(u) for u in user_precision]
        query = Rocchio(weight, user_precision, params, terms, query, topK=2, reorder=False, N=len(results))

        print("FEEDBACK SUMMARY\n")
        print("New precision: %.1f\n" % cur_precision)
        print("Query       = {}".format(" ".join(query)))
        print("Still below the desired precision: {}".format(precision))

        results = search(" ".join(query), precision, my_search_engine_id, my_api_key)
        if len(results) < 10:
            early_stop_print(results)

        
def prompt(query, precision, my_search_engine_id, my_api_key):
    print("Parameters:")
    print("Client key  = {}".format(my_api_key))
    print("Engine key  = {}".format(my_search_engine_id))
    print("Query       = {}".format(query))
    print("Precision   = {}".format(precision))
    print("Google Search Results:")
    print("=" * 30)


def early_stop_print(results):
    for r in results:
        print("id: %d, title: %s, url: %s\n" % (r["id"], r["title"], r["url"]))
        print("description: %s\n" % (r["description"]))
        print("=================================\n")
    err_msg("Precision fulfilled.")


def round_print(url, title, summary):
    res = {
        "URL": url,
        "Title": title,
        "Summary": summary
    }
    print(json.dumps(res, indent=2))
    while True:
        response = input("Relevant (Y/N)?")
        if response.lower() == "y":
            return True
        elif response.lower() == "n":
            return False
        else:
            print("Please type in Y|y for yes, N|n for no")


if __name__ == '__main__':
    params = {
        "alpha": 1.0,
        "beta": 0.75,
        "gamma": 0.15,
        "threshold": 0.2,
        "title": 0.3,
        "all_cap": 0.2
    }
    main()


