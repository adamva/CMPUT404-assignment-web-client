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
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body
    def get_body(self): return self.body
    def get_code(self): return self.code

class HTTPClient(object):
    def get_host_port(self, url):
        """ Return the hostname and port from a URL string

        Parameters:
            url (string): A HTTP URL string
        
        Returns:
            (host, port) (tuple): A tuple containing the host and port
        """
        port = 0
        host = ''
        # Check URL for hostname and optional port
        url_arr = url.split('/') # ['http', '', 'localhost:8080', 'index.html']
        if len(url_arr) > 2:
            host_port = url_arr[2] 
            host_port_arr = host_port.split(':') # ['localhost', '8080']
            if len(host_port_arr) > 1:
                port = host_port_arr[1]
            host = host_port_arr[0]
    
        # HTTP schemes have standard ports
        if port == 0:
            if url.startswith('http:'):
                port = 80
            elif url.startswith('https:'):
                port = 443

        # TODO Check if host or port still are not set
        return (host, port)

    def connect(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
        except socket.error as e:
            raise e
        return None

    def get_code(self, data):
        return None

    def get_headers(self,data):
        return None

    def get_body(self, data):
        return None
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
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
        server_host, server_port = self.get_host_port(url)
        self.connect(server_host, server_port)
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""
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
    print(http_rsp.get_body())
    

