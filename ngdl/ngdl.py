from concurrent.futures import ThreadPoolExecutor
from hyper import HTTPConnection
from urllib.parse import urlparse
import queue
import requests


def make_id_queue(num):
    q = queue.Queue()
    for i in range(num):
        q.put(str(i))
    return q


def get_data_length(url):
    hr = requests.head(url.scheme + '://' + url.netloc + url.path)
    return int(hr.headers['content-length'])


def get_order(header):
    range_header = header['Content-Range']
    index = range_header.find(b'-')
    return int(range_header[:index])


class Downloader(object):
    def __init__(self, urls, parallel_num):
        self.parallel_num = parallel_num
        self.begin = self.end = 0
        self.id_queue = make_id_queue(num=self.parallel_num)
        self.data_length = self.urls = self.conns = {}

        conn_num_per_a_server = int(self.parallel_num // len(urls))
        conn_reminder = int(self.parallel_num % len(urls))

        for url in urls:
            for i in range(conn_num_per_a_server):
                self.set_param(url)
            if conn_reminder > 0:
                self.set_param(url)
                conn_reminder -= 1

        identify = self.id_queue.get()
        self.length = self.data_length[identify]
        self.id_queue.put(identify)

    def set_param(self, url):
        identify = self.id_queue.get()
        self.urls[identify] = urlparse(url)
        self.conns[identify] = HTTPConnection(host=url.hostname)
        self.data_length[identify] = get_data_length(url)
        self.id_queue.put(identify)

    def range_request(self, identify):
        resp = self.conns[identify].request(method='GET',
                                            url=self.urls[identify],
                                            header={'Range': 'bytes={0}-{1}'.format(self.begin, self.end)}
                                            )
        return resp

    def isfinish(self):
        return True

    def download(self):
        with ThreadPoolExecutor(max_workers=self.parallel_num, thread_name_prefix='thread') as executor:
            while self.isfinish():
                identify = self.id_queue.get()
                future_resp = executor.map(self.range_request(identify), range(self.parallel_num))
                self.id_queue.put(identify)
