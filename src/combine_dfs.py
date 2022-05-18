"""
Script for combining different dfs
"""

import pandas as pd
import changepoint
import covid_clean
import os

if __name__ =="__main__":
    ### Loading information dynamics and raw emotions
    dynamics_model_path = os.path.join("data", "idmdl", "tweets_emo_date_W3.csv")
    dynamics_df = pd.read_csv(dynamics_model_path)

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
    change_locations = changepoint.detect_change_points(dynamics_df['resonance'].to_numpy(), pen=4)
    dynamics_df_w_change = changepoint.write_model_df(dynamics_df, change_locations, labels=labels)

    ### Loading SSI timeline
    timeline_path = os.path.join("data", "covid_events", "timeline_covid.xlsx")
    timeline = pd.read_excel(open(timeline_path, "rb"), engine='openpyxl')
    timeline = covid_clean.clean_timeline(timeline)
    timeline = covid_clean.get_dummies(timeline, cols_to_dummy=["type", "nationality"])

    ## Combining dynamics and timeline
    dates = list(dynamics_df_w_change['date'])
    for col in ["epidemiological", "other", "policy", "danish", "international"]:
        tmp = []
        for date in dynamics_df_w_change['date']:
            if any(timeline[timeline['date']==date][col]):
                tmp.append(1)
            else:
                tmp.append(0)
        dynamics_df_w_change[col] = tmp

    ### Loading n cases
    owid_path = os.path.join("data", "covid_events", "owid-covid-data.csv")
    owid = pd.read_csv(owid_path)
    owid = owid[owid['location']=='Denmark']
    owid['new_cases_MA7'] = owid['new_cases'].rolling(window=7).mean()

    ## Combing owid with dynamics and timeline
    global_df = dynamics_df_w_change.merge(owid[["date","new_cases", "new_cases_MA7"]], how="left", on="date")

    # Combining with n_tweets
    n_tweets_path = os.path.join("data", "covid_events", "n_tweets.csv")
    n_tweets = pd.read_csv(n_tweets_path, index_col=0)
    global_df = global_df.merge(n_tweets[["date", "n_all_tweets", "n_keyword_tweets", "proportion_keyword_tweets"]],
                                how='left', on='date')
    
    out_path = os.path.join("data", "model_df.csv")
    global_df.to_csv(out_path)