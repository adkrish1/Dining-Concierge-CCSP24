import json
import boto3
import datetime
from decimal import *
import time


cuisines = ['chinese', 'italian', 'indian']
API_KEY = ""
headers = {'Authorization': 'Bearer %s' % API_KEY}
root = 'https://api.yelp.com/v3/businesses/'
idSet = set()
    
def pushToDb(cuisine):
    
    filename = cuisine + '.json'
    with open(filename, 'r') as f:
        data = json.load(f)

    for key, val in data.items():
        if 'businesses' not in val: continue

        businesses = val["businesses"]
        for rest in businesses:
            entrydb = {}
            id = rest['id']
            if id not in idSet:
                entrydb['id'] = id
                entrydb['cuisine'] = cuisine    # cuisine type
                entrydb['name'] = rest['name'] 
                entrydb['insertedAtTimestamp'] = str(datetime.datetime.now())
                entrydb['rating'] = str(rest['rating'])
                entrydb['review_count'] = rest['review_count']
                entrydb['address'] = ", ".join(rest['location']['display_address'])
                entrydb['phone'] = rest["display_phone"]
                entrydb['zip_code'] = rest['location']['zip_code']

                client = boto3.resource(service_name='dynamodb',aws_access_key_id="",aws_secret_access_key="",region_name="us-east-1",)
                table = client.Table('yelp-restaurants')
                table.put_item(Item=entrydb)
                idSet.add(id)

def main():  
    for cuisine in cuisines:    
        pushToDb(cuisine)
        time.sleep(2)

if __name__ == '__main__':
    main()