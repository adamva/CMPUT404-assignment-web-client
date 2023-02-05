#!/bin/sh

PYTHON=/usr/bin/python3.8

do_it () {
    url=$1
    $PYTHON httpclient.py GET "$1" > /dev/null
    e=$?; if [ $e -eq 0 ]; then echo "ERR GET on $1 worked"; fi
}

do_it ''
do_it 'error'
do_it 'https://www.example.com/'
do_it 'http//www.example.com/'
do_it 'http:/www.example.com/'
do_it 'http:www.example.com/'
do_it 'http:///'
do_it 'http://www.exampl%2Fe.com/'
do_it 'http://www.exampl&e.com/'
do_it 'http://www.exampl*e.com/'
do_it 'http://www.example.com:10000000/'
do_it 'http://www.example.com:foobar/'
do_it 'http://www.example.cooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooom/'
do_it 'http://www.example.com/foo /bar'
echo "All Pass"
