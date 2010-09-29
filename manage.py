#!/usr/bin/env python
from werkzeug import script
from werkzeug import DebuggedApplication

def make_app():
    from mizwiki.application import application
    return application

def make_debug_app():
    return DebuggedApplication(make_app(), evalex=True)

def make_shell():
    from mizwiki import models,local,cache
    application = make_app()
    return locals()

action_runserver = script.make_runserver(make_debug_app, use_reloader=True)
action_shell = script.make_shell(make_shell)
action_initdb = lambda: make_app().init_database()

script.run()
