import os
import logging
from bulbs.neo4jserver import (Graph as NeoGraph, Config as NeoConfig,
                               NEO4J_URI)
from flask import Flask, json
from flask.sessions import SecureCookieSession, SecureCookieSessionInterface
from flask.ext.sqlalchemy import SQLAlchemy

__version__ = '0.10'


db = SQLAlchemy()


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


def load_config(app, subdomain='', config=None):
    """
    Grab config from DISCVIZ_SETTINGS envvar or use default dev config.
    Update the SERVER_NAME based on subdomain
    """
    if config is not None:
        app.config.from_object('config.{0}'.format(config))
    elif os.environ.get('DISCVIZ_SETTINGS') is not None:
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
    if app.graph is not None:
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


def create_app(subdomain='', config=None):
    app = Flask(__name__)
    load_config(app, subdomain=subdomain, config=config)
    #if app.config.get('HEROKU'):
        #heroku.init_app(app)
    if app.config['ENABLE_NEO4J']:
        init_graph(app)
    else:
        app.graph = None
    if app.config['ENABLE_SQL']:
        db.init_app(app)
    else:
        app.db = None
    if app.config.get('LOGGING'):
        attach_loggers(app)
    app.session_interface = JSONSecureCookieSessionInterface()
    register_blueprints(app)
    attach_before_request_handlers(app)
    inject_context_processors(app)
    return app
