import os
import errno
from functools import wraps
from discviz import create_app


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_here(f):
    return os.path.abspath(os.path.dirname(__file__))


def get_data_path(f):
    here = get_here(f)
    return os.path.abspath(os.path.join(here, '../../data'))


def script(*create_app_args, **create_app_kwargs):
    def _script(f):
        '''Calls the decorated function with a request context bound'''
        @wraps(f)
        def wrapped(*args, **kwargs):
            app = create_app(*create_app_args, **create_app_kwargs)
            with app.test_request_context():
                return f(*args, **kwargs)
        return wrapped
    return _script
