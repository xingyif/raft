#!/usr/bin/python
import gzip
import socket
import sys
from HTMLParser import HTMLParser
from StringIO import StringIO
from urlparse import urlparse

import time

import zlib

USERNAME = '' #"1778409"
PASSWORD = '' #"ZUE3UDQE"

fakebook_url = urlparse('http://fring.ccs.neu.edu/fakebook/')
login_url = urlparse('http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/')
full_login_path = "/accounts/login/?next=/fakebook/"
HOST = fakebook_url.netloc
# fakebook_url.netloc fring.ccs.neu.edu
FAKEBOOK_PATH = fakebook_url.path
LOGIN_PATH = login_url.path
HTTP_VERSION = "HTTP/1.1"

PORT = 80
HOST_PORT = (HOST, PORT)

paths_visited = set()
paths_tovisit = set()
secret_flags = set()

csrf = ''
session_id = ''

# secret_flags_file = open('secret_flags', 'w')

class PageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.secret_flag_found = False

    def handle_starttag(self, tag, attrs):
        global paths_visited, paths_tovisit, secret_flags
        # find links in the page
        if tag == 'a':
            for attr, val in attrs:
                if attr == 'href':
                    # only add to tovisit list if the url has not been visited
                    # doesn't exist in tovisit list already, and it's valid
                    val_path = urlparse(val).path
                    if val_path not in paths_visited and val_path not in paths_tovisit and val.startswith('/fakebook/'):
                        #print("found: %s" % val_path)
                        paths_tovisit.add(val_path)
                        #print("add a new valid url to visit: %s" % val_path)
        # find secret flag
        if tag == 'h2':
            for attr, val in attrs:
                if attr == 'class' and val == 'secret_flag':
                    self.secret_flag_found = True


    def handle_endtag(self, tag):
        if tag == "html":
            pass

    def handle_data(self, data):
        global secret_flags, csrf, session_id
        if "csrftoken" in data:
            csrf = data.split("csrftoken=")[1].split(";")[0]

        if "sessionid" in data:
            session_id = data.split("sessionid=")[1].split(";")[0]

        # if self.secret_flag_found:
        #     flag = data.split(" ")[1]
        #     if flag not in secret_flags:
        #         secret_flags.append(flag)
        #         self.secret_flag_found = False
        #         # print("appended text", file=secret_flags_file)
        #         with open('secert_flags', 'a') as secret_flags_file:
        #             secret_flags_file.write(str(flag) + '\n')
        # found a new flag, print it TODO check length?
        if 'FLAG:' in data: # FLAG: 64-characters-of-random-alphanumerics
            flag = data.split(" ")[1] #flag = data.split('FLAG:')[1].split('</h2>')[0]
            secret_flags.add(flag)
            print(flag)
            print('Flag length: %d' % len(flag))


# parser = PageParser()


"""
receive HTTP responses using the socket
"""
def recv_response(sock, timeout=0.5):

    # full_response = ''
    # print(sock.gettimeout())
    # full_response += sock.recv(9000)
    # print(sock.gettimeout())
    # print("in recv_response")
    # cur_time = time.time()
    # deadline = cur_time + timeout
    # while '</html>' not in full_response:
    #     # socket should time out if it exceeds deadline
    #     if time.time() > deadline:
    #         print("break out")
    #         break
    #     sock.settimeout(deadline - time.time())
    #     resp = sock.recv(9000)
    #     print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~in while, before set timeout\n\n\n\n\n\n\n") # TODO only print this when timeout=1
    #     if resp:
    #         print("add rep to full_response")
    #         full_response += resp
    #
    # sock.close()
    # return full_response
    data_buffer = ''
    sock.settimeout(timeout)
    while True:
        try:
            data = sock.recv(9000)

            if not data:
                break

            data_buffer += data
        except:
            break
    sock.close() #TODO retry
    return data_buffer


"""
    handle returned status codes
    200 - accepted
    301 - moved permanently. try the request again using the new URL given by the server in the Location header.
    403 - Forbidden
    404 - Not Found
     Our web server may return these codes in order to trip up your crawler.
     In this case, your crawler should abandon the URL that generated the error code.
    500 - Internal Server Error
     Our web server may randomly return this error code to your crawler.
     In this case, your crawler should re-try the request for the URL until the request is successful.
"""

def handle_http_status_codes(response, path):
    global paths_visited, paths_tovisit
    try:
        status_code = response.split(' ')[1]
    except:
        print(response)
        print(path)
        return '404'
        # print(str(status_code))
    if status_code == '200':
        pass
    elif status_code == '301' or status_code == '302':
        new_path = urlparse(response.split('Location: ')[1].split('\r\n')[0]).path
        # add the new_path to visit
        if new_path not in paths_tovisit and new_path not in paths_visited:
            paths_tovisit.add(new_path)
        # add current path to already visited list
        if path not in paths_visited:
            paths_visited.add(path)
        # removed path from to visit list
        if path in paths_tovisit:
            paths_tovisit.remove(path)
        # TODO make get (cookie) request again
        # TODO remove url from tovisit, add to visited
    elif status_code == '403' or status_code == '404':
        # drop path
        if path in paths_tovisit:
            paths_tovisit.remove(path)
        if path not in paths_visited:
            paths_visited.add(path)
    elif status_code == '500':
        # try to GET the same page again
        # response = cookie_GET(path)
        # handle_http_status_codes(response, path)
        if path not in paths_tovisit:
            paths_tovisit.add(path)
    return status_code


