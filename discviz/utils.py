from flask import url_for


def static_url(path):
    return url_for('static', filename=path)


class AttributeDict(dict):

    def __setattr__(self, k, v):
        return dict.__setitem__(self, k, v)

    def __getattribute__(self, key):
        if key in self:
            return dict.__getitem__(self, key)
        return object.__getattribute__(self, key)
