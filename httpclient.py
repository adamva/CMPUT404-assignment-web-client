#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# Copyright 2023 Adam Ahmed
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
import time
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, headers={}, body=""):
        self.code = code
        self.headers = headers
        self.body = body
    def get_code(self): return self.code
    def get_body(self): return self.body
    def get_headers(self): return self.headers

class HTTPClient(object):

    def __init__(self):
        self.error_code_messages = {
            1: 'Protocol %s not supported',
            3: 'URL using bad/illegal format or missing URL',
            6: 'Bad response from server',
            52: 'Empty reply from server'
        }

    def build_http_request(self, method='GET', version='1.1', path='/', headers={}, payload=''):
        """ Return a HTTP request string

        Parameters:
            method  (string): HTTP method type
            version (string): HTTP version
            path    (string): HTTP request path
            headers (dict):   Dictionary of HTTP request headers
            payload (string): String of request payload
        
        Returns:
            http_request (string): A HTTP request string
        """
        line_ending = '\r\n'
        # Create status line
        http_request = f'{method.upper()} {path} HTTP/{version}' + line_ending

        # Append headers
        for header in headers:
            http_request += f'{header}: {headers[header]}' + line_ending

        # Append headers if not done prior
        # Content-Length
        payload_length = len(payload.encode('utf-8'))
        if payload_length > 0:
            if not headers.get('Content-Length'):
                http_request += f'Content-Length: {payload_length}' + line_ending
            if not headers.get('Content-Type'):
                http_request += f'Content-Type: application/x-www-form-urlencoded' + line_ending
        # User-Agent
        if not headers.get('User-Agent'):
            http_request += 'User-Agent: badCurl/0.0.1' + line_ending
        # Accept
        if not headers.get('Accept'):
            http_request += 'Accept: */*' + line_ending

        # Append message body
        http_request += line_ending
        if payload:
            http_request += payload
        return http_request

    def check_url(self, urllib_parse):
        code = 0; message = ''
        if not urllib_parse.scheme:
            code = 3; message = self.error_code_messages[code]
        elif urllib_parse.scheme != 'http':
            code = 1; message = self.error_code_messages[code] % urllib_parse.scheme
        elif not urllib_parse.hostname:
            code = 3; message = self.error_code_messages[code]
        # Hostname should only be alphanumeric, dots, or hyphens
        elif len(urllib_parse.hostname) != len(re.match('[a-zA-Z0-9.-]+', urllib_parse.hostname).group()):
            code = 3; message = self.error_code_messages[code]

        if code != 0:
            return (code, message)

    def get_path(self, url):
        path = '/'
        url_arr = url.split('/') # ['http', '', 'localhost:8080', 'index.html']
        if len(url_arr) > 3:
            path += '/'.join(url_arr[3:])
        
        # TODO Check if path is not set
        return path

    def get_line_ending(self, string):
        line_ending = ''
        if string.find('\r\n') != -1:
            line_ending = '\r\n'
        elif string.find('\n') != -1:
            line_ending = '\n'
        elif string.find('\r') != -1:
            line_ending = '\r'
        # TODO if line_ending is still empty, then raise error
        return line_ending

    def connect(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
        except socket.error as e:
            raise            
        return None

    def get_code(self, data):
        """ Return HTTP code from HTTP reponse data

        Parameters:
            data (string): A HTTP response string

        Returns:
            code (int): An int of the HTTP response code
        """
        code = -1; code_raw = ''

        # Split the response status line goodies
        line_ending = self.get_line_ending(data)
        status_line_end_index = data.find(line_ending)
        status_line = data[0:status_line_end_index]
        split_status_line = status_line.split(' ') # ['HTTP/1.0', '200', 'OK']
        # Check parse array gave minimum values
        if len(split_status_line) >= 2: 
            code_raw = split_status_line[1]
        else:
            raise Exception('Could not find status code in response status line')
        
        # Code comes as string so make it an int
        try:
            code = int(code_raw)
        except ValueError as e:
            raise

        if code < 100 or code > 599:
            raise ValueError(f'Response code is out of range {code}')

        return code

    def get_headers(self, data):
        """ Return HTTP headers from HTTP reponse data

        Parameters:
            data (string): A HTTP response string

        Returns:
            headers (dict): An dict of the HTTP headers key value pairs
        """
        headers = {}
        # Split headers on newline and double newline cadence
        line_ending = self.get_line_ending(data)
        status_line_end_index = data.find(line_ending)
        message_body_start_index = data.find(line_ending+line_ending)
        if status_line_end_index <= -1 or message_body_start_index <= -1:
            raise ValueError('Response headers are malformed or missing')
        else:
            status_line_end_index += len(line_ending)
        
        headers_data = data[status_line_end_index:message_body_start_index]
        headers_array = headers_data.split(line_ending)
        for header in headers_array:
            header_array = header.split(': ') # ['Content-Length', '1234']
            # Assign key value pair to dict
            headers[header_array[0]] = header_array[1]
        return headers

    def get_body(self, data):
        """ Return HTTP message body from HTTP reponse data

        Parameters:
            data (string): A HTTP response string

        Returns:
            message_body (string): An string of the HTTP message body
        """
        message_body = ''
        line_ending = self.get_line_ending(data)
        message_body_start_index = data.find(line_ending+line_ending)
        if message_body_start_index <= -1:
            raise ValueError('Could not determine response body')
        else:
            # Skip the first two newlines
            message_body_start_index += len(line_ending)*2
        message_body = data[message_body_start_index:]
        return message_body
    
    def sendall(self, data):
        try:
            self.socket.sendall(data.encode('utf-8'))
        except socket.error as e:
            raise
        return None

    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def do_request(self, method, url, args=None):
        code = 500; body = ""; headers = {}
        # Build HTTP request body
        # Validate input URL params
        try:
            url_parse = urllib.parse.urlparse(url)
        except AttributeError as e:
            print(f'badCurl: ({e.errno}) {e.strerror}')
            sys.exit(e.errno)

        url_check = self.check_url(url_parse)
        if url_check:
            print(f'badCurl: ({url_check[0]}) {url_check[1]}')
            sys.exit(url_check[0])

        server_host = url_parse.hostname
        server_port = url_parse.port if url_parse.port else 80
        request_headers = {
            'Host': server_host,
            'Content-Length': 0,
            'Content-Type': 'application/octet-stream'
        }
    
        request_path =  '/'
        if url_parse.path:
            request_path = url_parse.path + '?' + url_parse.query

        # URL encode a payload if given
        request_payload = ''
        if args:
            request_payload = urllib.parse.urlencode(args)
            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if method == 'POST':
            request_headers['Content-Length'] = len(request_payload.encode('utf-8'))

        http_request_data = self.build_http_request(method=method, path=request_path, headers=request_headers, payload=request_payload)
        # print(repr(http_request_data)) # print literal string chars

        # Connect & send request
        try:
            self.connect(server_host, server_port)
            self.sendall(http_request_data)
            time.sleep(150/1000) # Was getting an empty reply from server if I did not wait after sending HTTP request 
            self.socket.shutdown(socket.SHUT_WR)
        except Exception as e:
            print('badCurl: (1)', e)
            self.socket.close()
            sys.exit(1)
        
        # Read response
        http_response_data = self.recvall(self.socket)
        if not http_response_data:
            print('badCurl: (52) ' + self.error_code_messages[52])
        elif not http_response_data.startswith('HTTP'):
            print('badCurl: (6) ' + self.error_code_messages[6])
        else:
            try:
                code = self.get_code(http_response_data)
                headers = self.get_headers(http_response_data)
                body = self.get_body(http_response_data)
            except Exception as e:
                print('badCurl: (1)', e)

        self.socket.close()
        return HTTPResponse(code, headers, body)

    def GET(self, url, args=None):
        return self.do_request('GET', url, args)

    def POST(self, url, args=None):
        return self.do_request('POST', url, args)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    http_rsp = None
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        http_rsp = client.command( sys.argv[2], sys.argv[1] )
    else:
        http_rsp = client.command( sys.argv[1] )
    # print("RSP Code:", http_rsp.get_code())
    # print("RSP Headers:", http_rsp.get_headers())
    # if len(http_rsp.get_body()) < 64:
    if http_rsp.get_body():
        print(http_rsp.get_body())
    

