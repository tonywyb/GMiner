import sys
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import requests
from stanfordnlp.server import CoreNLPClient
from stanfordnlp.server import to_text
import datetime

# 4 relations we only care about
relations = ["", "per:schools_attended", "per:employee_or_member_of",
             "per:cities_of_residence", "org:top_members_employees"]
# query set storing all query we have used
query_set = set()
# url set storing all urls we have requested
url_set = set()


def err_msg(str):
    print(str)
    sys.exit()


def get_input():
    # prompt user input for google search api key, engine id, relation, condifence threshold, query and number of tuples
    if len(sys.argv) < 6:
        err_msg("Usage: <google api key> <google engine id> <relation> <confidence> <query> <number of tuples>")

    # parse and data type cast
    my_api_key = sys.argv[1]
    my_search_engine_id = sys.argv[2]
    r = int(sys.argv[3])
    t = float(sys.argv[4])
    k = int(sys.argv[-1])
    query = sys.argv[5:-1][0]

    # validate input params
    try:
        if r not in [1, 2, 3, 4]:
            err_msg("Invalid relation input, please enter an integer between 1 and 4")
        if t < 0 or t > 1:
            err_msg("Invalid extraction confidence threshold, please enter a real number between 0 and 1")
        if k <= 0:
            err_msg("Invalid number of tuples requested in the output, please enter an integer greater than 0")
        if not query:
            err_msg("Invalid seed query, please enter a list of words")
    except ValueError:
        err_msg("Incorrect prompt,"
                " Usage: <google api key> <google engine id> <relation> <confidence> <query> <number of tuples>")

    return my_api_key, my_search_engine_id, r, t, query, k


def preprocess_text(response, cutoff_length):
    # find text content (i.e. non-HTML) from the HTML using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.find_all(text=True)

    result = ''

    #  a few items in the blacklist that we likely do not want
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head',
        'input',
        'script',
        'style'
    ]

    for t in text:
        if t.parent.name in blacklist or not t:
            continue
        result += '{} '.format(t)

    # strips a string of leading and trailing newlines, filter empty lines
    result_lis = result.strip('\n').split('\n')
    result_lis = [r.strip() for r in result_lis if r.strip()]
    result = '\n'.join(result_lis)
    if len(result) > cutoff_length:
        print(' ' * 6 + 'Truncating webpage text from size (num characters) {} to  ...'
              .format(len(result), cutoff_length))
        result = result[: cutoff_length]
    return result


def search(query, my_search_engine_id, my_api_key, cutoff_length):
    # Build a service object for interacting with the API
    service = build("customsearch", "v1",
                    developerKey=my_api_key)

    # retrieve top 10 pages using google custom search
    res = service.cse().list(
        q=query,
        cx=my_search_engine_id,
        num=10,
    ).execute()
    
    text = []
    URLs = []
    for item in res["items"]:
        URL = item["link"]
        try:
            response = requests.get(url=URL, timeout=200)
        except Exception as e:
            print(e)
        if response.status_code != 200:
            url_set.add(URL)
            text.append("Error")
        elif URL in url_set:
            text.append("Repeated URL")
        else:
            url_set.add(URL)
            output = preprocess_text(response, cutoff_length)
            text.append(output)
        URLs.append(URL)

    return text, URLs


