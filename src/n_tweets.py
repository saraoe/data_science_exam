'''
Counting number of tweets in the relevant data paths
'''

import ndjson, os
from glob import glob
from csv import writer
import re
import pandas as pd
from typing import List


def ndjson_gen(path: str):
    for in_file in glob(path):
        with open(in_file) as f:
            reader = ndjson.reader(f)

            for post in reader:
                yield post


def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)


def count_tweets(path: str, count_keywords: List[str], count_retweets: bool=False):
    '''
    Return df with all tweets from a certain date

    Args:
        path (str): path to where the tweets are
        count_keywords (List[str]): List of keywords that should be included in tweets
        count_retweets (bool): whether retweets should be counted or not
    
    Return:
        (tuple) n_all_tweets, n_keyword_tweets
    '''

    n_all_tweets = {}
    n_keyword_tweets = {}

    for i, tweet in enumerate(ndjson_gen(path)):
        if i % 1000000 == 0:
            print(f'at tweet {i}')
            print(f'have gone through {n_all_tweets.keys()}')
        if not count_retweets and re.search("^RT", tweet['text']):  # if tweet is a retweet
            continue
        date = re.findall(r'(\d+-\d+-\d+)', tweet['created_at'])[0]
        n_all_tweets[date] = n_all_tweets.get(date, 0) +1
        if any([keyword in tweet['text'] for keyword in count_keywords]):
            n_keyword_tweets[date] = n_keyword_tweets.get(date, 0) +1

    return n_all_tweets, n_keyword_tweets


def main(keywords: List[str], in_path: str, out_path: str):
    n_all_tweets, n_keyword_tweets = count_tweets(in_path, keywords)

    ### Creating out csv ###
    print('>> creating out data frame')
    out = pd.DataFrame(columns = ["date", "n_all_tweets", "n_keyword_tweets", "proportion_keyword_tweets"])
    out.to_csv(out_path)
    for i, date in enumerate(n_all_tweets.keys()):
        all_tweets = n_all_tweets[date]
        keyword_tweets = n_keyword_tweets[date]
        proportion_keyword = keyword_tweets/all_tweets
        row = [i, date, all_tweets, keyword_tweets, proportion_keyword]
        append_list_as_row(out_path, row)
        if i % 10==0:
            print(f'At date {row[0]}')

if __name__=='__main__':
    tweets_path = os.path.join('/data', '004_twitter-stopword', '*.ndjson')
    keywords = [
        "selvtest","vaccin","coronapas","mundbind","corona","covid","restriktion","genåb",
        "omicron","alpha","b.1.1.529","b11529","omikron","mutation","variant","lockdown",
        "nedluk","lock-down","delta","indisk variant","indiske variant","b.1.617.2",
        "b16172","ba1","ba2","ba.1","ba.2","pcr","#Covid19dk","revaccin","booster","smitte"
    ]
    out_path = os.path.join('data', 'covid_events', 'n_tweets.csv')

    main(keywords, tweets_path, out_path)

