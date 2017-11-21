import pstats

if __name__ == '__main__':
    p = pstats.Stats('ngdl.profile')
    p.sort_stats('cumtime')
    p.print_stats()
