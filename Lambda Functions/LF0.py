import json
import boto3
import secrets

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    botId='OMKEQDST2K'
    botAliasId='DVQ2DGQBV4'
    localeId='en_US'

    client = boto3.client('lexv2-runtime')

    response = client.recognize_text(
        botId=botId,
        botAliasId=botAliasId,
        localeId=localeId,
        sessionId="sessionId2sda",
        text=event['messages'][0]['unstructured']['text'] 
    )

    return {
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        },
        'statusCode': 200,
        'messages': response['messages'] if 'messages' in response else response
    }
