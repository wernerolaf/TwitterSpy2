import json
import logging
import time
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SnsWrapper:
    """Encapsulates Amazon SNS topic and subscription functions."""
    def __init__(self, sns_resource):
        """
        :param sns_resource: A Boto3 Amazon SNS resource.
        """
        self.sns_resource = sns_resource

    def create_topic(self, name):
        """
        Creates a notification topic.

        :param name: The name of the topic to create.
        :return: The newly created topic.
        """
        try:
            topic = self.sns_resource.create_topic(Name=name)
            logger.info("Created topic %s with ARN %s.", name, topic.arn)
        except ClientError:
            logger.exception("Couldn't create topic %s.", name)
            raise
        else:
            return topic.arn
    

def add_topic_to_db(name, arn, table):

    response = table.put_item(
        Item={
            'topicName' : name,
            'topicArn' : arn
        }
    )
    return response

def initializeTopics():
    topics_to_initialize = ['Crypto', 'Test', 'Parrots']

    sns_wrapper = SnsWrapper(boto3.resource('sns'))
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('topic')

    for topic in topics_to_initialize:
        arn = sns_wrapper.create_topic(topic)
        response = add_topic_to_db(topic, arn, table)
        print(f'Creating topic {topic} , response: {response}')

if __name__ == "__main__":
    initializeTopics()
