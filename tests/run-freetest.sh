#!/bin/sh

PYTHON=/usr/bin/python3.8*

$PYTHON freetests.py
e=$?; if [ $e -ne 0 ]; then echo "ERR Failed freetests.py"; fi
