'''
Detecting change points in resonance signal using ruptures
'''
import numpy as np
import ruptures as rpt
import pandas as pd
import re, os
from typing import List, Optional


def detect_change_points(ts: np.ndarray, pen: int ):
    '''
    detecting change points in a time series using Pelt and cost function rbf

    Args:
        ts (np.ndarray): time series
        pen (int): penalty of the model
    
    Returns
        List of change point locations
    '''
    algo = rpt.Pelt(model="rbf").fit(ts)
    change_locations = algo.predict(pen=pen)
    return change_locations


def get_emotion_distribution(emo: str):
    '''
    For transforming the emotion distribution from a str to a list of floats
    '''
    emo_list = re.sub('[^A-Za-z0-9\s]+', '', emo).split(' ')
    emo_list = list(map(lambda x: float(x), emo_list))
    return emo_list


def emotions_dict(df: pd.DataFrame, emotion_col: str, labels: List[str]):
    '''
    gives dict with list of probabilities for the different emotions in labels from pd.DataFrame 

    Args:
        df (pd.DataFrame): data frame with emotion probabilities
        emotion_col (Optional[str]): name of the col with the emotion probabilities
        labels (Optional[List[str]]): List of the emotion labels
    
    Returns
        dict: with labels as keys and probabilities as values
    '''
    emo_lists = list(map(get_emotion_distribution, list(df[emotion_col])))
    zip_emo_lists = [probs for probs in zip(*emo_lists)]
    return {label: probs for label, probs in zip(labels, zip_emo_lists)}


def write_model_df(df: pd.DataFrame, 
                   change_locations: List[int], 
                   out_path: str,
                   emotion_col: Optional[str] = 'emo_prob',
                   labels: Optional[List[str]]=[
                          "Glæde/Sindsro",
                          "Tillid/Accept",
                          "Forventning/Interrese",
                          "Overasket/Målløs",
                          "Vrede/Irritation",
                          "Foragt/Modvilje",
                          "Sorg/trist",
                          "Frygt/Bekymret"]
                    ):
    '''
    writes df for making the linear models. The df contains columns for the number of changepoint,
    resonance, novelty and transience together with the values for all the labels.

    Args:
        df (pd.Dataframe): dataframe with information signal
        change_locations (List[int]): list of where the change points are (to index the df)
        out_path (str): path for saving the dataframe
        emotion_col (Optional[str]): name of the col with the emotion probabilities. Defaults to 'emo_prob'.
        labels (Optional[List[str]]): List of the labels. If it is not specified the labels from the BERT emotion model us used.
    
    '''
    # define the model df
    model_df = pd.DataFrame(columns=[
        'change_point',
        'resonance',
        'novelty',
        'transience'
    ] + labels)

    for n, (i, j) in enumerate(zip([0]+change_locations[:-1], change_locations)):
        tmp_dict = {'change_point': n}
        tmp_df = df.iloc[i:j]
        # get information signals
        for col in ['resonance', 'novelty', 'transience']:
            tmp_dict[col] = tmp_df[col]
        # get emotion values
        emo_dict = emotions_dict(tmp_df, emotion_col, labels)
        # concat with dataframe
        tmp = pd.DataFrame.from_dict({**tmp_dict, **emo_dict})
        model_df = pd.concat([model_df,tmp])
    model_df.to_csv(out_path)


if __name__=='__main__':
    # define paths and parameters
    df = pd.read_csv('/home/saram/hope-twitter/emoDynamics/idmdl/tweets_emo_date_W3.csv')
    out_path = os.path.join('model_df.csv')
    pen = 4
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

    print(f'''Running changepoint.py with
                out_path: {out_path},
                penalty: {pen},
                labels: {labels}
    ''', end='\n\n')

    change_locations = detect_change_points(df['resonance'].to_numpy(), pen)
    print(f'change locations found: {change_locations}')
    write_model_df(df, change_locations, out_path, labels=labels)
    print('DONE')
