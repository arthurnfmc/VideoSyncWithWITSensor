import sensordataIO
import plotting

if __name__ == "__main__":
    df = sensordataIO.read_data('./data/20250409175709.txt', 'DeviceName', 'Version()', 'Battery level(%)')
    print(df)
    plotting.plot_graph(df, 'AccX(g)', 'AccY(g)', 'AccZ(g)')
