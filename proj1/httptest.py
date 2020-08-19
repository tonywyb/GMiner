import requests 

# api-endpoint 
URL = "https://www.gatesnotes.com/"
# defining a params dict for the parameters to be sent to the API 
PARAMS = {} 

# sending get request and saving the response as response object 
r = requests.get(url = URL, params = PARAMS) 
print(r.text[:2000]) 