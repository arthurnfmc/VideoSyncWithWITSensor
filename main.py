import sensordataIO
import plotting
import actionstart
import videoIO

if __name__ == "__main__":
    df = sensordataIO.read_data('./data/video_data.txt', 'DeviceName', 'Version()', 'Battery level(%)')
    print(df)
    df = actionstart.make_cuts_sensor(df, start_time=8, video_length=11)
    video = videoIO.read_video('./data/gordo_pulando.mp4')
    video = actionstart.make_cuts_video(video, start_time=0.500, video_length=11)
    plotting.plot_graph(df, 'AccX(g)', 'AccY(g)', 'AccZ(g)', plot_path='./data/plot_path.png')
    plotting.save_video(video)
