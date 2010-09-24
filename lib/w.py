# -*- coding:utf-8 mode:Python -*-

import config
import sqlobject as so
so.sqlhub.processConnection = so.connectionForURI('sqlite:' + config.cachedb)

import mapper
def handler(req):
  return mapper.start(req)
