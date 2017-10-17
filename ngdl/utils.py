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
    tmp = range_header.split(b' ')
    tmp = tmp[1].split(b'/')
    tmp = tmp[0].split(b'-')
    order = int(tmp[0]) // split_size
    return order

