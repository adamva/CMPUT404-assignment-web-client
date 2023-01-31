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
            path += url_arr[3]
        
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
        status_line_end_index = data.find('\n')
        status_line = data[0:status_line_end_index]
        split_status_line = status_line.split(' ') # ['HTTP/1.0', '200', 'OK']
        if len(split_status_line) >= 2: 
            code = split_status_line[1]
        else:
            raise Exception('ERR Response status line is malformed')
        # TODO check if response code is out of band (<100 or >599)
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
        status_line_end_index = data.find(line_ending) + len(line_ending)
        message_body_start_index = data.find(line_ending+line_ending)
        # TODO if either index is <=0 than HTTP reponse is wrong
        
        headers_data = data[status_line_end_index:message_body_start_index]
        headers_array = headers_data.split(line_ending)
        for header in headers_array:
            header_array = header.split(': ') # ['Content-Length', '1234']
            # Assign key value pair to dict
            headers[header_array[0]] = header_array[1]
        return headers

    def get_body(self, data):
        return None
    
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
        # Build HTTP request body
        server_host, server_port = self.get_host_port(url)
        request_path = self.get_path(url)
        # GET / HTTP/1.1\nHost: localhost\n\n
        http_request_data = 'GET ' + request_path + ' HTTP/1.0\nHost: ' + server_host + '\n\n'

        # Connect & send request
        self.connect(server_host, server_port)
        self.sendall(http_request_data)
        self.socket.shutdown(socket.SHUT_WR)
        
        # Read response
        # TODO Response is empty when trying www.google.com
        http_response_data = self.recvall(self.socket)
        # TODO Break out if response does not start with HTTP
        code = self.get_code(http_response_data)
        headers = self.get_headers(http_response_data)
        body = self.get_body(http_response_data)

        self.close()
        return HTTPResponse(code, headers, body)

    def POST(self, url, args=None):
        code = 500
        body = ""

        self.close()
        return HTTPResponse(code, body)

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
    print("RSP Code:", http_rsp.get_code())
    print("RSP Headers:", http_rsp.get_headers())
    print("RSP Body:", http_rsp.get_body())
    

