from matplotlib import pyplot as plt
import pickle
import glob

if __name__ == '__main__':

    filename_list = sorted(glob.glob('log_2*.pickle'))

    for filename in filename_list:
        param = filename[filename.find('('):filename.rfind('.')]
        i = int(filename[filename.find('_') + 1:filename.find('_') + 2])
        with open(filename, 'rb') as f:
            result = pickle.load(f)
        exp_data = result['exp_data']
        arrival_time = []
        order = []
        for data in exp_data:
            arrival_time.append(data['time'])
            order.append(data['order'])

        plt.figure()
        plt.plot(arrival_time, order, '.', markersize=3, label=param)
        plt.legend()
        plt.title('Relationship between block arrival time and parameters')
        plt.xlabel('time[s]')
        plt.ylabel('block number')
        plt.savefig('arrival_time_{}.pdf'.format(param))

    plt.figure()
    for filename in filename_list:
        param = filename[filename.find('('):filename.rfind('.')]
        with open(filename, 'rb') as f:
            result = pickle.load(f)
        exp_data = result['exp_data']
        arrival_time = []
        order = []
        for data in exp_data:
            arrival_time.append(data['time'])
            order.append(data['order'])

        plt.plot(arrival_time, order, '.', markersize=3, label=param)
        plt.legend()
    plt.title('Relationship between block arrival time and parameters')
    plt.xlabel('time[s]')
    plt.ylabel('block number')
    plt.savefig('arrival_time.pdf')
