import sys
import pandas as pd
import numpy as np
from itertools import chain, combinations
from collections import defaultdict
import csv


def err_msg(str):
    print(str)
    sys.exit()

# convert numeric feature to categorical data
def get_category_name(num, col_name, max_num, num_of_chunk=5):
    col_name = col_name.replace(',', '')
    lst = [i * round(float(max_num) / num_of_chunk, 2) for i in range(num_of_chunk)]
    lst = list(zip(lst, lst[1:]))

    # generate categorical feature name
    chunk_name = []
    for l in lst:
        chunk_name.append(str(l[0]) + " < " + col_name + " <= " + str(l[1]))
    chunk_name.append(col_name + '>' + str(lst[-1][1]))

    # categorize into different "chunk"
    for i in range(len(lst)):
        if lst[i][0] <= num <= lst[i][1]:
            return chunk_name[i]
    return chunk_name[-1]


# refine age feature: Old, Middle age, Young
def get_age_name(age):
    if age in ['60+']:
        return "Old"
    elif age in ['50 - 59', '40 - 49', '30 - 39']:
        return "Middle age"
    elif age in ['13 - 19', '20 - 29']:
        return "Young"
    return "UK"


# preprocess "DOHMH_HIV_AIDS_Annual_Report.csv" -> "INTEGRATED-DATASET.csv"(max_row = 10000)
def preprocess(selected_num=10000):
    # extract meaningful columns, definitions:
    # HIV diagnosis rate: HIV diagnoses per 100,000 NYC population using annual intercensal population estimates.
    # AIDS diagnosis rate: AIDS diagnoses per 100,000 NYC population using annual intercensal population estimates.
    # HIV-related death rate: Death rate for those assigned an HIV-related cause of death.
    # PLWDHI prevalence: Estimated number of people 13 years of age or older
    # living with diagnosed HIV infection (PLWDHI) per 100 NYC population
    used_col = [
        'Gender',
        'Age',
        'HIV diagnosis rate',
        'AIDS diagnosis rate',
        'HIV-related death rate',
        'PLWDHI prevalence'
        ]
    filename = "DOHMH_HIV_AIDS_Annual_Report.csv"
    df = pd.read_csv(filename,
                     usecols=used_col,
                     header=0,
                     encoding='iso-8859-1')

    # omit meaningless rows
    word_omitted = ['',
                    '0',
                    'All',
                    '99999', 'Other/Unknown',
                    ]
    for word in word_omitted:
        df.replace(word, np.nan, inplace=True)
    df.dropna(subset=used_col, inplace=True)

    # categorization
    col_partitioned = [
        'HIV diagnosis rate',
        'AIDS diagnosis rate',
        'HIV-related death rate',
    ]

    for col in col_partitioned:
        df[col] = df[col].apply(lambda t: get_category_name(t, col, 100.0, 10))
    df["Age"] = df["Age"].apply(lambda t: get_age_name(t))
    df['PLWDHI prevalence'] = df['PLWDHI prevalence'].apply(lambda t: get_category_name(t, 'PLWDHI prevalence', 2.0, 15))

    # randomly sample certain number of rows from entire table without replacement
    total_rows = df.shape[0]
    df = df.sample(frac=selected_num * 1. / total_rows) if total_rows > selected_num else df
    selected_df = df[:selected_num]
    selected_df.to_csv('INTEGRATED-DATASET.csv', header=None, index=False, quoting=csv.QUOTE_NONE, escapechar=' ')


# get all subsets of a given set
def subset(data):
    s = list(data)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


# generate large item set for next iteration using join/union
def apriori_gen(item_set, k):
    res = set()
    for i in item_set:
        for j in item_set:
            union_set = i.union(j)
            if len(union_set) == k:
                res.add(union_set)
    return res


# prune large item set L_{k}, make sure all (k - 1) subsets are included in L_{k-1}
def apriori_prune(item_set, k, item_set_record):
    item_to_remove = set()
    for item in item_set:
        for i in list(combinations(item, k - 1)):
            if not frozenset(i) in (item_set_record[k - 1]):
                item_to_remove.add(item)
                break
    return item_set - item_to_remove


