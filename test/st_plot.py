import glob
import pickle
from matplotlib import pyplot as plt

if __name__ == '__main__':
    filename_list = sorted(glob.glob('statistic*.pickle'))

    rbn_mean = []
    rbn_stdev = []
    stack_mean = []
    stack_stdev = []
    thp_mean = []
    thp_stdev = []
    xticks = []

    for filename in filename_list:
        param = filename[filename.find('('):filename.rfind('.')]
        with open(filename, 'rb') as f:
            p = pickle.load(f)
        rbn_mean.append(p['rbn_mean'])
        rbn_stdev.append(p['rbn_stdev'])
        stack_mean.append(p['stack_mean'])
        stack_stdev.append(p['stack_stdev'])

        xticks.append(param)

    plt.figure(figsize=(16, 10))
    x_mean = range(len(filename_list))
    plt.bar(x_mean, rbn_mean, yerr=rbn_stdev)
    plt.xticks(x_mean, xticks)
    plt.title('Number of simultaneous write blocks')
    plt.savefig('write_block_num.pdf')

    plt.figure(figsize=(16, 10))
    x_mean = range(len(filename_list))
    plt.bar(x_mean, stack_mean, yerr=stack_stdev)
    plt.xticks(x_mean, xticks)
    plt.title('Number of stack blocks')
    plt.savefig('stack_block_num.pdf')


