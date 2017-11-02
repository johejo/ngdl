from matplotlib import pyplot as plt
import pickle


if __name__ == '__main__':

    filename = 'statistic.pcl'

    with open(filename, 'rb') as f:
        result = pickle.load(f)

    xticks = []
    avg = []
    stdev = []
    for key, value in result.items():
        xticks.append(key)
        avg.append(value['avg'])
        stdev.append(value['stdev'])
    plt.figure(figsize=(24, 10))

    x = [i + 0.4 for i in range(len(result))]
    plt.bar(range(len(result)), avg, width=0.4, align='center', label='AVG')
    plt.bar(x, stdev, width=0.4, align='center', label='STDEV')
    plt.legend()
    xx = [i + 0.2 for i in range(len(result))]
    plt.xticks(xx, xticks)
    plt.xlabel('bias, power')
    plt.title('AVG and STDEV of the number of simultaneous write blocks')

    plt.savefig('write_block_num_1029-w.pdf')
