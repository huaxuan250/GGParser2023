from collections import defaultdict
import json
import os
from implementation import load_tweets, mine_hosts, mine_awards, mine_winners, mine_presenters, mine_nominees, mine_red_carpet, sentimental_analysis

'''Version 0.35'''

OFFICIAL_AWARDS_1315 = ['cecil b. demille award', 'best motion picture - drama', 'best performance by an actress in a motion picture - drama', 'best performance by an actor in a motion picture - drama', 'best motion picture - comedy or musical', 'best performance by an actress in a motion picture - comedy or musical', 'best performance by an actor in a motion picture - comedy or musical', 'best animated feature film', 'best foreign language film', 'best performance by an actress in a supporting role in a motion picture', 'best performance by an actor in a supporting role in a motion picture', 'best director - motion picture', 'best screenplay - motion picture', 'best original score - motion picture', 'best original song - motion picture', 'best television series - drama', 'best performance by an actress in a television series - drama', 'best performance by an actor in a television series - drama', 'best television series - comedy or musical', 'best performance by an actress in a television series - comedy or musical', 'best performance by an actor in a television series - comedy or musical', 'best mini-series or motion picture made for television', 'best performance by an actress in a mini-series or motion picture made for television', 'best performance by an actor in a mini-series or motion picture made for television', 'best performance by an actress in a supporting role in a series, mini-series or motion picture made for television', 'best performance by an actor in a supporting role in a series, mini-series or motion picture made for television']
OFFICIAL_AWARDS_1819 = ['best motion picture - drama', 'best motion picture - musical or comedy', 'best performance by an actress in a motion picture - drama', 'best performance by an actor in a motion picture - drama', 'best performance by an actress in a motion picture - musical or comedy', 'best performance by an actor in a motion picture - musical or comedy', 'best performance by an actress in a supporting role in any motion picture', 'best performance by an actor in a supporting role in any motion picture', 'best director - motion picture', 'best screenplay - motion picture', 'best motion picture - animated', 'best motion picture - foreign language', 'best original score - motion picture', 'best original song - motion picture', 'best television series - drama', 'best television series - musical or comedy', 'best television limited series or motion picture made for television', 'best performance by an actress in a limited series or a motion picture made for television', 'best performance by an actor in a limited series or a motion picture made for television', 'best performance by an actress in a television series - drama', 'best performance by an actor in a television series - drama', 'best performance by an actress in a television series - musical or comedy', 'best performance by an actor in a television series - musical or comedy', 'best performance by an actress in a supporting role in a series, limited series or motion picture made for television', 'best performance by an actor in a supporting role in a series, limited series or motion picture made for television', 'cecil b. demille award']

""" API Interaction Function """

def get_hosts(year):
    '''Hosts is a list of one or more strings. Do NOT change the name
    of this function or what it returns.'''

    with open('results.json') as json_file:
      data = json.load(json_file)
      hosts = data["{}".format(year)]["hosts"]

    # Your code here
    return hosts

def get_awards(year):
    '''Awards is a list of strings. Do NOT change the name
    of this function or what it returns.'''

    with open('results.json') as json_file:
      data = json.load(json_file)
      awards = data["{}".format(year)]["awards"]

    return awards

def get_nominees(year):
    '''Nominees is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change
    the name of this function or what it returns.'''
    # Your code here
    with open('results.json') as json_file:
      data = json.load(json_file)
      nominees = data["{}".format(year)]["nominees"]

    return nominees

def get_winner(year):
    '''Winners is a dictionary with the hard coded award
    names as keys, and each entry containing a single string.
    Do NOT change the name of this function or what it returns.'''
    # Your code here
    with open('results.json') as json_file:
      data = json.load(json_file)
      winners = data["{}".format(year)]["winners"]

    return winners

def get_presenters(year):
    '''Presenters is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change the
    name of this function or what it returns.'''
    # Your code here
    with open('results.json') as json_file:
      data = json.load(json_file)
      presenters = data["{}".format(year)]["presenters"]

    return presenters

def pre_ceremony():
    '''This function loads/fetches/processes any data your program
    will use, and stores that data in your DB or in a json, csv, or
    plain text file. It is the first thing the TA will run when grading.
    Do NOT change the name of this function or what it returns.'''
    # Your code here

    # Some
    year2collection = defaultdict(dict)
    for year in [2013, 2015]:

      data_path = 'sample_data/gg{}.json'.format(year)
      if os.path.exists(data_path):
        yearly_collection = {}

        tweets = load_tweets(year)
        print("There are {} tweets loaded for {}".format(len(tweets), year))
        print()

        print("Begin Mining Hosts:")
        mined_hosts = mine_hosts(tweets)
        yearly_collection["hosts"] = mined_hosts
        print("Hosts Mined.")
        print()

        print("Begin Mining Awards:")
        mined_awards = mine_awards(tweets)
        yearly_collection["awards"] = mined_awards
        print("Awards Mined.")
        print()

        print("Begin Mining Winners:")
        mined_winners = mine_winners(tweets, OFFICIAL_AWARDS_1315)
        yearly_collection["winners"] = mined_winners
        print("Winners Mined.")
        print()

        print("Begin Mining Presenters:")
        mined_presenters = mine_presenters(tweets, OFFICIAL_AWARDS_1315)
        yearly_collection["presenters"] = mined_presenters
        print("Presenters Mined.")
        print()

        print("Begin Mining Nominees:")
        mined_nominees = mine_nominees(tweets, OFFICIAL_AWARDS_1315)
        yearly_collection["nominees"] = mined_nominees
        print("Nominees Mined.")
        print()

        print("Begin EC - Red Carpet:")
        mined_red_carpet = mine_red_carpet(tweets)
        yearly_collection["red_carpet"] = mined_red_carpet
        print("EC - Red Carpet Mined.")
        print()

        print("Begin EC - Sentimental Analysis")
        mined_sentiments = sentimental_analysis(tweets)
        yearly_collection["sentiments"] = mined_sentiments
        print("EC - Sentiments Mined.")
        print()

        year2collection[year] = yearly_collection
    
    with open("results.json", "w") as outfile:
      json.dump(year2collection, outfile, indent=4)

    return

def main():
    '''This function calls your program. Typing "python gg_api.py"
    will run this function. Or, in the interpreter, import gg_api
    and then run gg_api.main(). This is the second thing the TA will
    run when grading. Do NOT change the name of this function or
    what it returns.'''

    # Print Summaries Here
    with open('results.json') as json_file:
      results = json.load(json_file)
      
      for year in ['2013', '2015']:
        if year in results:

          print("Golden Globe 2013 Ceremony")

          hosts = results[year]['hosts']
          print("Hosts: ", hosts)

          sentiments = results[year]['sentiments']
          print("People Most Positive Sentiments: ", sentiments['Most Positive'])
          print("People Most Negative Sentiments: ", sentiments['Most Negative'])

          for award in OFFICIAL_AWARDS_1315:

            print(award)
            
            winner = results[year]['winners'][award]
            print("Winner: ", winner)

            nominees = results[year]['nominees'][award]
            print("Nominees: ", nominees)

            presenters = results[year]['presenters'][award]
            print("Presenters: ", presenters)

            print()

    return

if __name__ == '__main__':
    pre_ceremony()
    main()
