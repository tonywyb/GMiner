# GMiner
A Rule&amp;Relation Extractor Based on Google Custom Search

* [Project 1: Rocchio Algorithm with TF-IDF](proj1/README.md): Implement an information retrieval system that exploits user-provided feedback to improve the search results returned by Google.

1. Receive as input a user query, which is simply a list of words, and a value—between 0 and 1—for the target “precision@10”.

2. Retrieve the top-10 results for the query from Google, using the Google Custom Search API.

3. Present these results including the title, URL, and description returned by Google to the user, so that the user can mark all the webpages that are relevant to the intended meaning of the query among the top-10 results.

4. If the precision@10 of the results from Step 2 for the relevance judgments of Step 3 is greater than or equal to the target value, then stop. If the precision@10 of the results is zero, then also stop. Otherwise, use the pages marked as relevant to automatically derive new words that are likely to identify more relevant pages. The program introduces at most 2 new words during each round. 

5. Modify the current user query by adding to it the newly derived words and ordering all words in the best possible order, as determined in Step 4, and go to Step 2.

