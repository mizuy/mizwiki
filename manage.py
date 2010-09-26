#!/usr/bin/env python
from werkzeug import script
from werkzeug import DebuggedApplication

def make_app():
    from mizwiki.application import application
    return DebuggedApplication(application, evalex=True)

def make_shell():
    from mizwiki import models, utils
    application = make_app()
    return locals()

action_runserver = script.make_runserver(make_app, use_reloader=True)
action_shell = script.make_shell(make_shell)

script.run()
