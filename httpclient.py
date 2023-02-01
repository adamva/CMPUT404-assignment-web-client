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
    def serialize(self, data):
        """ Return a string representation of Python dict

        Parameters:
            data (dict): Dictionary of data to serialize
        
        Returns:
            data_string (string): A string representation of dict
        """
        data_string = urllib.parse.urlencode(data)
        return data_string

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
        if not headers.get('Host'):
            print("TODO ERROR")
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

    def get_host_port(self, url):
        """ Return the hostname and port from a URL string

        Parameters:
            url (string): A HTTP URL string
        
        Returns:
            (host, port) (tuple): A tuple containing the host and port
        """
        port = -1
        host = ''
        # Check URL for hostname and optional port
        url_arr = url.split('/') # ['http', '', 'localhost:8080', 'index.html']
        if len(url_arr) > 2:
            host_port = url_arr[2] 
            host_port_arr = host_port.split(':') # ['localhost', '8080']
            if len(host_port_arr) > 1:
                port = int(host_port_arr[1])
            host = host_port_arr[0]
    
        # HTTP schemes have standard ports
        if port == -1:
            if url.startswith('http:'):
                port = 80
            # TODO Raise exception for https attempts
            # elif url.startswith('https:'):
                # port = 443

        # TODO Check if host or port still are not set
        return (host, port)

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
            raise e
        return None

    def get_code(self, data):
        """ Return HTTP code from HTTP reponse data

        Parameters:
            data (string): A HTTP response string

        Returns:
            code (int): An int of the HTTP response code
        """
        code = -1
        code_raw = ''
        line_ending = self.get_line_ending(data)
        status_line_end_index = data.find(line_ending)
        status_line = data[0:status_line_end_index]
        split_status_line = status_line.split(' ') # ['HTTP/1.0', '200', 'OK']
        if len(split_status_line) >= 2: 
            code_raw = split_status_line[1]
        else:
            raise Exception('ERR Response status line is malformed, could not find status code')
        try:
            code = int(code_raw)
        except Exception as e:
            raise Exception('ERR Response code is not a number')
        if code < 100 or code > 599:
            raise Exception('ERR Response code is not valid <100 or >599')

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
            print("TODO ERROR")
            # TODO raise an error
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
        # TODO if either index is <=-1 than HTTP reponse is wrong
        if message_body_start_index <= -1:
            print("TODO ERROR")
            # TODO raise an error
        else:
            message_body_start_index += len(line_ending)*2
        message_body = data[message_body_start_index:-1]
        return message_body
    
    def sendall(self, data):
        try:
            self.socket.sendall(data.encode('utf-8'))
        except socket.error as e:
            raise e
        return None
        
    def close(self):
        self.socket.close()

    # read everything from the socket
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

    def GET(self, url, args=None):
        code = 500
        body = ""
        headers = {}
        # Build HTTP request body
        server_host, server_port = self.get_host_port(url)
        request_path = self.get_path(url)
        # GET / HTTP/1.1\nHost: localhost\n\n
        req_headers = {'Host': server_host}
        http_request_data = self.build_http_request(path=request_path, headers=req_headers)
        # Connect & send request
        self.connect(server_host, server_port)
        self.sendall(http_request_data)
        time.sleep(150/1000) # Without this sleep wait, the connection becomes closed too quick before server can recognize what is happening and not give an actual HTTP reponse
        self.socket.shutdown(socket.SHUT_WR)
        
        # Read response
        http_response_data = self.recvall(self.socket)
        if http_response_data and http_response_data.startswith('HTTP'):
            code = self.get_code(http_response_data)
            headers = self.get_headers(http_response_data)
            body = self.get_body(http_response_data)
        else:
            print("ERR Empty or not-HTTP reply from server")

        self.close()
        return HTTPResponse(code, headers, body)

    def POST(self, url, args=None):
        code = 500
        body = ""
        headers = {}
        # Build HTTP request body
        server_host, server_port = self.get_host_port(url)
        request_path = self.get_path(url)
        request_headers = {'Host': server_host}
        request_payload = ''
        if args:
            request_payload = self.serialize(args)
        request_headers['Content-Length'] = len(request_payload.encode('utf-8'))
        request_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        http_request_data = self.build_http_request(method='POST', path=request_path, headers=request_headers, payload=request_payload)
        # Connect & send request
        self.connect(server_host, server_port)
        self.sendall(http_request_data)
        time.sleep(150/1000) # Without this sleep wait, the connection becomes closed too quick before server can recognize what is happening and not give an actual HTTP reponse
        self.socket.shutdown(socket.SHUT_WR)
        
        # Read response
        http_response_data = self.recvall(self.socket)
        if http_response_data and http_response_data.startswith('HTTP'):
            code = self.get_code(http_response_data)
            headers = self.get_headers(http_response_data)
            body = self.get_body(http_response_data)
        else:
            print("ERR Empty or not-HTTP reply from server")

        self.close()
        return HTTPResponse(code, headers, body)

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
    print(http_rsp.get_body())
    

