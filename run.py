#!/usr/bin/env python

import os
from flask.ext.failsafe import failsafe


@failsafe
def create_app(subdomain=''):
    from discviz import create_app
    return create_app(subdomain)


def run():
    app = create_app()
    server_name = app.config.get('SERVER_NAME')
    if server_name is not None:
        # Assume local configuration with port given
        host, port = server_name.split(':')
        port = int(port)
    else:
        # Assume heroku configuration, no SERVER_NAME present, get port
        # from environment
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)

if __name__ == '__main__':
    run()
