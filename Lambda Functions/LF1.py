import json
import time
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


''' --- Helpers to build responses which match the structure of the necessary dialog actions --- '''


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
	return {
		'sessionState': {
			'sessionAttributes': session_attributes,
			'dialogAction': { 
				'type': 'ElicitSlot',
				'intentName': intent_name,
				'slotToElicit': slot_to_elicit
			},
			'intent': {
				'name': intent_name,
				'state': 'InProgress',
				'slots': slots,
			}
		},
		'messages': [{
			'contentType': 'PlainText',
			'content': message
		}]
	}

def fulfilled(output_session_attributes, intent_name, slots, content):
	return {
		'sessionState': {
			'sessionAttributes': output_session_attributes,
			'dialogAction': { 
				'type': 'Close',
			},
			'intent': {
				'name': intent_name,
				'state': 'Fulfilled',
				'slots': slots,
			}
		},
		'messages': [{
			'contentType': 'PlainText',
			'content': content
		}]
	}

''' --- Helpers ---'''

location_set = {'Manhattan'}
cuisine_set = {'Indian', 'Chinese', 'Italian'}


def item_in_set(item, item_set):
	item_set = {element.lower() for element in item_set}
	return item['value']['interpretedValue'].lower() in item_set


def build_validation_result(is_valid, violated_slot, message_content):
	return {
		'isValid': is_valid,
		'violatedSlot': violated_slot,
		'message': {'contentType': 'PlainText', 'content': message_content}
	}

def print_set(set_to_print):
	delimiter = ', '
	return delimiter.join(map(str, set_to_print))


def validate_booking(booking_location, booking_cuisine, booking_time, booking_count, booking_email, slots):
	if not booking_location: 
		return build_validation_result(False, 'Location', 'Can you please tell me with which locality you want for dinner?')
	if booking_location and not item_in_set(booking_location, location_set):
		return build_validation_result(False, 'Location', 'Sorry, we do not support booking in {} at the moment Please pick from the following options - {}'.format(booking_location['value']['originalValue'], print_set(location_set)))
	if not booking_cuisine: 
		return build_validation_result(False, 'Cuisine', 'What cuisine are you looking for?')
	if booking_cuisine and not item_in_set(booking_cuisine, cuisine_set):
		return build_validation_result(False, 'Cuisine', 'Sorry, we do not have much information on {} cuisine at the moment. Please pick from the following options - {}'.format(booking_cuisine['value']['originalValue'], print_set(cuisine_set)))
	if not booking_time:
		return build_validation_result(False, 'Time', 'What time should I make the reservation for?')
	if booking_time and not 'interpretedValue' in booking_time['value']:
		return build_validation_result(False, 'Time', 'The time you specified was a bit ambiguous, can you please specify again')
	if not booking_count:
		return build_validation_result(False, 'Count', 'For how many people should I make this reservation for?')
	if booking_count and int(booking_count['value']['interpretedValue']) > 12:
		return build_validation_result(False, 'Count', 'For bulk booking mail us at abc@fjk.com, do you want to book a table for fewer people now? If yes, how many?')
	if booking_count and int(booking_count['value']['interpretedValue']) <= 0:
		return build_validation_result(False, 'Count', 'How do I make a reservation for such a low count? C\'mon give me a valid number of people.')
	if not booking_email:
		return build_validation_result(False, 'email', 'Where should I send the reservation details to?')
	if booking_email and not 'interpretedValue' in booking_email['value']:
		return build_validation_result(False, 'email', 'Sorry but I won\'t be able to send the confirmation to this email, specify an alternate email!')
	return build_validation_result(True, None, None)


def make_appointment(intent_request):

	booking_location = intent_request['sessionState']['intent']['slots']['Location']
	booking_cuisine = intent_request['sessionState']['intent']['slots']['Cuisine']
	booking_time = intent_request['sessionState']['intent']['slots']['Time']
	booking_count = intent_request['sessionState']['intent']['slots']['Count']
	booking_email = intent_request['sessionState']['intent']['slots']['email']

	output_session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState']['sessionAttributes'] is not None else {}

	source = intent_request['invocationSource']

	logger.debug(json.dumps(intent_request['sessionState']['intent']['slots']))

	if source == 'DialogCodeHook':
		slots = intent_request['sessionState']['intent']['slots']
		validation_result = validate_booking(booking_location, booking_cuisine, booking_time, booking_count, booking_email, slots)

		if not validation_result['isValid']:
			slots[validation_result['violatedSlot']] = None
			return elicit_slot(
				output_session_attributes,
				intent_request['sessionState']['intent']['name'],
				slots,
				validation_result['violatedSlot'],
				validation_result['message']['content']
			)
	message_body = {
		"location": booking_location['value']['interpretedValue'],
		"cuisine": booking_cuisine['value']['interpretedValue'],
		"time": booking_time['value']['interpretedValue'],
		"count": booking_count['value']['interpretedValue'],
		"email": booking_email['value']['interpretedValue'] 
	}
	sqs = boto3.client('sqs')
	sqs.send_message(
		QueueUrl = "https://sqs.us-east-1.amazonaws.com/767397968615/RestaurantQueue",
		MessageBody = json.dumps(message_body)
	)
	logger.debug("Done sending to queue" + json.dumps(message_body))
	closeResponse = fulfilled(output_session_attributes, intent_request['sessionState']['intent']['name'], slots, "Thank you for using this bot. ")

	return closeResponse




''' --- Intents --- '''


def dispatch(intent_request):
	'''
	Called when the user specifies an intent for this bot.
	'''

	intent_name = intent_request['sessionState']['intent']['name']

	# Dispatch to your bot's intent handlers
	if intent_name == 'DiningSuggestionIntent':
		return make_appointment(intent_request)
	elif intent_name == 'FallbackIntent':
		output_session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState']['sessionAttributes'] is not None else {}
		return fulfilled(output_session_attributes, 'FallbackIntent', {}, str('Sorry I didn\'t catch that. Can you please repeat?'))

	raise Exception('Intent with name ' + intent_name + ' not supported')


''' --- Main handler --- '''


def lambda_handler(event, context):
	'''
	Route the incoming request based on intent.
	The JSON body of the request is provided in the event slot.
	'''
	# By default, treat the user request as coming from the America/New_York time zone.
	os.environ['TZ'] = 'America/New_York'
	time.tzset()
	logger.debug('event.bot.name={}'.format(event['bot']['name']))

	return dispatch(event)
