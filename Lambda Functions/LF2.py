import json
import boto3
from pip._vendor import requests
import logging
import random as rn

logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

session = boto3.session.Session()
sqs = session.client('sqs', region_name='us-east-1')

def lambda_handler(event, context):
    
    queueURL="https://sqs.us-east-1.amazonaws.com/767397968615/RestaurantQueue"
    messages = sqs.receive_message(QueueUrl=queueURL)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    
    if 'Messages' in messages:
        for message in messages['Messages']: 
            
            sqs.delete_message(QueueUrl=queueURL,ReceiptHandle=message['ReceiptHandle'])                        
            
            messageBody=json.loads(message['Body'])
            cuisine=messageBody['cuisine']
            email=messageBody['email']
            location=messageBody['location']
            time=messageBody['time']
            count=messageBody['count']
            
            url = 'https://search-es-test-gd6ka5rkmhvujnvg3znqp334je.aos.us-east-1.on.aws/restaurants/_search?size=50&&q=cuisine:'+cuisine
            esResponse = requests.get(url, headers={"Content-Type": "application/json"}, auth=("id", "pass"))
            data = json.loads(esResponse.content.decode('utf-8'))
            restaurant_ids=data['hits']['hits']
            
            max_res = len(restaurant_ids)
            res_list = []
            res_indices=[rn.randint(0, max_res), rn.randint(0, max_res), rn.randint(0, max_res)]
            for i in res_indices:
                res_id = restaurant_ids[i]['_id']
                item = table.get_item(Key={
                    'id': res_id
                })
                res_list.append(item['Item'])
                res_data_for_email = str()
    
                for item in res_list:
                    res_data_for_email += item['name'] + " at " + item['address'] + "<br>"
                print(res_data_for_email)
            
            AWS_REGION = "us-east-1"
            client = boto3.client('ses',region_name=AWS_REGION)

            BODY_TEXT = ("AWS project in (Python)")
            CHARSET = "UTF-8"
            # The HTML body of the email.
            BODY_HTML = """<html>
                <head></head>
                <body>
                    <h1>Restaurant Suggestions</h1>
                    <p>Heyyy, you can try the following restaurants</p>
                    <p>""" + res_data_for_email + """</p>
                    <p>for your reservation at """ + time + """ for """ + count + """ people.</p>
                </body>
                </html>"""
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        email,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': "Dinner Reservation",
                    },
                },
                Source='swaran.work@gmail.com',
            )
            
            logger.debug("Restaurant List1" + res_data_for_email)
            print("Restaurant List" + res_data_for_email)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }