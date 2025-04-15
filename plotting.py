import matplotlib.pyplot as plt

def plot_graph(df, *args, **kwargs):
    """
    Plots a graph according to data in 'df' and the columns informed on '*args'.
    """
    _, ax = plt.subplots()

    for arg in args:
        ax.plot(df['seconds_passed'], df[arg], label=arg)
        ax.legend()

    plt.xlabel('Seconds')
    plt.ylabel('Value')
    
    plt.savefig(kwargs.get('plot_path') if kwargs.get('plot_path') else './data/plot.png')

def save_video(video, video_path='./data/video.mp4'):
    video.write_videofile(video_path)