# -*- coding:utf-8 mode:Python -*-

import config
import sqlobject as so
so.sqlhub.processConnection = so.connectionForURI('sqlite:' + config.cachedb)

import handler as h
def handler(req):
  return h.handler(req)
