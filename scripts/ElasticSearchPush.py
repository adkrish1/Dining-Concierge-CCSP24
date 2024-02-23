import json
from decimal import *
import time


cuisines = ['chinese', 'italian', 'indian']
idSet = set()
opstring = ""

def espush(cuisine):
    
    global opstring
    filename = cuisine + '.json'
    with open(filename, 'r') as f:
        data = json.load(f)

    for key, val in data.items():
        if 'businesses' not in val: continue
        businesses = val["businesses"]
        for business in businesses:
            id = business['id']
            if id not in idSet:
                info = {
                    'id': id,
                    'cuisine': cuisine
                }
                header = {"index":{"_index": "restaurants", "_id":id}}
                opstring += json.dumps(header) + '\n' + json.dumps(info) + '\n'

def main():  
    for cuisine in cuisines:    
        espush(cuisine)
        time.sleep(2)
    file_name = 'data_es.json'
    with open(file_name, 'w') as openfile:
        openfile.write(opstring)

if __name__ == '__main__':
    main()