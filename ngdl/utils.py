import os
import signal


def map_all(es):
    """
    :param es: list
    :return: bool
    """
    return all([e == es[0] for e in es[1:]]) if es else False


def get_order(range_header, split_size):
    """

    :param range_header: bytes
    :param split_size: int
    :return:
    """
    tmp = range_header.split(' ')
    tmp = tmp[1].split('/')
    tmp = tmp[0].split('-')
    order = int(tmp[0]) // split_size
    return order


def kill_all():
    os.kill(os.getpid(), signal.SIGKILL)
