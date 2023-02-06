import re
import json
from collections import defaultdict 
from difflib import SequenceMatcher
import spacy
from imdb import Cinemagoer
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')


"""
    Global loading phase, nlp spacy model and keywords
"""
nlp = spacy.load('en_core_web_md')
sia = SentimentIntensityAnalyzer()
HOST_WORDS = {'host'}
NOMINATION_WORDS = {'nom'}
PRESENTATION_WORDS = {'present','introduce','announce'}
CONGRATS_WORDS = {'congraluations', 'congrats', 'wins', 'winner', 'won', 'award'}
PEOPLE_WORDS = {'actor', 'actress', 'director', 'score', 'cecil', 'screenplay'}

def type_check(award):
  if tweet_has_words(award, PEOPLE_WORDS):
    return 'person'
  else:
    return 'title'

def extract_award_name(tweet):

  best_match = re.search('best',tweet, re.I)
  best_start = best_match.span()[0]

  tweet = tweet[best_start:]

  # Punctuation Termination Condition
  matches = re.search(r'[.!?#"\'(@:]', tweet)
  if matches:
    best_end = matches.start()
    tweet = tweet[:best_end]

  # Preposition Termination Condition
  # checkin if the last word is in,for, to
  test_chunk = [x for x in tweet.split(' ') if x]
  if test_chunk[-1] in ["in", "for", "to"]:
      test_chunk = test_chunk[:-1]
      tweet = ' '.join(test_chunk)

  result = tweet.lower()
  return result

# TODO:
# This Can be better improved
# We can add rules when iterating through the labels
def extract_potential_names(tweet):
  names = []
  doc = nlp(tweet)
  for ent in doc.ents:
    if ent.label_ == 'PERSON':
      names.append(ent.text)
  names = [re.fullmatch(r"[A-Z][a-z]+,?\s+(?:[A-Z][a-z]*\.?\s*)?[A-Z][a-z]+", x) for x in names]
  names = [x.group(0) for x in names if x]
  return names

def extract_potential_titles(tweet):

  results = []

  # 1. Using #
  if '#' in tweet:

    tweet = tweet+' '
    start = tweet.index('#')
    end = tweet.index(' ', start)
    target_name = tweet[start+1:end]

    if target_name[:6] not in ['Golden', 'golden', "GOLDEN"]:
      results.append(target_name)
  
  return results

def epn_2(tweet):
  names = []
  doc = nlp(tweet)
  for ent in doc.ents:
    if ent.label_ == 'PERSON':
      names.append(ent.text) 

  # Clean posession form ('s)
  names = [name.replace("'s", '') for name in names]

  # Clean each name by dropping non-alphabet char
  regex = re.compile('[^a-zA-Z ]')
  names = [regex.sub("", name) for name in names]

  return names

def token_match_score(tweet, award):
  
  tweet_token = tweet.lower().split()
  award_token = award.lower().translate(',-').split()

  matches = [x for x in award_token if x in tweet_token]
  count = len(matches)
  award_score = count/float(len(award.split()))

  return award_score

def best_matching_award(tweet, awards):

  # Score Matrix: [(award, score)]
  candidates = [[award, SequenceMatcher(None, tweet.lower(), award.lower()).ratio()] for award in awards]
  candidates = sorted(candidates, key = lambda x: x[1], reverse=True)
  top_5 = [candidate[0] for candidate in candidates][:5]

  # Token Matching 
  final_rounds = [[award, token_match_score(tweet, award)] for award in top_5]
  final_rounds = sorted(final_rounds, key = lambda x: x[1], reverse=True)
  best_award = final_rounds[0][0]

  return best_award

def tweet_has_word(tweet, word):
  return re.search(word, tweet, re.I) is not None

def tweet_has_words(tweet, words):
  for word in words:
    if tweet_has_word(tweet, word):
      return True
  return False

def imdb_match_person(name):
  ia = Cinemagoer()
  people = ia.search_person(name)
  if people:
    return people[0]['name']

