import requests
import json
import time

API_KEY = ""
cuisines = ['chinese', 'italian', 'indian']
    

def yelprequest(apikey, term, location = "Manhattan", limit = 50):
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': 'Bearer %s' % apikey}
 
    offset = 50
    params = {'term':term,'location': location, 'limit': limit, 'offset': offset}
    req = requests.get(url, params = params, headers = headers)
    json_map = req.json()

    file_name = term + '.json'
    with open(file_name, 'w') as openfile:
        json.dump(json_map, openfile, indent = 4)
    

def main():      
    for cuisine in cuisines:
        yelprequest(API_KEY, cuisine)
        time.sleep(5)


if __name__ == '__main__':
    main()