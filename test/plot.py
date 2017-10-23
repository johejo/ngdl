from matplotlib import pyplot as plt
import pickle
import statistics as st
import glob

if __name__ == '__main__':

    file_names = sorted(glob.glob('2017*'))
    server_results = []
    return_block_nums_ave = []
    return_block_nums_stdev = []
    orders = []
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'pink']
    bias = [0, 2, 5, 10, 20, 30, 50]

    for b, filename, color in zip(bias, file_names, colors):
        with open(filename, 'rb') as f:
            result = pickle.load(f)

        exp_data = result['exp_data']
        time = []
        order = []
        for data in exp_data:
            time.append(data['time'])
            order.append(data['order'])

        orders.append(order)

        server_results.append(result['server_result'])
        return_block_nums_ave.append(st.mean(result['return_block_num']))
        return_block_nums_stdev.append(st.stdev(result['return_block_num']))

        plt.plot(time, order, 'x', color=color, label='BIAS: {}'.format(b))
        plt.legend()
        plt.title('Relationship between block arrival time and parameters')
        plt.xlabel('time[s]')
        plt.ylabel('block number')

    # x = [i + 0.4 for i in range(len(bias))]
    # plt.bar(range(len(bias)), return_block_nums_ave, width=0.4, align='center', color='red', label='AVE')
    # plt.bar(x, return_block_nums_stdev, width=0.4, align='center', color='green', label='STDEV')
    # plt.legend()
    # xx = [i + 0.2 for i in range(len(bias))]
    # plt.xticks(xx, bias)
    # plt.xlabel('BIAS')
    # plt.title('AVE and STDEV of the number of simultaneous write blocks')

    plt.show()