def has_required_ner(sentence_ner, relation):
    # extract named entities contained by the sentence
    ner_set = set()
    for m in sentence_ner.mentions:
        ner_set.add(m.ner)

    # check if the sentence contains both required named entities for the relation of interest
    if relation in [relations[1], relations[2], relations[4]]:
        return "ORGANIZATION" in ner_set and "PERSON" in ner_set
    elif relation == relations[3]:
        ner_lis = ["LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]
        return "PERSON" in ner_set and any([n in ner_set for n in ner_lis])


def extract(pipeline_ner, pipeline_kbp, text, relation, X, t, sentence_cutoff=40):
    print(" " * 6 + "Annotating the webpage using [tokenize, ssplit, pos, lemma, ner] annotators ...")
    ann_ner = pipeline_ner.annotate(text)
    print("Extracted", len(ann_ner.sentence),
          "sentences. Processing each sentence one by one to check for presence of right pair of named entity types; "
          "if so, will run the second pipeline ...")
    relation_count = len(X)
    kbp_count = 0
    for ith, sentence_ner in enumerate(ann_ner.sentence):
        if (ith + 1) % 5 == 0 or (ith + 1) == len(ann_ner.sentence):
            print(" " * 6 + "Processed {} / {} sentences".format(ith + 1, len(ann_ner.sentence)))
        if not has_required_ner(sentence_ner, relation):
            # skip sentences which don't contain both required named entities for the relation of interest
            continue

        # limit the number of tokens able to be passed to the second pipeline
        parsed_sentence = to_text(sentence_ner)
        parsed_sentence = parsed_sentence.strip().split(' ')[:sentence_cutoff]
        parsed_sentence = " ".join(parsed_sentence)
        ann = pipeline_kbp.annotate(parsed_sentence)

        for sentence in ann.sentence:
            kbp_count += 1
            for kbp_triple in sentence.kbpTriple:
                # skip triples without relation of interest
                if kbp_triple.relation != relation:
                    continue
                print(" " * 12 + "=== Extracted Relation ===")
                print(" " * 12 + "Sentence: " + to_text(sentence))
                print(" " * 12 + "Confidence: " + str(kbp_triple.confidence) + "\t Subject: "
                      + kbp_triple.subject + "\t Object: " + kbp_triple.object)
                extracted_tuple, confidence = (kbp_triple.subject, kbp_triple.object), kbp_triple.confidence
                if confidence >= t:
                    if extracted_tuple not in X:
                        X[extracted_tuple] = confidence
                        print(" " * 12 + "Adding to set of extracted relations")
                    else:
                        if X[extracted_tuple] >= confidence:
                            print(" " * 12 + "The same relation is already present with higher (or equal) confidence."
                                             " Ignoring this.")
                        else:
                            X[extracted_tuple] = confidence
                            print(" " * 12 + "The same relation is already present but with a lower confidence."
                                             " Just updating the confident value.")
                else:
                    print(" " * 12 + "Confidence is lower than threshold confidence. Ignoring this.")

    # number of extracted relation = increased size of X
    relation_count = len(X) - relation_count

    print(" " * 6 + "Extracted kbp annotations for", kbp_count, "out of total", len(ann_ner.sentence), "sentences")
    print(" " * 6 + "Relations extracted from this website: {}  (Overall: {})".format(relation_count, len(X)))


def main():
    iteration = 0
    my_api_key, my_search_engine_id, r, t, query, k = get_input()
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("run {} {} ".format(my_api_key, my_search_engine_id) + ' '.join(sys.argv[3:]))
    print("_______")
    print("Parameters:")
    print("Client key      = " + my_api_key)
    print("Engine key      = " + my_search_engine_id)
    print("Relation        = " + relations[r])
    print("Threshold       = " + str(t))
    print("Query           = " + query)
    print("# of Tuples     = " + str(k))
    print("Loading necessary libraries; This should take a minute or so ...")

    # dict mapping extracted tuples to its confidence
    X = dict()

    with CoreNLPClient(annotators=['tokenize','ssplit','pos','lemma','ner'], timeout=30000, memory='4G', endpoint="http://localhost:9000") as pipeline_ner:
        with CoreNLPClient(annotators=['tokenize','ssplit','pos','lemma','ner', 'depparse','coref', 'kbp'], timeout=30000, memory='4G', endpoint="http://localhost:9001") as pipeline_kbp:
            while iteration < 10:
                print("=========== Iteration: {} - Query: {} ===========".format(iteration, query))
                # retrieve web page html
                results, URLs = search(query, my_search_engine_id, my_api_key, 20000)
                # extract according to relations
                for i in range(len(results)):
                    print("URL (" + str(i + 1) + "/ " + str(len(results)) + "): " + URLs[i])
                    print(" " * 6 + "Fetching text from url ...")

                    if results[i] == "Error!":
                        print(" " * 6 + "Unable to fetch URL. Continuing.")
                        continue
                    if results[i] == "Repeated URL":
                        print(" " * 6 + "Skip already-seen URL. Continuing.")
                        continue
                    print(" " * 6 + "Webpage length (num characters):", len(results[i]))
                    extract(pipeline_ner, pipeline_kbp, results[i], relations[r], X, t)
                
                # sort extracted triples by its confidence in descending order, get top k tuples
                tuple_lis = list(X.items())
                top_k = sorted(tuple_lis, key=lambda t: t[1], reverse=True)

                stop = True
                if len(X) < k:
                    # select new query if there is insufficient number of extracted triples
                    for y in top_k:
                        # create new query q from tuple y by concatenating the attribute values together
                        q = y[0][0] + " " + y[0][1]
                        if q not in query_set:
                            query_set.add(q)
                            query = q
                            stop = False
                            break

                if stop:
                    print("================== ALL RELATIONS ({}) =================".format(len(X)))
                    for (relation_tuple, confidence) in top_k:
                        print("Confidence: {:.6f}\t| Subject: {:40}\t| Object: {}"
                              .format(confidence, relation_tuple[0], relation_tuple[1]))
                    return
                
                iteration += 1


if __name__ == '__main__':
    main()

