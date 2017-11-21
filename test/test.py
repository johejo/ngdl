import time
import statistics
import pickle
import gc
from logging import getLogger, StreamHandler, DEBUG


from ngdl import MODE_ESTIMATE, MODE_CONVEX_DOWNWARD, MODE_CONVEX_UPWARD, MODE_NORMAL
from ngdl import Downloader

handler = StreamHandler()
handler.setLevel(DEBUG)
local_logger = getLogger(__name__)
local_logger.setLevel(DEBUG)
local_logger.addHandler(handler)

if __name__ == '__main__':

    urls0 = ['http://165.242.111.92/ubuntu-17.10-server-i386.template',
             'http://165.242.111.93/ubuntu-17.10-server-i386.template'
             ]

    urls1 = ['http://165.242.111.92/ubuntu-17.10-server-amd64.iso',
             'http://165.242.111.93/ubuntu-17.10-server-amd64.iso'
             ]

    urls2 = [
        'http://ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.10/ubuntu-17.10-server-amd64.iso',  # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.10/ubuntu-17.10-server-amd64.iso',  # toyama
        # 'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-amd64.iso',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-amd64.iso',  # jaist
        # 'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-amd64.iso',  # yamagata
    ]

    urls3 = [
        'http://ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.10/ubuntu-17.10-server-i386.template',  # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.10/ubuntu-17.10-server-i386.template',  # toyama
        # 'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # jaist
        # 'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-i386.template'  # yamagata
    ]

    urls0s = ['https://165.242.111.92/ubuntu-17.10-server-i386.template',
              # 'https://165.242.111.93/ubuntu-17.10-server-i386.template',
              'https://165.242.111.94/ubuntu-17.10-server-i386.template',
              ]

    urls1s = ['https://165.242.111.92/ubuntu-17.10-server-amd64.iso',
              # 'https://165.242.111.93/ubuntu-17.10-server-amd64.iso',
              'https://165.242.111.94/ubuntu-17.10-server-amd64.iso',
              ]

    urls4 = urls0s + urls3
    urls5 = urls1s + urls2

    times = 10

    rbn_mean_data = []
    stack_mean_data = []
    rbn_stdev_data = []
    stack_stdev_data = []
    thp_data = []
    statistic_result = {}
    statistic_data = {}

    params = [(None, None, MODE_NORMAL), (None, None, MODE_ESTIMATE),
              (50, 3, MODE_CONVEX_DOWNWARD), (50, 3, MODE_CONVEX_UPWARD), (50, 1, MODE_CONVEX_DOWNWARD)
              ]
    # pickle_dump = False
    pickle_dump = True

    for param in params:
        param_str = str(param).replace(' ', '_')
        print(param_str)
        bias, power, mode = param
        for i in range(times):
            with open('test', 'wb') as f:
                pass
            begin = time.monotonic()
            with open('test', 'ab') as f:
                with Downloader(urls=urls1s,
                                split_size=1000000,
                                logger=local_logger,
                                parallel_num=1,
                                power=power,
                                bias=bias,
                                mode=mode,
                                ) as dl:
                    local_logger.debug('STARTED')
                    get_bytes_len = 0
                    while dl.is_continue():
                        b = dl.get_bytes()
                        get_bytes_len += len(b)
                        f.write(b)
                    end = time.monotonic()
                    # thp = get_bytes_len * 8 / (end - begin) / (10 ** 6)
                    local_logger.debug('TOTAL: {} bytes'.format(get_bytes_len))
                    local_logger.debug('TIME: {} sec'.format(end - begin))
                    result = dl.get_result()
                    thp = result['thp']
                    local_logger.debug('Throughput: {} Mbps'.format(thp))

            # print(result['return_block_num'])
            # print(result['accumulation'])
            # print(result['server_result'])
            rbn_mean_data.append(statistics.mean(result['return_block_num']))
            stack_mean_data.append(statistics.mean(result['accumulation']))
            rbn_stdev_data.append(statistics.stdev(result['return_block_num']))
            stack_stdev_data.append(statistics.stdev(result['accumulation']))
            thp_data.append(thp)

            if pickle_dump:
                with open('log_{}_{}.pickle'.format(i, param_str), 'wb') as f:
                    pickle.dump(result, f)

        rbn_mean = statistics.mean(rbn_mean_data)
        rbn_stdev = statistics.mean(rbn_stdev_data)
        stack_mean = statistics.mean(stack_mean_data)
        stack_stdev = statistics.mean(stack_stdev_data)
        thp_mean = statistics.mean(thp_data)
        thp_stdev = statistics.stdev(thp_data)

        if pickle_dump:
            with open('statistic_{}.pickle'.format(param_str), 'wb') as f:
                pickle.dump({'rbn_mean': rbn_mean, 'rbn_stdev': rbn_stdev,
                             'stack_mean': stack_mean, 'stack_stdev': stack_stdev,
                             'thp_mean': thp_mean, 'thp_stdev': thp_stdev,
                             }, f)
        gc.collect()
