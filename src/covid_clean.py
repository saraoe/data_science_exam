import pandas as pd
import os
from datetime import datetime
from typing import List

def convert_dates(df:pd.DataFrame, date_column="date", year_column="year", exclude_date:List[str]=["Midt nov", "Jan"]):
    """Converting dates from Danish and messy to compatible

    Args:
        df (pd.DataFrame): dataframe with dates to clean
        date_column (str, optional): column name of column with dates. Defaults to "date".
        year_column (str, optional): column name of column with year. Defaults to "year".
        exclude_date (List[str], optional): list of date string to exclude. Defaults to ["Midt nov", "Jan"].

    Returns:
        df (pd.DataFrame): the input dataframe with date column updated and converted
    """    
    df = df[~df["date"].isin(exclude_date)]
    
    # Prepare date_column strings to datetime parsing
    df[date_column] = [date.replace("maj", "may").replace("okt", "oct").replace(".", "") for date in df[date_column]]

    df[date_column] = [datetime.strptime(date, "%d %b").strftime("%m-%d") for date in df[date_column]]
    df[date_column] = [str(y)+"-" for y in df[year_column]] +  df[date_column]
    
    return df


def clean_timeline(timeline: pd.DataFrame):
    """Clean the timeline dataframe

    Args:
        timeline (pd.DataFrame): dataframe to clean

    Returns:
        timeline (pd.DataFrame): cleaned dataframe
    """    

    timeline = timeline[timeline["type"].apply(lambda x: not isinstance(x, float))]
    timeline["year"] = [int(y) for y in timeline["year"]]
    timeline["relevant"] = [int(y) for y in timeline["relevant"]]
    timeline = convert_dates(timeline)

    return timeline

def get_dummies(timeline, cols_to_dummy=["type", "nationality", "relevant"]):
    """Get dummy variables for specied columns

    Args:
        timeline (pd.DataFrame): dataframe with column to dummy code
        cols_to_dummy (list, optional): list of column to dummy. Defaults to ["type", "nationality", "relevant"].

    Returns:
        timeline (pd.DataFrame): dataframe with dummies added
    """    
    for col in cols_to_dummy:
        if col == "relevant":
            dummy = pd.get_dummies(timeline[col], prefix="relevant")
        else:
            dummy = pd.get_dummies(timeline[col])
        timeline = timeline.join(dummy)
    return timeline

if __name__ == "__main__":
    timeline_path = os.path.join("..", "..", "HOPE-keyword-query-Twitter", "timeline_covid.xlsx")
    timeline = pd.read_excel(open(timeline_path, "rb"), engine='openpyxl')
    timeline = clean_timeline(timeline)
    timeline = get_dummies(timeline)

    print(timeline.head())
