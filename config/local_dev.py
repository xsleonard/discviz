from common import make_database_uri

SERVER_NAME = '127.0.0.1:5000'
DEBUG = True
ENABLE_NEO4J = False
NEO4J_URI = 'http://localhost:7474/db/data'
NEO4J_USER = ''
NEO4J_PASS = ''
LOGGING = True
SESSION_COOKIE_DOMAIN = '127.0.0.1'
SESSION_COOKIE_HTTPONLY = True
SECRET_KEY = '\x99\x96?1\xdc\x89o0\xf5\xd1\x1f\x99\x8f5\x9bA\x9e\xd7\xdc\xb4d"\xb9\x0e\xb6\xbe\x95\xaf\xab\x919\xc2'
SESSION_SALT = '\xb9\xd9v\x84\xa0\xde\xbb\xdc\x1e\x99.\xea\x91Z\xf1\x06\x99\xfc\xba\xdd\xcf\x83\x1d\xcb\xde(\xd5\xa0\x153\x12\xef'
CONFIG_NAME = 'local_dev'

ENABLE_SQL = True
DB_USER = 'steve'
DB_PASSWORD = 'monkey'
DB_ADDRESS = 'localhost'
DB_PORT = 5432
DB_NAME = 'discviz'
SQLALCHEMY_DATABASE_URI = make_database_uri('postgres', DB_USER, DB_PASSWORD,
                                            DB_ADDRESS, DB_PORT, DB_NAME)
