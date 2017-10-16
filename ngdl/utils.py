def map_all(es):
    """
    :param es: list
    :return: bool
    """
    return all([e == es[0] for e in es[1:]]) if es else False
