#!/bin/sh

PYTHON=/usr/bin/python3.8
e=0

do_it () {
    url=$1
    $PYTHON httpclient.py GET $1 >/dev/null
    e=$?; if [ $e -ne 0 ]; then echo "ERR Failed GET $1"; fi
}

do_it 'http://example.com'
do_it 'http://www.cs.ualberta.ca/'
do_it 'http://softwareprocess.es/static/SoftwareProcess.es.html'
do_it 'http://c2.com/cgi/wiki?CommonLispHyperSpec'
do_it 'http://slashdot.org'
if [ $e -eq 0 ]; then echo "OK All pass"; fi
