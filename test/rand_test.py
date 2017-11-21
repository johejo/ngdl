from ngdl import Downloader

if __name__ == '__main__':
    urls0 = ['http://165.242.111.92/ubuntu-17.10-server-i386.template',
             'http://165.242.111.93/ubuntu-17.10-server-i386.template'
             ]

    urls3 = [
        'http://www.ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.10/ubuntu-17.10-server-i386.template',  # KDDI
        'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.10/ubuntu-17.10-server-i386.template',  # toyama
        'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # riken
        'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.10/ubuntu-17.10-server-i386.template',  # jaist
        'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.10/ubuntu-17.10-server-i386.template'  # yamagata
    ]

    target = 4

    with Downloader(urls=urls0+urls3,
                    split_size=1000000,
                    parallel_num=1
                    ) as dl:
        dl._set_bad_url(target)
        for i in range(100):
            x = dl._get_randrange()
            assert x != target
