from hyper import HTTPConnection

if __name__ == '__main__':
    conn = HTTPConnection(host='165.242.111.93', port=8080)
    conn.request('HEAD', url='/index.html')
    resp = conn.get_response()
    print(resp.headers)
