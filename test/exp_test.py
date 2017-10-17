from ngdl import Downloader
import time
from logging import getLogger, StreamHandler, DEBUG

handler = StreamHandler()
handler.setLevel(DEBUG)
local_logger = getLogger(__name__)
local_logger.setLevel(DEBUG)
local_logger.addHandler(handler)


if __name__ == '__main__':

    # create file
    with open('test', 'wb') as f:
        pass

    with Downloader(urls=['http://165.242.111.92:8080/ubuntu-17.04-server-i386.template',
                          'http://165.242.111.93:8080/ubuntu-17.04-server-i386.template'
                          ],
                    parallel_num=5,
                    split_size=1000000,
                    logger=local_logger) as dl:
        dl.start_download()
        local_logger.debug('STARTED')
        get_bytes_len = 0
        while dl.is_finish():
            b = dl.get_bytes()
            get_bytes_len += len(b)
            local_logger.debug('Get bytes {}'.format(len(b)))
            with open('test', 'ab') as f:
                f.write(b)
            time.sleep(0.1)
        local_logger.debug('TOTAL: {} bytes'.format(get_bytes_len))
