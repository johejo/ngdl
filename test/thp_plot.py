from matplotlib import pyplot as plt
import pickle
import glob

if __name__ == '__main__':
    filename_list = sorted(glob.glob('statistic*.pickle'))
    xticks = []
    x_thp_mean = []
    x_thp_stdev = []

    for filename in filename_list:
        param_str = filename[filename.find('_') + 1:filename.rfind('.')]
        xticks.append(param_str)
        with open(filename, 'rb') as f:
            p = pickle.load(f)
        thp_mean = p['thp_mean']
        thp_stdev = p['thp_stdev']
        x_thp_mean.append(thp_mean)
        x_thp_stdev.append(thp_stdev)

    plt.figure(figsize=(16, 10))
    x_range = range(len(filename_list))

    plt.bar(x_range, x_thp_mean, yerr=x_thp_stdev)
    plt.xticks(x_range, xticks)
    plt.title('Throughput')
    plt.savefig('thp.pdf')
