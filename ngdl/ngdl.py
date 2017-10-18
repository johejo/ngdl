from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.parse import urlparse, ParseResult
from typing import List
from collections import deque
from random import randrange
from logging import getLogger, NullHandler
import gc
import requests
from requests.exceptions import ConnectionError
from hyper.contrib import HTTP20Adapter

from .exceptions import PortError, StatusCodeError, NoContentLength, FileSizeError, URIError, NoAcceptRange
from .utils import map_all, get_order

local_logger = getLogger(__name__)
local_logger.addHandler(NullHandler())

DEFAULT_SPLIT_SIZE = 1000


class Downloader(object):
    def __init__(self, urls, split_size=DEFAULT_SPLIT_SIZE, *, parallel_num=None, logger=local_logger):
        """

        :param list urls: URL list
        :param int parallel_num:
        :param int split_size:
        :param logger logger:
        """

        self.logger = logger

        self._original_urls = urls
        self._urls = []  # type: List[ParseResult]
        self._sessions = []  # type: List[requests.Session]
        self._ports = []
        self._length_list = []
        self._is_started = False

        for url in urls:
            self._sessions.append(self._check_url(url))
            self._urls.append(urlparse(url))

        if map_all(self._length_list) is False:
            raise FileSizeError
        length = int(self._length_list[0])

        if length > split_size:
            self._split_size = length // len(urls)
        else:
            self._split_size = split_size

        begin = 0
        self._request_num = length // split_size
        reminder = length % split_size
        if reminder != 0:
            self._request_num += 1

        self._request_queue = deque()

        for i in range(self._request_num):

            if reminder != 0 and i == self._request_num - 1:
                end = begin + reminder - 1
            else:
                end = begin + split_size - 1

            param = {'index': i,
                     'method': 'GET',
                     'headers': {'Range': 'bytes={0}-{1}'.format(begin, end)}
                     }
            self._request_queue.append(param)
            begin += split_size

        self._received_index = 0
        self._future_resp = deque()
        self._data = [None for i in range(self._request_num)]
        self._executor = ThreadPoolExecutor(max_workers=parallel_num)
        self._counts = deque()

        self.logger.debug('Successfully initialized')

    def _check_url(self, url):
        """

        :param url: str
        :return: sess requests.Session
        """
        parsed_url = urlparse(url)  # type: ParseResult

        if parsed_url.netloc == '':
            raise URIError

        if parsed_url.scheme == '' or parsed_url.scheme == 'http':
            if parsed_url.port is None:
                port = 80
            else:
                port = parsed_url.port

        elif parsed_url.scheme == 'https':
            if parsed_url.port is None:
                port = 443
            else:
                port = parsed_url.port

        else:
            raise PortError

        return self._check_host(url, port)  # type: requests.Session

    def _check_host(self, url, port):
        """

        :param url: str
        :param port: int
        :return: sess: request.Session
        """

        parsed_url = urlparse(url)  # type: ParseResult

        sess = requests.Session()
        sess.mount(parsed_url.scheme+'://'+parsed_url.netloc+':'+str(port), HTTP20Adapter())
        resp = sess.head(url=url)
        status = resp.status_code

        if 301 <= status <= 303 or 307 <= status <= 308:
            location = resp.headers['Location']
            self.logger.debug('Host {} is redirected to {}'.format(url, location))
            sess = self._check_url(url=location)
            resp = sess.head(url=location)

        elif status != 200:
            self.logger.debug('Invalid status code: {0}'.format(str(status)))
            raise StatusCodeError

        try:
            length = (resp.headers['Content-Length'])
        except KeyError:
            raise NoContentLength

        try:
            resp.headers['Accept-Ranges']
        except KeyError:
            raise NoAcceptRange

        self._length_list.append(length)

        return sess  # type: requests.Session

    def start_download(self):
        for i in range(self._request_num):
            self._future_resp.append(self._executor.submit(self._request))
        self.logger.debug('SUBMITTED')
        self._is_started = True

    def _create_new_session(self):
        rand = randrange(len(self._sessions))
        url = self._original_urls[rand]
        new_sess = self._check_url(url)
        self._sessions.append(new_sess)

    def _request(self):
        param = self._request_queue.popleft()
        rand = randrange(len(self._sessions))
        sess = self._sessions[rand]  # type: requests.Session
        url = self._original_urls[rand]
        self.logger.debug('Send request index: {} header:  {}'
                          .format(param['index'], param['headers']['Range']))

        try:
            resp = sess.request(method=param['method'], url=url, headers=param['headers'])
        except ConnectionError as e:
            self.logger.debug('{}'.format(e))
            self._request_queue.appendleft(param)
            self._sessions.remove(sess)
            self._create_new_session()
            return self._request()

        status = resp.status_code
        if status != 206:
            self.logger.debug('Failed {} status {}'.format(self._original_urls[rand], status))
            self._request_queue.appendleft(param)
            self._sessions.remove(sess)
            self._original_urls.remove(url)
            return self._request()

        content = resp.content
        range_header = resp.headers['Content-Range']
        order = get_order(range_header, self._split_size)
        self.logger.debug(msg='Received response order: {} header: {}'
                          .format(order, range_header))
        return order, content

    def get_bytes(self):
        """

        :return: bytes
        """

        if not self._is_started:
            self.start_download()

        i = 0
        while i < len(self._future_resp):
            if self._future_resp[i].running():
                i += 1
            else:
                try:
                    order, content = self._future_resp[i].result(timeout=0)
                    self.logger.debug('Successfully get result {}'.format(order))
                    self._data[order] = content
                    self._future_resp.remove(self._future_resp[i])
                    continue
                except TimeoutError:
                    i += 1

        b = bytearray()
        i = self._received_index
        count = 0
        while i < len(self._data):
            if self._data[i] is None:
                break
            else:
                b += self._data[i]
                self._data[i] = None
                i += 1
                count += 1
        self._received_index = i
        if count != 0:
            self._counts.append(count)
            self.logger.debug('Return {} bytes {} blocks'.format(len(b), count))
        gc.collect()
        return b

    def is_continue(self):
        """

        :return bool: status of downloading
        """
        if self._received_index == self._request_num:
            return False
        else:
            return True

    def __enter__(self):
        self.logger.debug('Enter')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug('Exit {}'.format(self._counts))
        self._executor.shutdown()
        return False