"""
    HTTP GET request
"""
def login_GET(path):
    global HOST_PORT, HOST, HTTP_VERSION
    # construct GET request
    request = "GET %s %s\nHost: %s\n\n" % (path, HTTP_VERSION, HOST)
    #print('==========================GET Request======================')
    #print(request_as_str)

    # send GET request
    # create the socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to the socket
        sock.connect(HOST_PORT)
        sock.sendall(request)
        # get response
        response = recv_response(sock)
        return response
    except socket.error as e:
        print 'ERROR: Failed to create socket! %s' % e
        exit(1)


"""
    HTTP GET request with the cookie
"""
def cookie_GET(path):
    global session_id, csrf, HOST_PORT, HOST, HTTP_VERSION
    request = '''\
GET %s %s
Host: %s
Cookie: csrftoken=%s; sessionid=%s

''' % (path, HTTP_VERSION, HOST, csrf, session_id)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to the socket
        sock.connect(HOST_PORT)
        sock.sendall(request)
        response = recv_response(sock)
        # decompressed_content = ''
        #
        # if 'gzip' in response:
        #     decompressed_content = zlib.decompress(response, 16+zlib.MAX_WBITS) # gzip.GzipFile(fileobj=StringIO(response)).read()
        #     print(decompressed_content)
        # print(response)
        return response
    except socket.error as e:
        print 'ERROR: Failed to create socket! %s' % e
        exit(1)


"""
    HTTP POST request
"""
def login_POST(path):
    global HOST_PORT, HTTP_VERSION, HOST, session_id, csrf
    data = "username=%s&password=%s&csrfmiddlewaretoken=%s&next=%%2Ffakebook%%2F" % (USERNAME, PASSWORD, csrf)
    request = '''\
POST %s %s
Host: %s
Content-Length: %d
Cookie: csrftoken=%s; sessionid=%s

%s
''' % (path, HTTP_VERSION, HOST, len(data), csrf, session_id, data)
    #print '==========================POST Request======================'
    #print(request_as_str)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to the socket
        sock.connect(HOST_PORT)
        sock.sendall(request)
        response = recv_response(sock)
        return response
    except socket.error as e:
        print 'ERROR: Failed to create socket! %s' %e
        exit(1)



"""
Logging in to fakebook, HTTP POST
1. initial GET request
2. POST with csrf tocken and sessionid
3. get new session id
4. GET with new session id
"""
def login(path):
    global LOGIN_PATH, HOST, USERNAME, PASSWORD, HOST_PORT, csrf, session_id
    # initial GET request and GET response
    get_response = login_GET(path)
    #print '---------------------------GET Response---------------------'
    #print(get_response)
    # TODO check status, but only quit if 404, rest recall
    get_status_code = handle_http_status_codes(get_response, full_login_path)
    if get_status_code == '200':
        crawl_webpage(get_response)
    elif get_status_code == '302':
        # retry using the redirected path
        login(paths_tovisit[0])
    elif get_status_code == '500':
        # retry using the same path
        login(path)
    else:
        print"First GET failed, cannot find the given path, exit the program"
        exit(1)

    # POST with the session id and token
    post_response = login_POST(LOGIN_PATH)
    # renew token
    crawl_webpage(post_response)
    post_status_code = handle_http_status_codes(post_response, LOGIN_PATH)
    if post_status_code == '200':
        if '<a href="/accounts/login/">Log in</a>' in post_response:
            print("Given Username and Password incorrect! Please retry")
            exit(1)



"""
crawls the webpage: find new links to visit and find flags
csrf token and session id should be updated
"""
def crawl_webpage(response):
    parser = PageParser()
    parser.feed(response)



"""
TODO chunks:
check flag length when add to flags_list
if not 64, then chunked = True, add initial part of the next response
in handle_end_tag, if chunked = True

# only craw the pages that are valid, starts with fring.ccs.neu.edu
"""
def main():
    global USERNAME, PASSWORD, full_login_path

    # if given incorrect input argument, then quit
    if len(sys.argv) < 3:
        print("Please input Username and Password for logging into fakebook!")
        exit(1)
    # takes input username and password
    USERNAME = sys.argv[1]
    PASSWORD = sys.argv[2]
    # login into fakebook
    login(full_login_path)

    while len(paths_tovisit) > 0 and len(secret_flags) < 5:
        # crawl all links found
        for cur_path in list(paths_tovisit):
            # found all flags
            if len(secret_flags) >= 5:
                break

            # if the current url hasn't been visited yet, then crawl it
            if cur_path not in paths_visited:
                # print("traversing: %s" % cur_path)
                # GET and crawl webpage
                response = cookie_GET(cur_path)
                status_code = handle_http_status_codes(response, cur_path)
                if status_code == '200':
                    crawl_webpage(response)
                    # add path to list of path already visited
                    if cur_path not in paths_visited:
                        paths_visited.add(cur_path)
                    # remove path from to visit list of paths
                    if cur_path in paths_tovisit:
                        paths_tovisit.remove(cur_path)

    # exit gracefully when found all flags
    exit(0)


if __name__ == "__main__":
    main()


