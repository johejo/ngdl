from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.parse import urlparse, ParseResult
from typing import List
from collections import deque
import random
from logging import getLogger, NullHandler
import gc
import traceback
import statistics
import sys
import requests
import time
from requests.exceptions import ConnectionError
from hyper.contrib import HTTP20Adapter, HTTPAdapter
from hyper.http11.parser import ParseError
from requests.exceptions import Timeout

from .exceptions import PortError, StatusCodeError, NoContentLength, FileSizeError, URIError, NoAcceptRange
from .utils import map_all, get_order, kill_all

local_logger = getLogger(__name__)
local_logger.addHandler(NullHandler())

DEFAULT_SPLIT_SIZE = 1000
DEFAULT_BIAS = 0
DEFAULT_POW = 0
DEFAULT_PARALLEL_NUM = 5
DEFAULT_THRESHOLD_RETRANSMISSION = 20

MODE_ESTIMATE = 'MODE_ESTIMATE'
MODE_CONVEX_DOWNWARD = 'MODE_CONVEX_DOWNWARD'
MODE_CONVEX_UPWARD = 'MODE_CONVEX_UPWARD'
MODE_NORMAL = 'MODE_NORMAL'


class Downloader(object):
    def __init__(self, urls, split_size=DEFAULT_SPLIT_SIZE, *,
                 parallel_num=DEFAULT_PARALLEL_NUM,
                 logger=local_logger,
                 bias=DEFAULT_BIAS,
                 power=DEFAULT_POW,
                 mode=None,
                 ):
        """
        :param list urls: URL list
        :param int parallel_num:
        :param int split_size:
        :param logger logger:
        """

        self.logger = logger

        self._bias = bias
        self._power = power
        self._urls = urls.copy()
        default = 1.0 / len(urls)
        self._priority = [default for _ in urls]

        self._length_list = []
        self._sessions = [self._check_url(url) for url in urls]  # type: List[requests.Session]
        self._ports = []
        self._host_ids = deque()

        for i in range(len(self._urls)):
            for j in range(parallel_num):
                self._host_ids.append(i)
        random.shuffle(self._host_ids)
        self._url_received_counts = [0 for _ in range(len(self._urls))]

        self._is_started = False

        if map_all(self._length_list) is False:
            raise FileSizeError
        self._length = int(self._length_list[0])

        if self._length < split_size:
            self._split_size = self._length // len(urls)
        else:
            self._split_size = split_size

        begin = 0
        self._request_num = self._length // split_size
        reminder = self._length % split_size
        if reminder != 0:
            self._request_num += 1

        self._params = []

        for i in range(self._request_num):

            if reminder != 0 and i == self._request_num - 1:
                end = begin + reminder - 1
            else:
                end = begin + split_size - 1

            param = {'host_id': i,
                     'method': 'GET',
                     'headers': {'Range': 'bytes={0}-{1}'.format(begin, end)}
                     }
            self._params.append(param)
            begin += split_size

        self._received_index = 0
        self._future_resp = []
        self._data = [None for _ in range(self._request_num)]
        self._executor = ThreadPoolExecutor(max_workers=parallel_num * len(self._urls))
        self._return_block_num = []
        self._accumulation = []

        self._plot = []
        self._time = []
        self._exp_data = []
        self._begin_time = time.monotonic()
        self._end_time = None

        self._bad_urls = []
        self._bad_host_id = []

        self._used_params = [None for _ in range(self._request_num)]
        self._previous_received_count = [0 for _ in range(len(self._urls))]
        self._current_receive_count = 0
        self._hosts = [urlparse(url).hostname for url in self._urls]
        self._mode = mode
        self._diffs = []

        self.logger.debug('Init')

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
        prefix = parsed_url.scheme + '://' + parsed_url.netloc
        self.logger.debug('Prefix: {}'.format(prefix))
        sess.mount(prefix, HTTP20Adapter())
        # sess.mount(prefix, HTTPAdapter())
        resp = sess.head(url=url, verify=False)
        status = resp.status_code

        if 301 <= status <= 303 or 307 <= status <= 308:
            location = resp.headers['Location']
            self._urls.remove(url)
            self._urls.append(location)
            print('Host {} is redirected to {}'.format(url, location), file=sys.stderr)
            sess = self._check_url(url=location)
            resp = sess.head(url=location)

        elif status != 200:
            self.logger.debug('Invalid status code: {0}'.format(str(status)))
            raise StatusCodeError

        self.logger.debug('File has found: {}'.format(url))

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

    def _get_index_rand(self):
        rand = random.random()
        v = 0
        for i, priority in enumerate(self._priority):
            v += priority
            if rand <= v:
                return i

    def _set_priority(self, index, ratio):
        old = self._priority[index]
        new = old * ratio
        if new > 1.0:
            new = 1.0
        diff = old - new
        each = diff / (len(self._priority) - 1)

        c = 0
        for i in range(len(self._priority)):
            if i == index:
                self._priority[i] = new
            else:
                self._priority[i] += each

            if self._priority[i] < 0:
                c += 1
                self._priority[i] = 0

        under = sum(self._priority) - 1.0

        if under != 0:
            u_each = under / (len(self._priority) - c - 1)
            for i in range(len(self._priority)):
                if self._priority[i] != 0 and i != index:
                    self._priority[i] -= u_each

        self.logger.debug('Connection Priority: {}'.format(self._priority))

        if sum(self._priority) > 1.00001:
            self.logger.debug('{}'.format(sum(self._priority)))
            kill_all()

    def _get_param_index(self, index):

        if self._power == 0:
            return 0

        c = self._url_received_counts[index]
        m = max(self._url_received_counts)

        try:
            x = c / m
            self.logger.debug('Ratio: {}'.format(x))
            if self._mode == MODE_CONVEX_DOWNWARD:
                y = int(self._bias * (1.0 - (1.5 * x)) ** self._power)
            elif self._mode == MODE_CONVEX_UPWARD:
                y = int(self._bias * (1.0 - (1.5 * x) ** self._power))
            else:
                y = 0

            if y < 0:
                y = 0
        except ZeroDivisionError:
            y = 0

        return y

    def _get_randrange(self):
        rand = random.randrange(len(self._urls))
        if rand in self._bad_host_id:
            return self._get_randrange()
        else:
            return rand

    def _set_bad_url(self, host_id):
        if host_id not in self._bad_host_id:
            self._bad_urls.append(self._urls[host_id])
            self._bad_host_id.append(host_id)

    def _re_request_new_session(self, host_id, param):
        self._host_ids.append(host_id)
        new_sess = self._remake_session(host_id)
        self._sessions.insert(host_id, new_sess)
        self._params.insert(0, param)
        return self._request()

    def _re_request_other_session(self, host_id, param):
        self._set_bad_url(host_id)
        new_index = self._get_randrange()
        self.logger.debug('New index: {}'.format(new_index))
        self._host_ids.append(new_index)
        self._params.insert(0, param)
        return self._request()

    def _remake_session(self, host_id):
        url = self._urls[host_id]
        return self._check_url(url)

    def _request(self):

        # print(self._host_ids)
        # print(self._bad_host_id)
        # print(self._bad_urls)

        while True:
            try:
                host_id = self._host_ids.pop()
                break
            except IndexError:
                self.logger.debug('Que is empty')
                self._host_ids.append(self._get_randrange())
                continue

        if self._mode == MODE_ESTIMATE:
            self._current_receive_count += 1
            previous = self._previous_received_count[host_id]
            diff = self._current_receive_count - previous
            self._diffs.append(diff)
            self.logger.debug('Diff: {}'.format(diff))
            self._previous_received_count[host_id] = self._current_receive_count

            mean = statistics.mean(self._diffs)
            if diff <= mean:
                self.logger.debug('Diff mean: {}'.format(mean))
                x = 0
            else:
                x = diff

        elif self._mode == MODE_NORMAL:
            x = 0

        else:
            x = self._get_param_index(host_id)

        while True:
            try:
                param = self._params.pop(x)
                break
            except IndexError:
                x -= 1

        sess = self._sessions[host_id]  # type: requests.Session
        url = self._urls[host_id]
        parsed_url = urlparse(url)
        self.logger.debug('Send request index: {} skip: {} host: {} header:  {}'
                          .format(param['host_id'], x, parsed_url.hostname, param['headers']['Range']))

        try:
            resp = sess.get(verify=False, url=url, headers=param['headers'], timeout=10)

        except ConnectionResetError as e:
            print(str(e))
            self.logger.debug('Reset Connection host_id: {} host:: {}'.format(host_id, self._urls[host_id]))
            return self._re_request_new_session(host_id, param)

        except ParseError:
            self.logger.debug('ParserError')
            return self._re_request_new_session(host_id, param)

        except ValueError:
            self.logger.debug('ValueError')
            return self._re_request_new_session(host_id, param)

        except ConnectionError:
            self.logger.debug('Connection aborted')
            return self._re_request_new_session(host_id, param)

        except Timeout:
            self.logger.debug('Timeout')
            return self._re_request_other_session(host_id, param)

        self._used_params[param['host_id']] = param
        status = resp.status_code
        if status != 206:
            self.logger.debug('Failed {} status: {} host_id: {}'.format(self._urls[host_id], status, host_id))
            return self._re_request_other_session(host_id, param)

        content = resp.content
        range_header = resp.headers['Content-Range']
        order = get_order(range_header, self._split_size)
        self.logger.debug(msg='Received response order: {} header: {} from {}'
                          .format(order, range_header, parsed_url.hostname))

        self._host_ids.append(host_id)
        # random.shuffle(self._host_ids)
        self._url_received_counts[host_id] += 1

        self._exp_data.append({'time': time.monotonic() - self._begin_time, 'order': order})

        return order, content

    def _get_retransmission_index(self):
        index = 0
        for data in self._data:
            if data is None:
                return index
            else:
                index += 1

    def get_result(self):

        server_result = {}
        for url, count in zip(self._urls, self._url_received_counts):
            parsed_url = urlparse(url)
            server_result[parsed_url.hostname] = count

        if self._end_time is not None:
            thp = self._length * 8 / (self._end_time - self._begin_time) / 10 ** 6
        else:
            thp = 0

        if self.is_continue() is False:
            return {'exp_data': self._exp_data,
                    'server_result': server_result,
                    'return_block_num': self._return_block_num,
                    'accumulation': self._accumulation,
                    'thp': thp,
                    }

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
                    self._data[order] = content
                    del self._future_resp[i]
                    continue
                except TimeoutError:
                    i += 1
                except TypeError:
                    continue

        b = bytearray()
        i = self._received_index
        stack_count = 0
        return_count = 0
        byte_link_flag = True
        return_flag = False

        while i < len(self._data):
            if self._data[i] is None:
                byte_link_flag = False
            else:
                if byte_link_flag:
                    return_count += 1
                    b += self._data[i]
                    self._data[i] = b''
                    return_flag = True
                else:
                    stack_count += 1
            i += 1

        if return_flag:
            self._received_index += return_count
            len_b = len(b)
            self._return_block_num.append(return_count)
            self.logger.debug('Return blocks. bytes: {} return_count: {} stack_count: {}'
                              .format(len_b, return_count, stack_count))

            self._accumulation.append(stack_count)

        gc.collect()
        return b

    def is_continue(self):
        """
        :return bool: status of downloading
        """
        if self._received_index == self._request_num != 0:
            if self._end_time is None:
                self._end_time = time.monotonic()
            return False
        else:
            return True

    def close(self):
        self._executor.shutdown()
        gc.collect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
