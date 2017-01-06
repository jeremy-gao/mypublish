#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
import bottle
import sys
import index

sys.path = ['/var/www/html/mypublish'] + sys.path
os.chdir(os.path.dirname(__file__))

application = index.myapp
