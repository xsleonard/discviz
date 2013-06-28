import os
import logging
from urlparse import urljoin
from bulbs.neo4jserver import (Graph as NeoGraph, Config as NeoConfig,
                               NEO4J_URI)
from flask import (Flask, current_app, jsonify, render_template, request, g,
                   session, json, abort)
from flask.sessions import SecureCookieSession, SecureCookieSessionInterface

__version__ = '0.10'

def init_graph(app):
    user = app.config.get('NEO4J_USER')
    password = app.config.get('NEO4J_PASS')
    uri = app.config.get('NEO4J_URI', NEO4J_URI)
    if user or password:
        cargs = (uri, user, password)
    else:
        cargs = (uri,)
    app.graph = NeoGraph(NeoConfig(*cargs))


def register_blueprints(app):
    """
    Register our blueprints with the app
    """
    from discviz.frontend.views import frontend
    app.register_blueprint(frontend)


def load_config(app, subdomain=''):
    """
    Grab config from DISCVIZ_SETTINGS envvar or use default dev config.
    Update the SERVER_NAME based on subdomain
    """
    if os.environ.get('DISCVIZ_SETTINGS') is not None:
        app.config.from_envvar('DISCVIZ_SETTINGS')
    else:
        app.config.from_object('config.local_dev')
    if subdomain:
        server_name = subdomain + '.' + app.config['SERVER_NAME']
        app.config['SERVER_NAME'] = server_name


def attach_loggers(app):
    """
    Setup stderr logging
    """
    log_format = ('%(asctime)s [%(pathname)s:%(lineno)d:%(levelname)s] '
                  '%(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))
    loggers = [app.logger]
    for logger in loggers:
        logger.addHandler(stream_handler)
    if app.config['DEBUG'] or app.config.get('DEBUG_LOGGING'):
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
    app.graph.config.set_logger(logging.DEBUG)


def attach_before_request_handlers(app):
    """
    Bind functions to run before_request
    """
    pass


def inject_context_processors(app):
    """
    Add custom variables to be exposed in jinja templates
    """
    from discviz.utils import static_url

    @app.context_processor
    def inject_static():
        return dict(static_url=static_url)


class JSONSecureCookieSession(SecureCookieSession):
    serialization_method = json


class JSONSecureCookieSessionInterface(SecureCookieSessionInterface):
    session_class = JSONSecureCookieSession


def create_app(subdomain=''):
    app = Flask(__name__)
    load_config(app, subdomain)
    if app.config.get('HEROKU'):
        heroku.init_app(app)
    init_graph(app)
    if app.config.get('LOGGING'):
        attach_loggers(app)
    app.session_interface = JSONSecureCookieSessionInterface()
    register_blueprints(app)
    attach_before_request_handlers(app)
    inject_context_processors(app)
    return app
