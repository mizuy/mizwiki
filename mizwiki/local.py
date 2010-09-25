from werkzeug import Local, LocalManager
from werkzeug.routing import Map, Rule
from mizwiki import config

local = Local()
local_manager = LocalManager([local])
application = local('application')

import sqlobject as so
so.sqlhub.processConnection = so.connectionForURI('sqlite:' + config.cachedb)

