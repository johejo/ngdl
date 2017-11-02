# ngdl
HTTP/2 parallel downloading client for Python

## Description
An HTTP/2 client module for easy downloading contents.  
Perform parallel download using HTTP / 2 stream, Range Request, multi-threading.  
It is possible to use the aligned part as a byte string even during downloading.  
It is also possible to acquire files from multiple servers.

## Install
```bash
$ pip instal ngdl
```

## Example

```python
from ngdl import Downloader

if __name__ == '__main__':

    urls = ['http://www.ftp.ne.jp/Linux/packages/ubuntu/releases-cd/17.04/ubuntu-17.04-server-amd64.iso',  # KDDI
            'http://ubuntutym2.u-toyama.ac.jp/ubuntu/17.04/ubuntu-17.04-server-amd64.iso',  # toyama
            'http://ftp.riken.go.jp/Linux/ubuntu-releases/17.04/ubuntu-17.04-server-amd64.iso',  # riken
            'http://ftp.jaist.ac.jp/pub/Linux/ubuntu-releases/17.04/ubuntu-17.04-server-amd64.iso',  # jaist
            'http://ftp.yz.yamagata-u.ac.jp/pub/linux/ubuntu/releases/17.04/ubuntu-17.04-server-amd64.iso',  # yamagata
            ]

    filename = 'ubuntu-17.04-server-amd64.iso'

    with open(filename, 'wb') as f:
        pass

    with open(filename, 'ab') as f:
        with Downloader(urls=urls, split_size=1000000) as dl:
            while dl.is_continue():
                b = dl.get_bytes()
                f.write(b)
```


