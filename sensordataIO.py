# This module handles sensor data IO

import pandas as pd
import numpy as np

def read_txt(fpath):
    """
    Reads the WIT sensor .txt file
    """
    df = pd.read_csv(fpath, sep='	', engine='python')
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
    **kwargs -> configuration for preprocess (e.g. groupMethod, camera_freq)

    returns:

    df : DataFrame -> pandas dataframe with sensor data adjusted to camera time base
    """

    # Reading data
    df = read_txt(fpath)
    if args:
        df = clean_data(df, *args)

    # Data preprocess
    def fix_milliseconds(time_str):
        parts = time_str.rsplit(':', 1)
        if len(parts) == 2:
            milliseconds = parts[1].zfill(3)
            return f"{parts[0]}:{milliseconds}"
        return time_str

    df['time'] = df['time'].apply(fix_milliseconds)
    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S:%f')

    # Tempo inicial e segundos passados
    initial_date = df['time'].iloc[0]
    df['seconds_passed'] = (df['time'] - initial_date).dt.total_seconds()

    # === Interpolação para base temporal da câmera ===
    camera_freq = kwargs.get("camera_freq", None)
    if camera_freq:
        start_time = df['seconds_passed'].iloc[0]
        end_time = df['seconds_passed'].iloc[-1]
        num_frames = int((end_time - start_time) * camera_freq) + 1

        # Nova base de tempo com frequência da câmera
        new_timebase = pd.DataFrame({
            'seconds_passed': pd.Series(np.linspace(start_time, end_time, num=num_frames))
        })

        # Interpola todas as colunas numéricas para a nova base
        numeric_cols = df.select_dtypes(include='number').columns.drop('seconds_passed')
        df_interp = pd.merge(new_timebase, df[['seconds_passed'] + list(numeric_cols)], on='seconds_passed', how='left')
        df_interp[numeric_cols] = df_interp[numeric_cols].interpolate(method='linear')

        df = df_interp.reset_index(drop=True)

    # === Agrupamento, se necessário ===
    elif not kwargs.get('groupMethod') or kwargs.get('groupMethod') == 'NbyN':
        N = kwargs.get('groupN') if kwargs.get('groupN') else 4
        df = df.groupby(df.index // N).mean().reset_index(drop=True)

    elif kwargs.get('groupMethod') == "seconds_passed":
        df = df.groupby('seconds_passed').mean().reset_index()

    elif kwargs.get('groupMethod') == "noGroup":
        pass

    else:
        raise Exception("groupMethod informado é inválido!")

    return df


