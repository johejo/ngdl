from ngdl import Downloader
import time
import statistics
from logging import getLogger, StreamHandler, DEBUG
import gc

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
              'https://165.242.111.93/ubuntu-17.10-server-i386.template',
              # 'https://165.242.111.94/ubuntu-17.10-server-i386.template',
              ]

    urls1s = ['https://165.242.111.92/ubuntu-17.10-server-amd64.iso',
              'https://165.242.111.93/ubuntu-17.10-server-amd64.iso',
              # 'https://165.242.111.94/ubuntu-17.10-server-amd64.iso',
              ]

    urls4 = urls0s + urls3
    urls5 = urls1s + urls2

    times = 3

    rbn_mean = []
    stack_mean = []
    rbn_stdev = []
    stack_stdev = []
    thp_data = []

    params = [(0, 0, 'MODE_ESTIMATE'), (50)]

    for bias, power, mode in params:
        for i in range(times - 1):
            with open('test', 'wb') as f:
                pass
            begin = time.monotonic()
            with open('test', 'ab') as f:
                with Downloader(urls=urls5,
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
                    thp = get_bytes_len * 8 / (end - begin) / (10 ** 6)
                    local_logger.debug('TOTAL: {} bytes'.format(get_bytes_len))
                    local_logger.debug('TIME: {} sec'.format(end - begin))
                    local_logger.debug('Throughput: {} Mbps'.format(thp))
                    result = dl.get_result()

            print(result['return_block_num'])
            print(result['accumulation'])
            print(result['server_result'])
            rbn_mean.append(statistics.mean(result['return_block_num']))
            stack_mean.append(statistics.mean(result['accumulation']))
            rbn_stdev.append(statistics.stdev(result['return_block_num']))
            stack_stdev.append(statistics.stdev(result['accumulation']))
            thp_data.append(thp)

    print('rbn_mean: {}'.format(statistics.mean(rbn_mean)))
    print('rbn_stdev: {}'.format(statistics.mean(rbn_stdev)))
    print('stack_mean: {}'.format(statistics.mean(stack_mean)))
    print('stack_stdev: {}'.format(statistics.mean(stack_stdev)))
    print('thp_mean: {}'.format(statistics.mean(thp_data)))

