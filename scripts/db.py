#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from discviz import db, create_app
from discviz.models import Label


def drop():
    db.drop_all()
    print 'Dropping completed successful!'


def create():
    db.create_all()
    print 'Creating completed successful!'


def reset():
    drop()
    create()

actions = dict(
    drop=(drop, 'drop tables'),
    create=(create, 'create tables'),
    reset=(reset, 'drop and create'),
)


def help(action=None):
    if action is not None:
        print 'Unknown command {0}'.format(str(action))
    print 'Please, use:'
    for name, (action, desc) in actions.items():
        print '{0} - {1}'.format(name, desc)


def _handle_cli():
    if len(sys.argv) < 2:
        help()
        sys.exit()
    action = sys.argv[1]
    if action not in actions:
        help(action)
        sys.exit()
    try:
        actions[action][0]()
    except Exception, e:
        print 'Error: ', e

if __name__ == '__main__':
    app = create_app()
    with app.test_request_context():
        _handle_cli()
