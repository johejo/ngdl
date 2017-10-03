from concurrent.futures import ThreadPoolExecutor, as_completed
from hyper import HTTPConnection
from urllib.parse import urlparse
import queue
import requests
import os


def make_id_queue(num):
    q = queue.Queue()
    for i in range(num):
        q.put(str(i))
    return q


def get_content_length(url):
    hr = requests.head(url.scheme + '://' + url.netloc + url.path)
    return int(hr.headers['content-length'])


def get_order(header):
    range_header = header['Content-Range']
    index = range_header.find(b'-')
    return int(range_header[:index])


class Downloader(object):
    def __init__(self, urls, parallel_num, split_size):
        self.parallel_num = parallel_num
        self.begin = 0
        self.count = 0
        self.id_queue = make_id_queue(num=self.parallel_num)
        self.data_length = []
        self.futures = {}
        self.urls = {}
        self.conns = {}
        self.body_list = []

        conn_num_per_a_server = int(self.parallel_num // len(urls))
        conn_reminder = int(self.parallel_num % len(urls))

        for url in urls:
            for i in range(conn_num_per_a_server):
                self.set_param(url)
            if conn_reminder > 0:
                self.set_param(url)
                conn_reminder -= 1

        identify = self.id_queue.get()
        self.id_queue.put(identify)

        self.url = url
        self.length = self.data_length[0]

        check_size = self.length // self.parallel_num
        if check_size > split_size:
            self.chunk_size = split_size
        else:
            self.chunk_size = check_size

        self.request_num = self.length // self.chunk_size
        self.reminder = self.length % self.chunk_size
        self.filename = os.path.basename(self.urls[identify].hostname)

        self.file = open(self.filename, 'ab')

    def set_param(self, url):
        identify = self.id_queue.get()
        self.urls[identify] = urlparse(url)
        self.conns[identify] = HTTPConnection(self.urls[identify].hostname)
        self.data_length.append(get_content_length(self.urls[identify]))
        self.id_queue.put(identify)

    def range_request(self, identify):
        conn = self.conns[identify]
        conn.request(method='GET',
                     url=self.url,
                     headers={'Range': 'bytes={0}-{1}'.format(self.begin, self.begin + self.chunk_size - 1)}
                     )
        self.begin += self.chunk_size
        # return conn.get_response().read()
        resp = conn.get_response()
        body = resp.read()
        return body

    def is_finish(self):
        if self.count >= self.request_num:
            return False
        else:
            return True

    def write_block(self):
        current = self.count
        block_list = []
        for future in as_completed(self.futures):
            pass

        block_list = self.body_list

        while current < len(block_list):
            if len(block_list[current]) != 0:
                self.file.write(block_list[current])
                current += 1
            else:
                break

    def download(self):
        with ThreadPoolExecutor(max_workers=self.parallel_num, thread_name_prefix='thread') as executor:
            while self.is_finish():
                identify = self.id_queue.get()
                self.futures[identify] = executor.submit(self.range_request, identify)
                self.id_queue.put(identify)
                self.write_block()
                self.count += 1

    def test_download(self):
        while self.is_finish():
            identify = self.id_queue.get()
            self.body_list.append(self.range_request(identify))
            self.id_queue.put(identify)
            self.write_block()
            self.count += 1
            print(self.count)
