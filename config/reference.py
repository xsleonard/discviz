from common import make_database_uri

SERVER_NAME = '127.0.0.1:5000'
DEBUG = True
NEO4J_URI = 'http://localhost:7474/db/data'
NEO4J_USER = ''
NEO4J_PASS = ''
LOGGING = True
SESSION_COOKIE_DOMAIN = '127.0.0.1'
SESSION_COOKIE_HTTPONLY = True
SECRET_KEY = 'xxx'
SESSION_SALT = 'yyy'
CONFIG_NAME = 'reference'

DB_USER = 'you'
DB_PASSWORD = 'pass'
DB_ADDRESS = 'localhost'
DB_PORT = 5432
DB_NAME = 'discviz'
SQLALCHEMY_DATABASE_URI = make_database_uri('postgres', DB_USER, DB_PASSWORD,
                                            DB_ADDRESS, DB_PORT, DB_NAME)
