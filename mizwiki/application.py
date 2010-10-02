from sqlalchemy import create_engine
from werkzeug import ClosingIterator, exceptions

import os,sys
root = os.path.join(os.path.dirname(__file__),'..')
sys.path.insert(0, root)

from mizwiki.local import local, local_manager, metadata, session
from mizwiki import config, models, controllers

import re
re_invalidchars = re.compile(r'[^\w_./+\-]',re.U)

class MizWiki(object):
    def __init__(self,repository_path):
        self.repository_path = repository_path
        self.database_engine = create_engine(config.DATABASE, convert_unicode=True)
        local.application = self

    def init_database(self):
        metadata.create_all(self.database_engine)
        metadata.reflect(bind=self.database_engine)
        for table in reversed(metadata.sorted_tables):
            self.database_engine.execute(table.delete())

    def __call__(self, environ, start_response):
        local.application = self
        if not hasattr(local,'repository'):
            local.repository = models.Repository(self.repository_path)

        local.head = local.repository.youngest
        try:
            path_info = environ.get('PATH_INFO','/').strip('/')
            if re_invalidchars.search(path_info) != None:
                raise exceptions.Forbidden()

            response = controllers.mapper.dispatch(path_info)
            if not response:
                response = exceptions.Forbidden()

            return ClosingIterator(response(environ, start_response), [session.remove, local_manager.cleanup])
        except exceptions.HTTPException, e:
            return e(environ, start_response)

application = MizWiki(config.REPOSITORY_PATH)
