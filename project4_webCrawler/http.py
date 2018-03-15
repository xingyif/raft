#!/usr/bin/python -u

import json

from HTMLParser import HTMLParser


class Request:
    
    def __init__(self, request_type, path, version, host, data="", token="", session_id=""):
        self.request_type = request_type
        self.path = path
        self.version = version
        self.host = host
        self.data = data
        self.token = token
        self.session_id = session_id


    """
    constructs a get request
    @return String - the constructed request
    """
    def get_request(self):
        request_as_str = "%s %s %s\nHost: %s" % (self.request_type, self.path, self.version, self.host)
        # request_as_str += "Cookie: csrftoken=%s; sessionid=%s\n\n&next=/fakebook/" % (self.token, self.session_id)
        print "-----------------initial request-----------"
        print request_as_str
        return request_as_str
    
    """
    constructs a get request with the session id
    @return string - the constructed request
    """
    def get_request_with_cookie(self):
        print "-----------------GET Request with Cookie-----------"
        # print request_as_str
        request_as_str = '''\
GET %s %s
Host: %s
Content-Length: %d
Cookie: csrftoken=%s; sessionid=%s

''' % (self.path, self.version, self.host, len(self.data), self.token, self.session_id)
        return request_as_str
    
    
    """
    constructs a post request
    @return String - the constructed request
    """
    def post_request(self):
        request_as_str = '''\
POST %s %s
Host: %s
Content-Length: %d
Cookie: csrftoken=%s; sessionid=%s

%s
''' % (self.path, self.version, self.host, len(self.data), self.token, self.session_id, self.data)
        return request_as_str






