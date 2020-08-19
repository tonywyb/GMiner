# 6111-proj3 README

## Files
- association_rule_mining.py
- README.pdf
- example-run.txt
- INTEGRATED-DATASET file

## How to run the program
Prerequisite: install `python >= 3.7`.

To run the program, type in 

 ``` ./run.sh <filename> <min_supp> <min_conf> ``` 

`<min_supp>` is the minimum support threshold, `<min_conf>` is the minimum confidence threshold to acheive.

## Data set choice
Use [DOHMH HIV/AIDS Annual Report](https://data.cityofnewyork.us/Health/DOHMH-HIV-AIDS-Annual-Report/fju2-rdad) as our data set, which reports the diagnosis of HIV for people ages 13 and older borough-wide and citywide in New York.

### Preprocess and Choice Justification
Before running program on the data, process it by removing empty field or fields with 0, unspecified, All etc. for the reason that they have conflict with other attributes of our choice or do not play an important role in the data. Therefore, you can omit the records containing ['', '0', 'All', '99999', 'Other/Unknown'].

Choose the column so that the values in that column won't all yield to a specific one and the values are potentially helpful in association rules mining (for example, the HIV-related death rate could be related to the actual diagnosis rate). The final columns inclue **Gender**, **Age**, **HIV diagnosis rate**, **AIDS diagnosis rate**, **HIV-related death rate**, and **PLWDHI prevalence**. 

For columns with numeric values, consider splitting the values in different ranges. For column **age** , 13 to 29 years old is classified as young, 30 to 59 years old is classified as middle age and greater than 60 years old classified as old. For columns **HIV diagnosis rate**, **AIDS diagnosis rate**, and **HIV-related death rate**, the program splits the values from 0 to 100 into 10 separate ranges with equal length. For column **PLWDHI prevalence** , the program splits the values from 0 to 2.0 into 15 separate ranges with equal length.

In addition, shuffle the data set by rows to ensure that the potential class ordering will not affect our data mining process. 


## Internal Design Structure
`get_category_name`: This method is used to split the data values in one column to different ranges.

`get_age_name`: This method is used specifically to split the data values in **age** column.

`preprocess`: Use this method to process the original data set and export it into the INTEGRATED-DATASET csv file.

`subset`: This method is used to find all subsets of an item set.

`apriori_gen`: This method is used to generate large item set for next iteration using join/union.

`apriori_prune`: This method is used after apriori_gen to prune large item set L_{k}, make sure all (k - 1) subsets are included in L_{k-1}.

`get_support`: This method is used to calculate support of item set.
 
`get_confidence`: This method is used to calculate confidence of item set.
 
`update_item_set`: This method is used to expand large item set for each iteration.
 
`get_item_info`: This method is used to extract all rows and items from preprocessed table.
 
`get_rule`: This method is used to generate rules with confidence above min_conf.
 
`print_res`: This method is used to print large item set and rules in the manner specified in handout.

For candicate generation in our apriori algorithm, the program uses the way of union different itemsets to add new items rather than adding them one by one.

### Command line specification
The minimum support rate is 0.2. Is is observed that this threshold can prevent some unhelpful attribute values in a maximum way, like those with ages over 60 years old. The minimum confidence rate is 0.6 because it won't include too many high frequency itemsets and still able to extract more high-confidence rules.

## Results
The association rule extracted are:
- `[0.0  <  PLWDHI  prevalence  <=  0.13] => [0.0  <  AIDS  diagnosis  rate  <=  10.0]`: PLWDHI prevalence is the estimated number of people 13 years of age or older living with diagnosed HIV infection (PLWDHI) per 100 NYC population. This rule shows that a low number PLWDHI prevalence indicates a low AIDS diagnosis rate. Therefore, the estimate of DOHMH is shown reliable in respect of AIDS diagnosis. 
- `[Female, 0.0  <  HIV  diagnosis  rate  <=  10.0] => [0.0  <  AIDS  diagnosis  rate  <=  10.0]`: This rule shows that the female in places with low HIV diagnosis rate indicates a low AIDS diagnosis. The rule `[0.0  <  HIV  diagnosis  rate  <=  10.0] => [0.0  <  AIDS  diagnosis  rate  <=  10.0]`.
- `[0.0  <  HIV  diagnosis  rate  <=  10.0] => [Female]`, this rule indicates that the low HIV diagnosis rate is more related to female instead of male, considering the male and female support rate are roughly the same. Disparate HIV behavior with respect to the two genders can be observed.
- `[Young] => [0.0  <  AIDS  diagnosis  rate  <=  10.0]`, this rule indicates that the age of young are less likely to be diagnosed AIDS.

The program has extracted a few association rules where the items in the rules are not strongly related, It is found that the interestingness of those rules are close to 0, which means the LHS and RHS of the itemset are independent. These rules are
```
[Male] => [0.0  <  HIV-related  death  rate  <=  10.0] (Conf: 67%, Supp: 33%, Interestingness: 0%)
[Middle  age] => [0.0  <  HIV-related  death  rate  <=  10.0] (Conf: 67%, Supp: 33%, Interestingness: 0%)
[Female] => [0.0  <  HIV-related  death  rate  <=  10.0] (Conf: 67%, Supp: 33%, Interestingness: 0%)
```

## Other Details
- Handle the trivial association rules by using a set to store the frequent itemsets to ensure that we only put unique items in the itemset. Therefore, the program can generate association rules with exactly one item on the right side and with at least one item on the left side, where the right-side item does not appear on the left side.
- To make a set hashable and stored in the dictionary, the program defines the item set as a frozenset which is immutable.
