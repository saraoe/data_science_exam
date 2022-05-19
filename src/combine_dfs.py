"""
Script for combining different dfs
"""

import pandas as pd
import changepoint
import covid_clean
import os
import re
from typing import List

def get_emotion_distribution(emo: str, n: int=8):
    '''
    For transforming the BERT emotion distribution from a str to a list of floats
    If there is no emotion distribution, it returns NaN
    '''
    if not isinstance(emo, str): # if emo == NaN
        return emo
    emo_list = re.split(r',\s+', emo[1:-1])[:n]
    emo_list = list(map(lambda x: float(x), emo_list))
    return emo_list

def find_add_change_points(df: pd.DataFrame, 
                            signal:str = 'resonance', 
                            penalty: float = 4):
    '''Finds change points in signal and adds column to df indicating change point period

    Args:
        df (pd.DataFrame): dataframe with signal to find change points in
        signal (str, optional): the signal to change points in. Default to 'resonance'
        penalty (float, optional): penalty parameter for algorithm. Defaults to 4.
    
    returns:
        df (pd.DataFrame): dataframe with column indicating change points
    '''
    change_locations = changepoint.detect_change_points(df[signal].to_numpy(), pen=penalty)

    # List comprehension calculating number of days in each change point period
    cp_lengths = [change_locations[n] if n == 0 else change_locations[n] - change_locations[n-1] for n in range(len(change_locations))]
    cps = sum([[cp+1]*n for cp, n in enumerate(cp_lengths)], [])
    df["change_point"] = cps

    return df

def add_emotion_probabilities(df: pd.DataFrame, 
                              col_name:str = "emo_prob",
                              labels:List[str] = [
                                                'happiness',
                                                'trust',
                                                'expectation',
                                                'surprised',
                                                'anger',
                                                'contempt',
                                                'grief',
                                                'fear'
                                                ]):
    '''Adds column with daily mean probability for each emotion in labels to df
    Throws an assertion error if number of labels is not equal to number of emotions

    Args:
        df (pd.DataFrame): dataframe with column with list of emotion probabilities 
        col_name (str, optional): name of the column with emotion probabilities. Defaults to emo_prob
        labels (List[str], optional): list of labels to use for column names. 
    
    Return:
        df (pd.DataFrame): the input dataframe with emotion probability columns added
    '''
    emo_lists = list(map(get_emotion_distribution,list(df[col_name])))
    assert len(emo_lists[0]) == len(labels), \
        f'Number of labels provided ({len(labels)}) must be equal to number of emotion probabilities ({len(emo_lists[0])})'
    for i, label in enumerate(labels):
        df[label] = [distribution[i] for distribution in emo_lists]

    return df

def load_prepare_ssi_timeline(path: str, 
                              dummy_cols:List[str]=["type", "nationality"]):
    '''Loads and prepares the SSI timeline

    Args:
        path (str): path to where the file is located
        dummy_cols (List[str], optional): list of columns to create dummy variables for. Default to ["type", "nationality"]
    
    returns:
        timeline (pd.DataFrame): the cleaned timeline with dummy variables added
    '''
    timeline = pd.read_excel(open(path, "rb"), engine='openpyxl')
    timeline = covid_clean.clean_timeline(timeline)
    timeline = covid_clean.get_dummies(timeline, cols_to_dummy=dummy_cols)

    return timeline

def merge_dynamics_timeline(dynamics_df: pd.DataFrame, 
                            timeline: pd.DataFrame, 
                            col_list:List[str] = ["epidemiological", 
                                                  "other", 
                                                  "policy", 
                                                  "danish", 
                                                  "international"]):
    '''Combines the information dynamics dataframe (possibly including emotions) with the timeline dataframe

    Args:
        dynamics_df (pd.DataFrame): the dynamics dataframe
        timeline (pd.DataFrame): the timeline dataframe
        col_list (List[str], optional): column to include from timeline
    
    Returns:
        dynamics_df (pd.DataFrame): the combined dataframe
    '''

    for col in col_list:
        tmp = []
    for date in dynamics_df['date']:
        if any(timeline[timeline['date']==date][col]):
            tmp.append(1)
        else:
            tmp.append(0)
    dynamics_df[col] = tmp
    return dynamics_df

def load_prepare_owid(path:str, 
                      window=7,
                      average:str = "new_cases"):
    '''Loads the owid (Our World In Data) data of daily number of COVID cases and computes rolling average 
    
    Args:
        path (str): path to where the file is located
        window (int, optional): window size in days to use for rolling average. Defaults to 7
        average (str, optional): the column to compute rolling average on. Defaults to 'new_cases'
    
    Returns:
        owid (pd.DataFrame): the dataframe with rolling average calculated
    '''
    owid = pd.read_csv(path)
    owid = owid[owid['location']=='Denmark']
    owid[f'{average}_MA{window}'] = owid[average].rolling(window=window).mean()
    return owid

def merge_df_owid_cases(df: pd.DataFrame, owid: pd.DataFrame, n_tweets: pd.DataFrame):
    '''Merges the three provided dataframes on date
    
    Args:
        df (pd.DataFrame): the dynamics and emotion probability dataframe
        owid: (pd.DataFrame) the preprocessed owid dataframe
        n_tweets (pd.DataFrame): the dataframe with daily number of tweets and covid tweets proportion
    
    Returns:
        global_df (pd.DataFrame): the merged dataframes
    '''
    tmp_df = df.merge(owid[["date","new_cases", "new_cases_MA7"]], how="left", on="date")
    global_df = tmp_df.merge(n_tweets[["date", "n_all_tweets", "n_keyword_tweets", "proportion_keyword_tweets"]],
                                how='left', on='date')
    return global_df

if __name__ =="__main__":
    ### Loading information dynamics and raw emotions
    dynamics_model_path = os.path.join("/home", "stine", "data_science_exam", "data", "idmdl", "tweets_emo_date_W3.csv")
    df = pd.read_csv(dynamics_model_path)
    labels = [
        'happiness',
        'trust',
        'expectation',
        'surprised',
        'anger',
        'contempt',
        'grief',
        'fear'
    ]

    ### Find change points and extract emotion probabilities
    df = find_add_change_points(df)
    df = add_emotion_probabilities(df)

    ### Loading SSI timeline
    timeline_path = os.path.join("..", "data", "covid_events", "timeline_covid.xlsx")
    timeline = load_prepare_ssi_timeline(timeline_path)

    ### Loading n cases
    owid_path = os.path.join("..", "data", "covid_events", "owid-covid-data.csv")
    owid = load_prepare_owid(owid_path)

    ### Loading n_tweets
    n_tweets_path = os.path.join("..", "data", "covid_events", "n_tweets.csv")
    n_tweets = pd.read_csv(n_tweets_path, index_col=0)

    ### Merging all dfs
    df = merge_dynamics_timeline(df, timeline)
    global_df = merge_df_owid_cases(df, owid, n_tweets)
    
    out_path = os.path.join("..", "data", "model_df.csv")
    global_df.to_csv(out_path)
