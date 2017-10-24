from ngdl import Downloader
import time
from logging import getLogger, StreamHandler, DEBUG
import gc

handler = StreamHandler()
handler.setLevel(DEBUG)
local_logger = getLogger(__name__)
local_logger.setLevel(DEBUG)
local_logger.addHandler(handler)

if __name__ == '__main__':

    urls0 = ['http://165.242.111.92:8080/ubuntu-17.10-server-i386.template',
             'http://165.242.111.93:8080/ubuntu-17.10-server-i386.template'
             ]

    urls1 = ['http://165.242.111.92:8080/ubuntu-17.10-server-amd64.iso',
             'http://165.242.111.93:8080/ubuntu-17.10-server-amd64.iso'
             ]

    urls2 = [
        'http://www.ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.10/ubuntu-17.10-server-amd64.iso',  # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.10/ubuntu-17.10-server-amd64.iso',  # toyama
        'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-amd64.iso',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-amd64.iso',  # jaist
        'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-amd64.iso',  # yamagata
    ]

    urls3 = [
        'http://www.ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.10/ubuntu-17.10-server-i386.template',  # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.10/ubuntu-17.10-server-i386.template',  # toyama
        'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # jaist
        'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-i386.template'  # yamagata
    ]

    urls4 = urls0 + urls3
    urls5 = urls1 + urls2

    with open('test', 'wb') as f:
        pass
    begin = time.monotonic()
    with Downloader(urls=urls4,
                    split_size=1000000,
                    logger=local_logger,
                    ) as dl:
        local_logger.debug('STARTED')
        get_bytes_len = 0
        while dl.is_continue():
            b = dl.get_bytes()
            get_bytes_len += len(b)
            with open('test', 'ab') as f:
                f.write(b)
            gc.collect()
        local_logger.debug('TOTAL: {} bytes'.format(get_bytes_len))
        local_logger.debug('TIME: {}'.format(time.monotonic() - begin))
        result = dl.get_result()