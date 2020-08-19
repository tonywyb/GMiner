# GMiner
A Rule&amp;Relation Extractor Based on Google Custom Search

* [Project 1: Rocchio Algorithm with TF-IDF Embedding](proj1/README.md): Implement an information retrieval system that exploits user-provided feedback to improve the search results returned by Google. The program basically performs following steps:

1. Receive as input a user query, which is simply a list of words, and a value—between 0 and 1—for the target “precision@10”.

2. Retrieve the top-10 results for the query from Google, using the Google Custom Search API.

3. Present these results including the title, URL, and description returned by Google to the user, so that the user can mark all the webpages that are relevant to the intended meaning of the query among the top-10 results.

4. If the precision@10 of the results from Step 2 for the relevance judgments of Step 3 is greater than or equal to the target value, then stop. If the precision@10 of the results is zero, then also stop. Otherwise, use the pages marked as relevant to automatically derive new words that are likely to identify more relevant pages. The program introduces at most 2 new words during each round. 

5. Modify the current user query by adding to it the newly derived words and ordering all words in the best possible order, as determined in Step 4, and go to Step 2.

* [Project 2: Iterative Set Expansion with Standford CoreNLP Pipelines](proj2/README.md): Built a "structured" information extractor for information that is embedded in natural language text on the web. The program basically performs following steps:

1. Initialize X, the set of extracted tuples, as the empty set.

2. Query Google Custom Search Engine to obtain the URLs for the top-10 webpages for query q.

3. For each URL from the previous step that is not processed before:

  a. Retrieve the corresponding webpage; if you cannot retrieve the webpage (e.g., because of a timeout), just skip it and move on, even if this involves processing fewer than 10 webpages in this iteration.
  
  b. Extract the actual plain text from the webpage using Apache Tika or your preferred toolkit (see above).
  
  c. If the resulting plain text is longer than 20,000 characters, truncate the text to its first 20,000 characters (for efficiency) and discard the rest.
  
  d. Annotate the text with the Stanford CoreNLP software suite and, in particular, with the Stanford KBP Annotator, to extract all instances of the relation specified by input parameter r.
  
  e. Identify the tuples that have an associated extraction confidence of at least t and add them to set X.

4. Remove exact duplicates from set X: if X contains tuples that are identical to each other, keep only the copy that has the highest extraction confidence and remove from X the duplicate copies.

5. If X contains at least k tuples, return the top-k such tuples sorted in decreasing order by extraction confidence, together with the extraction confidence of each tuple, and stop. 

6. Otherwise, select from X a tuple y such that (1) y has not been used for querying yet and (2) y has an extraction confidence that is highest among the tuples in X that have not yet been used for querying. Create a query q from tuple y by just concatenating the attribute values together, and go to Step 2. If no such y tuple exists, then stop. 


