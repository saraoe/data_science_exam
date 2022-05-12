"""
Script for combining different dfs
"""

import pandas as pd
import changepoint
import covid_clean
import os
import numpy as np

if __name__ =="__main__":
    ### Loading information dynamics and raw emotions
    dynamics_model_path = os.path.join("..", "data", "idmdl", "tweets_emo_date_W3.csv")
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
    timeline_path = os.path.join("..", "data", "covid_events", "timeline_covid.xlsx")
    timeline = pd.read_excel(open(timeline_path, "rb"), engine='openpyxl')
    timeline = covid_clean.clean_timeline(timeline)
    timeline = covid_clean.get_dummies(timeline, cols_to_dummy=["type", "nationality"])

    ## Combining cynamics and timeline
    dynamics_timeline = dynamics_df_w_change.merge(timeline, how="left", on="date")
    for col in ["relevant", "epidemiological", "other", "policy", "danish", "international"]:
        dynamics_timeline[col] = [0 if np.isnan(x) else int(x) for x in dynamics_timeline[col]]

    ### Loading n cases
    owid_path = os.path.join("..", "data", "covid_events", "owid-covid-data.csv")
    owid = pd.read_csv(owid_path)
    owid = owid[owid['location']=='Denmark']
    owid['new_cases_MA7'] = owid['new_cases'].rolling(window=7).mean()

    ## Combing woid with dynamics and timeline
    global_df = dynamics_timeline.merge(owid[["date","new_cases", "new_cases_MA7"]], how="left", on="date")
    
    out_path = os.path.join("..", "data", "model_df.csv")
    # global_df.to_csv(out_path)