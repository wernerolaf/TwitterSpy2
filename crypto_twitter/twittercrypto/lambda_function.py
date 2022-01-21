import json

import config
import spacy
from spacy.matcher import PhraseMatcher
from twitter import Twitter, OAuth

auth = OAuth(
	consumer_key=config.API_KEY,
	consumer_secret=config.API_SECRET,
	token=config.ACCESS_TOKEN,
	token_secret=config.ACCESS_TOKEN_SECRET
)

nlp = spacy.load("/opt/en_core_web_sm-2.2.5/en_core_web_sm/en_core_web_sm-2.2.5")

TOPIC_DICT = {
	"Crypto": [nlp(text) for text in ['cryptocurrency', 'bitcoin', 'ethereum', 'blockchain', 'dogecoin', 'crypto']],
	"Parrots": [nlp(text) for text in ['parrot', 'ara', 'macaw', 'psittacine', 'parakeet', 'cockatoo']]
}

PHRASE_MATCHERS = dict()
for topic, phrases in TOPIC_DICT.items():
	PHRASE_MATCHERS[topic] = PhraseMatcher(nlp.vocab, attr="LEMMA")
	# for spaCy 3.0 replace with .add(topic, phrases)
	PHRASE_MATCHERS[topic].add(topic, None, *phrases)


def find_topic(tweet, topic):
	sentence = nlp(tweet["text"].lower())
	matched_phrases = PHRASE_MATCHERS[topic](sentence)
	return len(matched_phrases) > 0


def lambda_handler(event, context):
	event = json.loads(event['body'])

	api = Twitter(auth=auth)
	tweets = api.statuses.user_timeline(screen_name=event['screen_name'])
	matches = [tweet for tweet in tweets if find_topic(tweet, event['topic'])]
	for i in range(len(matches)):
		matches[i].update({"topic_detected": event['topic']})
	return {
		"statusCode": 200,
		"body": json.dumps(matches)
	}
