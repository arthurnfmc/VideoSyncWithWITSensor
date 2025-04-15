# This module handles sensor data IO

import pandas as pd

def read_txt(fpath):
    """
    Reads the WIT sensor .txt file
    """
    df = pd.read_csv(fpath, sep='	')
    return df

def clean_data(df, *args):
    """
    Drops columns on dataframe according to args
    """
    return df.drop(columns=[*args])

def read_data(fpath, *args, **kwargs):
    """
    Reads data and saves to adequate format

    params:

    fpath : string -> wit sensor .txt file path;

    *args : string -> columns to be dropped;

    **kwargs -> configuration for preprocess

    returns:

    df : DataFrame -> pandas dataframe containing data;

    """
    
    # Reading data
    df = read_txt(fpath)
    if args:
        df = clean_data(df, *args)

    # Data preprocess

    # Function to normalize the milliseconds to 3 digits
    def fix_milliseconds(time_str):
        parts = time_str.rsplit(':', 1)
        if len(parts) == 2:
            milliseconds = parts[1].zfill(3)  # pad with zeros on the left
            return f"{parts[0]}:{milliseconds}"
        return time_str  # fallback in case of unexpected format
    df['time'] = df['time'].apply(fix_milliseconds)
    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S:%f')

    # Time passed column
    initial_date = df['time'].iloc[0]
    df['seconds_passed'] = (df['time'] - initial_date).dt.total_seconds()

    # Data grouping

    # Each second is the mean of it's 4 sensor reads (standard process)
    if not kwargs.get('groupMethod') or kwargs.get('groupMethod') == 'NbyN':
        N = kwargs.get('groupN') if kwargs.get('groupN') else 4
        df = df.groupby(df.index // N).mean().reset_index(drop=True)

    # Each second is grouped as recorded
    elif kwargs.get('groupMethod') == "seconds_passed":
        df = df.groupby('seconds_passed').mean().reset_index()

    elif kwargs.get('groupMethod') == "noGroup":
        pass

    else:
        raise Exception("groupMethod informed is invalid!")

    return df

