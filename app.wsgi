#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
import bottle
import sys

workdir = os.path.dirname(__file__)
sys.path = [workdir] + sys.path
os.chdir(workdir)
bottle.TEMPLATE_PATH.insert(0, workdir + '/views/')

import index

application = index.myapp
