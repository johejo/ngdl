from ngdl import Downloader
import argparse
import sys

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print('rangedl: try \'rangedl -h\'', file=sys.stderr)
        exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('URLs', nargs='*', help='target URLs')
    parser.add_argument('-n', '--num', nargs='?', default=5, const=5, help='num of TCP connection', type=int)
    parser.add_argument('-s', '--size', nargs='?', default=0, const=0, help='split size (MB)', type=int)
    parser.add_argument('-sk', '--size-kb', nargs='?', default=0, const=0, help='split size (KB)', type=int)
    parser.add_argument('-sg', '--size-gb', nargs='?', default=0, const=0, help='split size (GB)', type=int)
    parser.add_argument('-p', '--non-progress', action='store_false', help='disable progress bar using \'tqdm\'')
    parser.add_argument('-d', '--debug', action='store_true', help='debug option')
    args = parser.parse_args()

    split_size = (args.size * 1000 + args.size_kb + args.size_gb * 1000 * 1000) * 1000
    if split_size == 0:
        split_size = 1000 * 1000
    d = Downloader(urls=args.URLs,
                   parallel_num=args.num,
                   split_size=split_size,
                   )
    d.test_download()
