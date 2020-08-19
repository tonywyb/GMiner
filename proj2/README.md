#6111-proj2 README

## Files
- info_extraction_system.py
- README.pdf
- Transcript.jpg

## How to run the program
Prerequisite: install `python == 3.7.6`, `google-api-python-client`[See more config details here](https://github.com/googleapis/google-api-python-client), `Java 13`[link](https://download.java.net), `stanfordnlp`[link](https://stanfordnlp.github.io/CoreNLP/), `StanfordNLP Python package`[link](https://stanfordnlp.github.io/stanfordnlp/installation_usage.html#installation).

To run the program, type in 

 ``` python info_extraction_system.py <google api key> <google engine id> <r> <t> <q> <k> ```

 \<r\> indicates relation to extract, \<t\> indicates extraction confidence threshold, \<q\> indicates query string, \<k\> indicates number of extracted tuples requested. 

## Internal Design Structure
For the external libraries, `googleapiclient` will be used to search for user query with google search engine, `requests` is used to form http request and retrieve response, `beautifulsoup (bs4)` will be used to parse html content from the http response, `stanfordnlp` will be used to annotate text and extract relations, and `datetime` will be used to print current timestamp.

The structure of the code can be divided into several parts including prompting input, searching for results, extracting and evaluating relations. The main high-level components are described as below.

`get_input`: Prompt user input, parse input parameters including relation to extract, extraction confidence threshold, query string and number of requested tuples. Error checking involved.

`search`: Build a service object for interacting with the API and provide text results for extraction. Skip already-seen urls and webpages can't be retireved because of timeout,  even if this involves processing fewer than 10 webpages in this iteration. 

`extract`: Implement two pipelines for iterative set expansion. Annotate the text with the Stanford CoreNLP software suite and extract relations according to user provided r value, evaluate tuples with respect to their confidence.

Other modules to support main components stated above:

`has_required_ner`: Check if a sentence contains both required named entities for the relation of interest. Perform as a sentence filter before running the second pipeline including the expensive `depparse` annotator. 

`preprocess_text`: Use beautifulsoup to parse html content from the http response. Preprocess the sentences including stripping strings of leading and trailing newlines, filter empty lines, skip contents in blacklist tags.


## Extraction process
(a) To extract relations and form new query, `search` method is designed to get urls from the top-10 search results, then use `requests` to send http request to those URL and receive response text. If the request times out or URL already seen, it will not be processed. 

(b) Beautiful soup is then used to retrieve html from the response text. 

(c) We set a cut-off length of 20000 characters so the html text will not overwhelm stanfordnlp server.

(d) Then the result web page texts are transferred to `extract` method, where we created  two pipelines with different annotators. For the pipeline with `ner` we check if the sentences fed into the pipeline has required named entity, if not we will skip this sentence, otherwise we hand the sentence over to the second pipeline with `kbp` and extract a tuple consisting of confidence, subject, and object of each kbptriple. 

(e) For any tuple with confidence at least the confidence threshold, we check if it's already seen before and decide to update its confidence or add it into the X set or do nothing and continue.

After extraction we use the tuples as instructed, checking if top-k is satisfied, if yes then return the answer, otherwise find the extracted relation tuple that will be used as query in next iteration. Stop if there is no extracted relation tuple satisfy the requirement stated above. 


## Google Search Engine Info
Google Custom Search Engine JSON API Key: XXXXXX

Search Engine ID: XXXXX


## Other Details

1. html text parsing and preprocessing: 

We use beautifulsoup to perform html text extraction. BeautifulSoup provides a simple way to find text content (i.e. non-HTML) from the HTML:`soup.find_all(text=True)`. We also use a blacklist to avoid text from any items from the blacklit tags. To avoid large empty lines fed into stanfordnlp annotators, we strips text strings of leading and trailing newlines and filter empty lines at the end of text preprocessing. 

Reference: https://matix.io/extract-text-from-webpage-using-beautifulsoup-and-python/

2. sentence parsing and truncating: To avoid error in kbp pipeline,  we limits the number of tokens able to be passed to the second pipeline. We specific it to 40 as default value. 

Reference: https://piazza.com/class/k5ifupgn538469?cid=114



