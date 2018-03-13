#!/usr/bin/python -u

import json


class Request:
    
    def __init__(self, request_type, path, version, host, data=""):
        self.request_type = request_type
        self.path = path
        self.version = version
        self.host = host
	self.data = data
    
    """
    converts this request into a json format (presumably to be sent)
    @return String
    """
    def get_str(self):
        request_as_str = "%s %s %s\nHost: %s\n\n%s" % (self.request_type, self.path, self.version, self.host, self.data)
	return request_as_str





class Response:

    def __init__(self, version, response_code, datetime, length):
	self.version = version
	self.response_code = response_code
	self.datetime = datetime
	self.length = length
