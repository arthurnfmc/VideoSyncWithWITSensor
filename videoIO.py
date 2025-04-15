from moviepy import VideoFileClip # type: ignore

def read_video(video_path):
    return VideoFileClip(video_path)