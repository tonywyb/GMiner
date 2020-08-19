# 6111-proj1 README

## Files
- info_retrieval_system.py
- stop_words.txt
- README.pdf
- Transcript.jpg

## How to run the program
Prerequisite: install `python == 3.6`and `google-api-python-client`.[See more config details here](https://github.com/googleapis/google-api-python-client)

To run the program, type in 

 ``` python info_retrieval_system.py <google api key> <google engine id> <precision> <query> ```

 After the search result documents are shown, select the relevant documents by inputting Y|y for yes, N|n for no. Once all the documents are evaluated, the new query with words derived will be printed out as well as the search results including newly derived words as keyword. Follow the instructions in command line until the program terminates.

## Internal Design Structure 
The structure of the code can be divided into several parts including prompting input, searching for results, generating documents' representative values, and deriving new query words.

`get_input`: Prompt user query words and precision value, error checking involved.

`search`: Build a service object for interacting with the API and provide results to the user. 

`generate_doc_vec`: Collect result documents' term frequency, document frequency and inverse document frequency, and calculate the weight of each document's(including query) terms. 

`Rocchio()`: Implements the Rocchio algorithm stated in the lecture slides 2. It will use the weights returned by `generate_doc_vec()` to calculate scores for each term and derive a new list of query terms to use.

## Query modification method
The main methods to modify query are `generate_doc_vec()` and `Rocchio()`. 

In `generate_doc_vec()`, the original document results passed in will be divided into words to get term frequency, total term count, and inverse document frequency by iterating through each word in the documents. Then, the weight variable will store the score of each term, if the term frequency of one word is 0, then the weight will also be 0, otherwise, the weight for that word will be calculated based on the formula: $(1 + log_{10}(tf_{t,d}))*log_{10}(N/df_t)$ where tf is the term frequency and df is the document frequency. 

In `Rocchio()`, calculate the term weight for each word according to the Rocchio formula: $ q_{new} = \alpha * q_{old} + \frac{\beta * d_j}{R} - \frac{\gamma * d_j}{NR}$. Alpha, beta and gamma are specified by default setting from reading materials provided in project instructions (alpha: 1.0, beta: 0.75, gamma: 0.15) [(Relevance feedback and query
expansion)](https://nlp.stanford.edu/IR-book/pdf/09expand.pdf). 

**How to select the new keywords to add in each round:**

After getting the score (weight) of each term, the program picks K words that is not in query with highest scores to be our new query words where K can be 1 or 2. Then it puts a constraint on the number of new words added into query set. If the second word's score is 20% lower than the first one, it only adds one key word to query set. Otherwise both top 2 terms will be included in next round search.

**How to determine the query word order in each round:**

Order the newly added query word by its score computed by `generate_doc_vec()`. The program remains the original order of initial query words. New query word extracted in current iteration will always come after those extracted in previous iterations. In this way, more and more query words padded and appended into the end of query words set.

## Google Search Engine Info
Google Custom Search Engine JSON API Key: XXXXXX

Search Engine ID: XXXXXX


## Other Details


- The program puts more weight on title words compared to description words appeared in snippets. Each time tf[d][t] values are calculated for certain document d and term t. If term t appears in title, corresponding tf values will be increased by 1.3 in our default setting. 
- The program puts preference in capitalized words which is likely to be named entities and provide critical information for our search system. 
- Stop words extraction is performed before calculating term weights. Perform data cleaning to wipe out strange characters using a regular expression filter.