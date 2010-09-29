from werkzeug import Local, LocalManager
from werkzeug.routing import Map, Rule
from mizwiki import config

local = Local()
local_manager = LocalManager([local])
application = local('application')

from sqlalchemy import MetaData
from sqlalchemy.orm import create_session, scoped_session

metadata = MetaData()
session = scoped_session(lambda: create_session(application.database_engine,
                         autocommit=False, autoflush=False),
                         local_manager.get_ident)
