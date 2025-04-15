import numpy as np
import pandas as pd
from moviepy import VideoFileClip # type: ignore

def make_cuts_sensor(df, start_time=None, video_length=None):
    """
    Cuts sensor data before 'start_time' and after 'video_length' has passed. All are measured in seconds. 

    In case none of the above is passed, data is not cut.
    """

    if start_time==None and video_length==None:
        return df
    
    # Left cut
    df = df[df['seconds_passed'] > start_time]

    # Right cut
    df = df[df['seconds_passed'] < (start_time+video_length)]
    
    # Starting at 0 again
    df['seconds_passed'] = df['seconds_passed'] - df['seconds_passed'].min()

    return df

def make_cuts_video(video, start_time=None, video_length=None):
    """
    Cuts video data before 'start_time' and after 'video_length' has passed. All are measured in seconds in following format: seconds.milliseconds. e.g.

    15.760 --> 15 seconds and 760 milliseconds 

    In case none of the above is passed, data is not cut.
    """

    if start_time==None and video_length==None:
        return video
    
    return video.subclipped(start_time, start_time+video_length)
