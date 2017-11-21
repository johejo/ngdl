import time
from logging import getLogger, StreamHandler, DEBUG
from datetime import datetime
import pickle
import statistics as st
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
        'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-amd64.iso',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-amd64.iso',  # jaist
        # 'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-amd64.iso',  # yamagata
    ]

    urls3 = [
        'http://ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.10/ubuntu-17.10-server-i386.template',  # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.10/ubuntu-17.10-server-i386.template',  # toyama
        'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # jaist
        'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-i386.template'  # yamagata
    ]

    urls0s = ['https://165.242.111.92/ubuntu-17.10-server-i386.template',
              'https://165.242.111.93/ubuntu-17.10-server-i386.template'
              ]

    urls1s = ['https://165.242.111.92/ubuntu-17.10-server-amd64.iso',
              'https://165.242.111.93/ubuntu-17.10-server-amd64.iso'
              ]

    urls4 = urls0s + urls3
    urls5 = urls1s + urls2

    # bias_list = [10, 30, 50, 100, 200, 300]
    # power_list = [1, 2, 3, 4, 5]
    # bias_list = [10, 20]
    # power_list = [1, 2]

    params = [(0, 0, 'MODE_ESTIMATE'), (0, 0, None), (50, 1, None), (50, 5, None)]

    # for bias in bias_list:
    #     for power in power_list:
    #         params.append((bias, power))

    split_size = 1000000
    times = 1

    statistic_data = {}
    statistic_result = {}
    for param in params:
        statistic_data[param] = {'avg': [], 'stdev': [], '_avg': [], '_stdev': [], 'thp': []}

    try:
        for i in range(times):
            for param in params:
                bias, power, mode = param
                with open('test', 'wb') as f:
                    pass
                begin = time.monotonic()

                with open('test', 'ab') as f:
                    with Downloader(urls=urls5,
                                    split_size=split_size,
                                    logger=local_logger,
                                    bias=bias,
                                    power=power,
                                    mode=mode,
                                    ) as dl:
                        local_logger.debug('STARTED')
                        get_bytes_len = 0
                        while dl.is_continue():
                            b = dl.get_bytes()
                            get_bytes_len += len(b)
                            f.write(b)
                        end = time.monotonic()
                        local_logger.debug('TOTAL: {} bytes'.format(get_bytes_len))
                        local_logger.debug('TIME: {}'.format(time.monotonic() - begin))
                        thp = get_bytes_len * 8 / (end - begin) / (10 ** 6)
                        local_logger.debug('Throughput: {} Mbps'.format(thp))
                        result = dl.get_result()

                statistic_data[param]['avg'].append(st.mean(result['return_block_num']))
                statistic_data[param]['stdev'].append(st.stdev(result['return_block_num']))
                statistic_data[param]['_avg'].append(st.mean(result['accumulation']))
                statistic_data[param]['_stdev'].append(st.stdev(result['accumulation']))
                statistic_data[param]['thp'].append(thp)
                filename = datetime.now().isoformat() + 't{}b{}p{}m{}.pcl'.format(i, bias, power, mode)
                if i == 0:
                    with open(filename, 'wb') as f:
                        pickle.dump(result, f)
    except Exception as e:
        local_logger.debug('{}'.format(e))

    finally:
        with open('statistic.pcl', 'wb') as f:
            for param in params:
                statistic_result[param] = {'avg': st.mean(statistic_data[param]['avg']),
                                           'stdev': st.mean(statistic_data[param]['stdev']),
                                           '_avg': st.mean(statistic_data[param]['_avg']),
                                           '_stdev': st.mean(statistic_data[param]['_stdev']),
                                           'thp': st.mean(statistic_data[param]['thp']),
                                           }
            pickle.dump(statistic_result, f)
