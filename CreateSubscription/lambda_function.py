import json
import logging
import time
import boto3
import os
import uuid
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SnsWrapper:
    """Encapsulates Amazon SNS topic and subscription functions."""
    def __init__(self, sns_resource):
        """
        :param sns_resource: A Boto3 Amazon SNS resource.
        """
        self.sns_resource = sns_resource
    
    def get_topic(self, arn):
        """
        Retrieves an exisiting notification topic.

        :param arn: ARN of the topic to retrieve.
        :return: The retrieved created topic.
        """
        try:
            topic = self.sns_resource.Topic(arn=arn)
            logger.info("Retrieved topic with ARN %s.", topic.arn)
        except ClientError:
            logger.exception("Couldn't retrieve topic with ARN %s.", arn)
            raise
        else:
            return topic
    
    def list_topics(self):
        """
        Lists topics for the current account.

        :return: An iterator that yields the topics.
        """
        try:
            topics_iter = self.sns_resource.topics.all()
            logger.info("Got topics.")
        except ClientError:
            logger.exception("Couldn't get topics.")
            raise
        else:
            return topics_iter


    @staticmethod
    def subscribe(topic, protocol, endpoint):
        """
        Subscribes an endpoint to the topic. Some endpoint types, such as email,
        must be confirmed before their subscriptions are active. When a subscription
        is not confirmed, its Amazon Resource Number (ARN) is set to
        'PendingConfirmation'.

        :param topic: The topic to subscribe to.
        :param protocol: The protocol of the endpoint, such as 'sms' or 'email'.
        :param endpoint: The endpoint that receives messages, such as a phone number
                         (in E.164 format) for SMS messages, or an email address for
                         email messages.
        :return: The newly added subscription.
        """
        try:
            subscription = topic.subscribe(
                Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
            logger.info("Subscribed %s %s to topic %s.", protocol, endpoint, topic.arn)
        except ClientError:
            logger.exception(
                "Couldn't subscribe %s %s to topic %s.", protocol, endpoint, topic.arn)
            raise
        else:
            return subscription

    def list_subscriptions(self, topic=None):
        """
        Lists subscriptions for the current account, optionally limited to a
        specific topic.

        :param topic: When specified, only subscriptions to this topic are returned.
        :return: An iterator that yields the subscriptions.
        """
        try:
            if topic is None:
                subs_iter = self.sns_resource.subscriptions.all()
            else:
                subs_iter = topic.subscriptions.all()
            logger.info("Got subscriptions.")
        except ClientError:
            logger.exception("Couldn't get subscriptions.")
            raise
        else:
            return subs_iter

    @staticmethod
    def add_subscription_filter(subscription, attributes):
        """
        Adds a filter policy to a subscription. A filter policy is a key and a
        list of values that are allowed. When a message is published, it must have an
        attribute that passes the filter or it will not be sent to the subscription.

        :param subscription: The subscription the filter policy is attached to.
        :param attributes: A dictionary of key-value pairs that define the filter.
        """
        try:
            att_policy = {key: [value] for key, value in attributes.items()}
            subscription.set_attributes(
                AttributeName='FilterPolicy', AttributeValue=json.dumps(att_policy))
            logger.info("Added filter to subscription %s.", subscription.arn)
        except ClientError:
            logger.exception(
                "Couldn't add filter to subscription %s.", subscription.arn)
            raise

    @staticmethod
    def delete_subscription(subscription):
        """
        Unsubscribes and deletes a subscription.
        """
        try:
            subscription.delete()
            logger.info("Deleted subscription %s.", subscription.arn)
        except ClientError:
            logger.exception("Couldn't delete subscription %s.", subscription.arn)
            raise




def get_topic_arns(topic_names):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('topic')
    topic_arns = []
    for topic in topic_names:
        topic_arns.append(table.get_item(Key = {'topicName' : topic})['Item']['topicArn'])
    return topic_arns

def create_subscription_record(type, event):
    id = uuid.uuid4().hex
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('subscription')
    item = {
            'subscriptionId': id,
            'type': type,
            'topics' : event['topics']
    }

    if type == 'discord':
        item['targetUrl'] = event['DiscordUrl']
    elif type == 'email':
        item['email'] = event['email']
    else:
        raise Exception('Invalid type')

    response = table.put_item(Item=item
    )
    return id

def subscribe_to_email_topic(event):

    sns_wrapper = SnsWrapper(boto3.resource('sns'))
    
    topic_arns = get_topic_arns(event['topics'])

    for topic_arn in topic_arns:

        topic = sns_wrapper.get_topic(topic_arn)
        email_sub = sns_wrapper.subscribe(topic, 'email', event['email'])

    id = create_subscription_record('email', event)

    return {
        'statusCode': 200,
        'body': json.dumps(["Created a subscribtion", {'subscribtionId' : id, 'type' : 'email'}])
    }
    

def subscribe_to_discord_topic(event):

    topic_arns = get_topic_arns(event['topics'])

    id = create_subscription_record('discord', event)

    return {
        'statusCode': 200,
        'body': json.dumps(["Created a subscribtion", {'subscribtionId' : id, 'type' : 'discord'}])
    }
    

def no_coffee(event):
    
    return {
        'statusCode': 418,
        'body': json.dumps("I'm a teapot")
    }


def lambda_handler(event, context):
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    subscription_handlers = {
        'email' : subscribe_to_email_topic,
        'discord' : subscribe_to_discord_topic,
        'coffee' : no_coffee
    }
    
    event = json.loads(event['body'])

    #try:
    response = subscription_handlers[event['type']](event)
    #except:
    #    response = {
    #    'statusCode': 400,
    #    'body': json.dumps('Bad request')
    #}

    return response