# calculate support of item set
def get_support(item, freq_cnt, total_num):
    return freq_cnt[item] * 1. / total_num


# calculate confidence of item set
def get_confidence(item, LHS, freq_cnt, total_num):
    return get_support(item, freq_cnt, total_num) * 1. / get_support(LHS, freq_cnt, total_num)


# expand large item set for each iteration
def update_item_set(item_set, item_row, freq_cnt, min_support):
    new_item_set = set()
    total_num = len(item_row)
    for item in item_set:
        for row in item_row:
            if item.issubset(row):
                freq_cnt[item] += 1
        if freq_cnt[item] / total_num >= min_support:
            new_item_set.add(item)
    return new_item_set


# extract all rows and items from preprocessed table
def get_item_info(filename="INTEGRATED-DATASET.csv"):
    item_set = set()
    item_row = []
    with open(filename, "r", encoding='utf-8') as f:
        for line in f:
            l = line.strip().split(',')
            item_row.append(frozenset(l)) # make set immutable to be hashable
            for item in l:
                item_set.add(frozenset([item]))
    return item_set, item_row


# generate rules with confidence above min_conf
def get_rule(item_set, freq_cnt, total_num, min_conf):
    for RHS in item_set:
        LHS = item_set - {RHS}
        conf = get_confidence(item_set, LHS, freq_cnt, total_num)
        if conf >= min_conf:
            return (LHS, {RHS}, conf, get_support(item_set, freq_cnt, total_num), get_support(frozenset([RHS]), freq_cnt, total_num))
    return None


# print large item set and rules in the manner specified in handout
def print_res(global_items, global_rules, min_sup, min_conf, verbose=False):
    print("==Frequent itemsets (min_sup={}%)".format(int(min_sup * 100)))
    for item in global_items:
        print("[" + ','.join(item[0]) + "], {}%".format(int(item[1] * 100)))
    print("==High-confidence association rules (min_conf={}%)".format(int(min_conf * 100)))
    for rule in global_rules:
        if verbose:
            print("[" + ','.join(rule[0]) + "] => [" + ','.join(rule[1]) + "] (Conf: {}%, Supp: {}%, Interestingness: {}%)"
                  .format(int(rule[2] * 100), int(rule[3] * 100), int((rule[2] - rule[4]) * 100)))
        else:
            print("[" + ','.join(rule[0]) + "] => [" + ','.join(rule[1]) + "] (Conf: {}%, Supp: {}%)"
                  .format(int(rule[2] * 100), int(rule[3] * 100)))


def apriori():
    if len(sys.argv) < 4:
        err_msg("Usage: <filename> <min_sup> <min_conf>")

    filename = sys.argv[1]
    min_sup = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    item_set, item_row = get_item_info(filename)
    total_num = len(item_row)
    freq_cnt = defaultdict(int)

    item_set_record = [{}, ]
    freq_item_set = update_item_set(item_set, item_row, freq_cnt, min_sup)
    item_set_record.append(freq_item_set)
    k = 2
    while len(freq_item_set) > 0:
        freq_item_set = apriori_gen(freq_item_set, k)
        freq_item_set = apriori_prune(freq_item_set, k, item_set_record)
        freq_item_set = update_item_set(freq_item_set, item_row, freq_cnt, min_sup)
        if len(freq_item_set) == 0:
            break
        item_set_record.append(freq_item_set)
        k += 1

    global_items = []
    global_rules = []
    for i in range(1, k):
        for item in item_set_record[i]:
            if len(item) >= 2:
                rule = get_rule(item, freq_cnt, total_num, min_conf)
                if rule is not None:
                    global_rules.append(rule)
            global_items.append((item, get_support(item, freq_cnt, total_num)))
    global_items = sorted(global_items, key=lambda l: l[1], reverse=True)
    global_rules = sorted(global_rules, key=lambda t: t[2], reverse=True)
    print_res(global_items, global_rules, min_sup, min_conf, verbose=False)


if __name__ == '__main__':
    # preprocess()
    apriori()
