import json
import logging
import boto3
from boto3.dynamodb.conditions import Attr

LOGGER = logging.getLogger(__name__)


def create_tweet_record(table, tweet):
    item = {
            'tweetId': tweet['id_str'],
            'topic': tweet['topic_detected'],
            'userScreenName' : tweet['user']['screen_name'],
            'createdAt' : tweet['created_at'],
            'tweetText' : tweet['text']
    }

    response = table.put_item(Item=item)
    LOGGER.info(f"added tweet with id {tweet['id_str']} to db")
    return response


def validate(sub, topic):
    return topic in sub['topics']


def lambda_handler(event, context):
    event = json.loads(json.loads(event['Records'][0]['Sns']['Message'])['responsePayload']['body'])

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('tweets')
    counter = 0
    for tweet in event:
        counter += 1
        response = create_tweet_record(table, tweet)

    return {
        'statusCode': 200,
        'body': json.dumps("Added {} records to db.".format(counter))
    }