#TODO: Change it to adaptive threshold
def organize_freq_threshold(frequency, threshold):
  
  candidates = []
  for name, freq in frequency.items():
    candidates.append([name, freq])

  sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse = True)

  results = [sorted_candidates[0][0]]

  for idx, candidate in enumerate(sorted_candidates):
    
    if idx == 0:
      continue

    prev_name, prev_vote = sorted_candidates[idx-1]
    curr_name, curr_vote = candidate

    if (prev_vote - curr_vote) > threshold:
      break
    else:
      results.append(curr_name)
    
  return results

def load_tweets(year):
	f = open('sample_data/gg{}.json'.format(year))
	tweets_json = json.load(f)
	tweets = []
	for tweet in tweets_json:
		if tweet['text'].isascii():
			tweets.append(tweet['text'])
	unique_tweets = list(set(tweets))
	return unique_tweets

# Mining Awards
def mine_awards(tweets):

  awards = []
  for tweet in tweets:
    if tweet_has_words(tweet, CONGRATS_WORDS):
      if tweet_has_words(tweet, ['for Best']):
        award = extract_award_name(tweet)
        awards.append(award)

  # Need to do 
  awards = list(set(awards))
  return awards

def mine_winners(tweets, awards):

  # Tweet Looping, faster
  awardNwinner2freq = {}
  for tweet in tweets:

    if tweet_has_words(tweet, CONGRATS_WORDS):
      if tweet_has_words(tweet, ['for Best', 'award']):

        best_award = best_matching_award(tweet, awards)
        award_type = type_check(best_award)

        if award_type == 'person':
          pot_names = extract_potential_names(tweet)
        else:
          pot_names = extract_potential_titles(tweet)

        for name in pot_names:
          # unique_names.append(name)
          pair = (best_award, name)
          if pair not in awardNwinner2freq:
            awardNwinner2freq[pair] = 1
          else:
            awardNwinner2freq[pair] += 1
  
  award2name2freq = defaultdict(dict)
  for pair,freq in awardNwinner2freq.items():
    award, name = pair
    award2name2freq[award][name] = freq

  award2winners = defaultdict(list)
  for award in awards:
    award2winners[award] = []

  for award, stats in award2name2freq.items():
    top_selection = organize_freq_threshold(stats, 1)
    award2winners[award] = top_selection[0]

  return award2winners

# Return {award -> [presenters]}
# 34 seconds for all awards
# Mid-Low Accuracy
# TODO: find tune accuracy in KEYWORDS as well as AGGREGATION phase
def mine_presenters(tweets, awards):

  # Tweet-Major: somehow faster than award major
  unique_names = []
  awardNpresenter2freq = {}
  for tweet in tweets:
    if tweet_has_words(tweet, PRESENTATION_WORDS):
      if tweet_has_words(tweet, ["Best", "Award"]):

        best_award = best_matching_award(tweet, awards)
        pot_names = epn_2(tweet)

        for name in pot_names:
          unique_names.append(name)
          pair = (best_award, name)
          if pair not in awardNpresenter2freq:
            awardNpresenter2freq[pair] = 1
          else:
            awardNpresenter2freq[pair] += 1

  unique_names = list(set(unique_names))
  unique_names = [imdb_match_person(name) for name in unique_names]
  unique_names = [x for x in unique_names if x]

  award2name2freq = defaultdict(dict)
  for pair,freq in awardNpresenter2freq.items():
    award, name = pair
    best_name = best_matching_award(name, unique_names)
    award2name2freq[award][best_name] = freq

  
  award2presenters = defaultdict(list)
  for award in awards:
    award2presenters[award] = []

  for award, stats in award2name2freq.items():
    top_selection = organize_freq_threshold(stats, 1)
    award2presenters[award] = top_selection[:2]
  
  return award2presenters

