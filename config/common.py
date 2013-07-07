from urllib import quote


def make_database_uri(dbtype, user, password, address, port, name):
    uri = '{dbtype}://{userpass}@{address}:{port}/{db}'
    if password:
        userpass = '{0}:{1}'.format(user, quote(password))
    else:
        userpass = user
    return uri.format(dbtype=dbtype, userpass=userpass, address=address,
                      port=port, db=name)
