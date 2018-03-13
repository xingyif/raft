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
    
    """
    constructs a post request
    @return String
    """
    def post_request(self):
        request_as_str = "%s %s %s\nHost: %s\n" % (self.request_type, self.path, self.version, self.host)
        #request_as_str += "Cookie: csrftoken=%s; sessionid=%s" % (self.token, self.session_id, self.data)
        request_as_str += "Cookie: csrftoken=%s;sessionid=%s\n\n" % (self.token, self.session_id)
        #request_as_str += "Referer: http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/\n" 
        request_as_str += "%s&next=/fakebook/" % self.data
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
        self.urls_visited = []
        self.urls_tovisit = []
        self.session_id = None
        self.secret_flag_found = False
        self.secret_flags = []

    def handle_starttag(self, tag, attrs):
        # find links in the page
        if tag == 'a':
            for attr, val in attrs:
                if attr == 'href':
                    # only add to tovisit list if the url has not been visited
                    # doesn't exist in tovisit list already, and it's valid
                    if val not in urls_visited && val not in urls_tovisit && if "fring.ccs.neu.edu" in val:
                        urls_tovisit.append(val)
                        print("add a new valid url to visit: %s" % val)
        # find secret flag
        if tag == 'h2':
            for attr, val in attrs:
                if attr == 'class' && val == 'secret_flag':
                    secret_flag = True



    def handle_endtag(self, tag):
        #print("end tag: " + str(tag))
        pass

    def handle_data(self, data):
        #print("Data: " + data)
        if "csrftoken" in data:
            self.csrf = data.split("csrftoken=")[1].split(";")[0]

        if "sessionid" in data:
            self.session_id = data.split("sessionid=")[1].split(";")[0]

        if secret_flag:
            flag = data.split(" ")[1]
            if flag not in secret_flags:
                secret_flags.append(flag)
                secret_flag_found = False
                print "found one secret flag %s" % str(flag)

            











