import json
import logging
import boto3
from discord_notify import Notifier
from boto3.dynamodb.conditions import Attr

SAMPLE_SUBS = [
    {
        "url": "https://discord.com/api/webhooks/850686252797919232/EB-iEm8cEvDfkkFqiOTpDXnrCDMWL6qT926iTEvCHRMrRM5ILVUqowcr4nz7v2Ou8epq",
        "topics": ["cryptocurrency", "data-science"]
    },
    {
        "url": "https://discord.com/api/webhooks/850694204774154260/-wfSYx0r8bwvf81aGIRQlN2Tp2cVCgBQkx1m0D_5bjxfwLVQpQNu1EahmOmVGQueTmOn",
        "topics": []
    }
]

LOGGER = logging.getLogger(__name__)


# is this configured somehow?
def get_subs(debug=False):
    if debug:
        return SAMPLE_SUBS

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('subscription')

    # possibly replace .scan() with .query(), but idk
    response = table.scan(FilterExpression=Attr('type').eq('discord'))
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    LOGGER.info(data)
    return data


# this function should check whether given Discord channel is subbed to given topic
def validate(sub, topic):
    return topic in sub['topics']


def lambda_handler(event, context):
    event = json.loads(json.loads(event['Records'][0]['Sns']['Message'])['responsePayload']['body'])

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    subs = get_subs()
    counter = 0

    for sub in subs:
        for tweet in event:
            is_subbed = validate(sub, tweet['topic_detected'])
            if is_subbed:
                LOGGER.info("{0} is subbed to {1}".format(sub['targetUrl'], tweet['topic_detected']))
                counter += 1
                notifier = Notifier(sub['targetUrl'])
                # btw, tweet ID is enough, the tweet can be accessed from "twitter.com/anyuser/status/$ID"
                notifier.send("{0} tweeted at {1} about {2}: \"{3}\"".format(
                    tweet['user']['screen_name'],
                    tweet['created_at'],
                    tweet['topic_detected'],
                    tweet['text']
                ), print_message=False)

    return {
        'statusCode': 200,
        'body': json.dumps("Notified {} channel(s).".format(counter))
    }
