import json
import logging
import boto3
from boto3.dynamodb.conditions import Attr

LOGGER = logging.getLogger(__name__)


def get_arn(topic_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('topic')

    response = table.get_item(Key={
        "topicName": topic_name
    })
    data = response['Item']

    LOGGER.info(data)
    return data


def lambda_handler(event, context):
    event = json.loads(json.loads(event['Records'][0]['Sns']['Message'])['responsePayload']['body'])
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    sns = boto3.resource('sns')
    
    for tweet in event:
        arn = get_arn(tweet['topic_detected'])['topicArn']
        topic = sns.Topic(arn)
        topic.publish(
            Message="{0} tweeted at {1} about {2}: \"{3}\"".format(
                tweet['user']['screen_name'],
                tweet['created_at'],
                tweet['topic_detected'],
                tweet['text']
            ),
            Subject="New tweet about {0}".format(tweet['topic_detected'])
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps("Nothing to dump here")
    }
