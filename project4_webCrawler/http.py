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
    @return String
    """
    def get_request(self):
        request_as_str = "%s %s %s\nHost: %s\n\n" % (self.request_type, self.path, self.version, self.host)
        # request_as_str += "Cookie: csrftoken=%s; sessionid=%s\n\n&next=/fakebook/" % (self.token, self.session_id)
        print "-----------------initial request-----------"
        print request_as_str
        return request_as_str
    
    def get_2nd_request(self, token, session_id):
        # request_as_str = "%s %s %s\nHost: %s\n\n" % (self.request_type, self.path, self.version, self.host)
        # request_as_str += "Cookie: csrftoken=%s; sessionid=%s\n\n&next=/fakebook/" % (self.token, self.session_id)
        print "-----------------initial request-----------"
        # print request_as_str
        request_as_str = '''\
GET /fakebook/ HTTP/1.1
Host: fring.ccs.neu.edu
Content-Length: 108
Cookie: csrftoken=%s; sessionid=%s

''' % (token, session_id)
        return request_as_str
    """
    constructs a post request
    @return String
    """
    def post_request(self, token, session_id):
        # request_as_str = "%s %s %s\nHost: %s\n" % (self.request_type, self.path, self.version, self.host)
        # #request_as_str += "Cookie: csrftoken=%s; sessionid=%s" % (self.token, self.session_id, self.data)
        # request_as_str += "Cookie: csrftoken=%s;sessionid=%s\n\n" % (self.token, self.session_id)
        # #request_as_str += "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/\n" 
        # request_as_str += "%s&next=%%2Ffakebook%%2F" % self.data
        request_as_str = '''\
POST /accounts/login/ HTTP/1.1
Host: fring.ccs.neu.edu
Content-Length: 108
Cookie: csrftoken=%s; sessionid=%s

username=1778409&password=ZUE3UDQE&csrfmiddlewaretoken=%s&next=%%2Ffakebook%%2F
''' % (token, session_id, token)
        return request_as_str





class Response:

    def __init__(self, version, response_code, datetime, length):
	    self.version = version
	    self.response_code = response_code
	    self.datetime = datetime
	    self.length = length