def mine_nominees(tweets,awards):
  
  # unique_names = []
  award_nominees_freq={}
  for tweet in tweets:
    if tweet_has_words(tweet, NOMINATION_WORDS):
      if tweet_has_words(tweet, ["Best", "Award"]):
        best_award = best_matching_award(tweet, awards)

        award_type = type_check(best_award)
        if award_type == 'person':
          pot_names = extract_potential_names(tweet)
        else:
          pot_names = extract_potential_titles(tweet)

        for name in pot_names:
            # unique_names.append(name)
            pair = (best_award, name)
            if pair not in award_nominees_freq:
              award_nominees_freq[pair] = 1
            else:
              award_nominees_freq[pair] += 1

  # unique_names = list(set(unique_names))
  # unique_names = [imdb_match_person(name) for name in unique_names]
  # unique_names = [x for x in unique_names if x]

  award2name2freq = defaultdict(dict)
  for pair,freq in award_nominees_freq.items():
    award, name = pair
    # best_name = best_matching_award(name, unique_names)
    award2name2freq[award][name] = freq

  award2nominees = defaultdict(list)
  for award in awards:
    award2nominees[award] = []

  for award, stats in award2name2freq.items():
    top_selection = organize_freq_threshold(stats, 50)
    award2nominees[award] = top_selection[:5]
  
  return award2nominees

def mine_hosts(tweets):

  host2freq = defaultdict(int)
  for tweet in tweets:
    if tweet_has_words(tweet, HOST_WORDS):
      pot_names = extract_potential_names(tweet)
      for name in pot_names:
        host2freq[name] += 1
  
  return organize_freq_threshold(host2freq, 100)
  


'''
Additional Goals
'''
def get_worst_dressed(tweets):

  worst_dressed_freq = defaultdict(int)
  for tweet in tweets:
    if tweet_has_words(tweet, ['worst dress', 'worst clothes', 'worst uniform']):
        potential_name=extract_potential_names(tweet)
        for name in potential_name:
          worst_dressed_freq[name]+=1
  
  return organize_freq_threshold(worst_dressed_freq, 1)[0]

def get_best_dressed(tweets):

  best_dressed_freq = defaultdict(int)
  for tweet in tweets:
    if tweet_has_words(tweet, ['best dress', 'best clothes', 'best uniform']):
        potential_name=extract_potential_names(tweet)
        for name in potential_name:
          best_dressed_freq[name]+=1
  
  return organize_freq_threshold(best_dressed_freq, 1)[0]


def get_weird_dressed(tweets):

  weird_dressed_freq = defaultdict(int)
  for tweet in tweets:
    if tweet_has_words(tweet, ['weird dress', 'weird clothes', 'weird uniform']):
        potential_name=extract_potential_names(tweet)
        for name in potential_name:
          weird_dressed_freq[name]+=1
  
  return organize_freq_threshold(weird_dressed_freq, 1)[0]


def mine_red_carpet(tweets):
  red_carpet = {}
  red_carpet['Best Dressed'] = get_best_dressed(tweets)
  red_carpet['Worst Dressed'] = get_worst_dressed(tweets)
  red_carpet['Most Controversially Dressed'] = get_weird_dressed(tweets)
  return red_carpet

def sentimental_analysis(tweets):

  name2scores = defaultdict(list)
  for tweet in tweets:
    if tweet_has_words(tweet, CONGRATS_WORDS):
      if tweet_has_words(tweet, ['for Best', 'award']):
        for name in extract_potential_names(tweet):
          scores = sia.polarity_scores(tweet)
          name2scores[name].append(scores['compound'])

  name2average = {}
  for name, scores in name2scores.items():
    mean = sum(scores)/len(scores)
    name2average[name] = mean
  
  most_positive = sorted(name2average, key=name2average.get, reverse=True)[:5]
  most_negative = sorted(name2average, key=name2average.get)[:5]

  senti2tops = {}
  senti2tops['Most Positive'] = most_positive
  senti2tops['Most Negative'] = most_negative
  return senti2tops

def main():
  return

main()