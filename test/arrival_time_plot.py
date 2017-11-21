from matplotlib import pyplot as plt
import pickle
import glob

if __name__ == '__main__':

    file_names = sorted(glob.glob('2017*'))

    for filename in file_names:
        t = int(filename[filename.find('t') + 1:filename.find('b')])
        bias = int(filename[filename.find('b') + 1:filename.find('p')])
        power = int(filename[filename.find('p') + 1:filename.find('p') + 2])
        if t == 0:
            with open(filename, 'rb') as f:
                result = pickle.load(f)

            exp_data = result['exp_data']
            time = []
            order = []
            for data in exp_data:
                time.append(data['time'])
                order.append(data['order'])

            plt.plot(time, order, '.', markersize=3, label='bias: {}, power: {}'.format(bias, power))
            plt.legend()

    plt.title('Relationship between block arrival time and parameters')
    plt.xlabel('time[s]')
    plt.ylabel('block number')
    plt.savefig('arrival_time.pdf')
