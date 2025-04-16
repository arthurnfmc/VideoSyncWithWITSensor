#import numpy as np
#import pandas as pd
#from moviepy import VideoFileClip # type: ignore
#
#def make_cuts_sensor(df, start_time=None, video_length=None):
#    """
#    Cuts sensor data before 'start_time' and after 'video_length' has passed. All are measured in seconds. 
#
#    In case none of the above is passed, data is not cut.
#    """
#
#    if start_time==None and video_length==None:
#        return df
#    
#    # Left cut
#    df = df[df['seconds_passed'] > start_time]
#
#    # Right cut
#    df = df[df['seconds_passed'] < (start_time+video_length)]
#    
#    # Starting at 0 again
#    df['seconds_passed'] = df['seconds_passed'] - df['seconds_passed'].min()
#
#    return df
#
#def make_cuts_video(video, start_time=None, video_length=None):
#    """
#    Cuts video data before 'start_time' and after 'video_length' has passed. All are measured in seconds in following format: seconds.milliseconds. e.g.
#
#    15.760 --> 15 seconds and 760 milliseconds 
#
#    In case none of the above is passed, data is not cut.
#    """
#
#    if start_time==None and video_length==None:
#        return video
#    
#    return video.subclipped(start_time, start_time+video_length)
#

from moviepy import VideoFileClip
import pandas as pd

def make_cuts_video(video_path, start_time, video_length):
    clip = VideoFileClip(video_path).subclipped(start_time, start_time + video_length)
    output_path = video_path.replace(".mp4", f"_cut_{start_time}s_{video_length}s.mp4")
    clip.write_videofile(output_path, codec='libx264')
    return output_path

def make_cuts_sensor(df, start_time=None, video_length=None):
    if start_time is None and video_length is None:
        return df

    if start_time:
        df = df[df['seconds_passed'] > start_time]
    
    if start_time and video_length:
        df = df[df['seconds_passed'] < (start_time + video_length)]
    elif video_length:
        df = df[df['seconds_passed'] < video_length]

    df['seconds_passed'] = df['seconds_passed'] - df['seconds_passed'].min()

    return df