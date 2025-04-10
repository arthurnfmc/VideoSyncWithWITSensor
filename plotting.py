import matplotlib.pyplot as plt

def plot_graph(df, *args):
    """
    Plots a graph according to data in 'df' and the columns informed on '*args'.
    """
    _, ax = plt.subplots()

    for arg in args:
        ax.plot(df['seconds_passed'], df[arg], label=arg)
        ax.legend()

    plt.xlabel('Seconds')
    plt.ylabel('Value')
    
    plt.savefig('./data/plot.png')