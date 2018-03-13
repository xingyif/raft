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
    converts this request into a json format (presumably to be sent)
    @return String
    """
    def get_str(self):
        request_as_str = "%s %s %s\nHost: %s\n" % (self.request_type, self.path, self.version, self.host)
        #request_as_str += "Cookie: csrftoken=%s; sessionid=%s" % (self.token, self.session_id, self.data)
        request_as_str += "Cookie: csrftoken=%s\n" % (self.token)
        #request_as_str += "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/\n" 
        request_as_str += "\n\n%s" % self.data
        return request_as_str





class Response:

    def __init__(self, version, response_code, datetime, length):
	    self.version = version
	    self.response_code = response_code
	    self.datetime = datetime
	    self.length = length


class PageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.csrf = None
        self.urls = []
        self.session_id = None

    def handle_starttag(self, tag, attrs):
        for attr, val in attrs:
            pass
            #print("attr: " + str(attr))
            #print("val: " + str(val))

    def handle_endtag(self, tag):
        print("end tag: " + str(tag))

    def handle_data(self, data):
        print("Data: " + data)
        if "csrftoken" in data:
            self.csrf = data.split("csrftoken=")[1].split(";")[0]

        if "sessionid" in data:
            self.session_id = data.split("sessionid=")[1].split(";")[0]
            











