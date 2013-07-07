# -*- coding: utf-8 -*-

from sqlalchemy.ext.hybrid import hybrid_property
from discviz import db

''' Mixins '''


class NameMixin(object):

    _name = db.Column(db.Unicode(256), nullable=False, unique=True,
                      index=True)
    display_name = db.Column(db.Unicode(256), nullable=False, unique=True)

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        name = name.strip()
        self._name = unicode(name.encode('utf-8').lower(), 'utf-8')
        self.display_name = unicode(name.encode('utf-8'), 'utf-8')

    @classmethod
    def get_all_by_names(cls, names):
        if not names:
            return []
        names = list(set(names))
        names = [unicode(name.strip().encode('utf-8').lower(), 'utf-8')
                 for name in names]
        return cls.query.filter(cls._name.in_(names)).all()

    @classmethod
    def get_by_name(cls, name):
        if name is None:
            return
        name = unicode(name.strip().encode('utf-8').lower(), 'utf-8')
        return cls.query.filter(cls._name == name).first()

    def __eq__(self, other):
        return (self.id is not None and self.id == other.id)

    def __ne__(self, other):
        return (not self.__eq__(other))


''' Association Tables '''


class ArtistGroup(db.Model):
    __tablename__ = 'artist_group'

    def __init__(self, artist_id, group_id):
        if artist_id == group_id:
            msg = 'Warning: setting artist in group to self for id {0}'
            print msg.format(artist_id)
        self.artist_id = artist_id
        self.group_id = group_id

    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'),
                          primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('artist.id'),
                         primary_key=True)


class ArtistAlias(db.Model):
    __tablename__ = 'artist_alias'

    def __init__(self, artist_id, alias_id):
        if artist_id == alias_id:
            msg = 'Warning: setting artist alias to self for id {0}'
            print msg.format(artist_id)
        self.artist_id = artist_id
        self.alias_id = alias_id

    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'),
                          primary_key=True)
    alias_id = db.Column(db.Integer, db.ForeignKey('artist.id'),
                         primary_key=True)


class ArtistRelease(db.Model):
    __tablename__ = 'artist_release'

    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'),
                          primary_key=True)
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'),
                           primary_key=True)
    release = db.relationship('Release')

    def __init__(self, artist_id, release_id):
        self.artist_id = artist_id
        self.release_id = release_id


class LabelRelease(db.Model):
    __tablename__ = 'label_release'

    label_id = db.Column(db.Integer, db.ForeignKey('label.id'),
                         primary_key=True)
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'),
                           primary_key=True)
    release = db.relationship('Release')

    def __init__(self, label_id, release_id):
        self.label_id = label_id
        self.release_id = release_id


''' Models '''


class Label(db.Model, NameMixin):

    __tablename__ = 'label'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    parent_label_id = db.Column(db.Integer, db.ForeignKey('label.id'),
                                nullable=True)
    parent_label = db.relationship('Label', backref='sublabels',
                                   remote_side='Label.id', post_update=True)
    releases = db.relationship(LabelRelease, backref='label')

    def __init__(self, name):
        self.name = name

    def set_parent_label(self, parent_name):
        if parent_name is None:
            return
        parent = self.get_by_name(parent_name)
        if parent is None:
            msg = u'Warning: parent label "{0}" not found for label "{1}"'
            print msg.format(parent_name, self.display_name)
            return
        if parent.id == self.id:
            return
        self.parent_label = parent

    def set_sublabels(self, sublabels):
        sublabels = self.get_all_by_names(sublabels)
        sublabels = [s for s in sublabels if s.id != self.id]
        self.sublabels = sublabels


class Artist(db.Model, NameMixin):

    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True, unique=True)

    groups = db.relationship(ArtistGroup, backref='group_members',
                             primaryjoin=(id == ArtistGroup.artist_id))

    aliases = db.relationship(ArtistAlias,
                              primaryjoin=(id == ArtistAlias.artist_id))

    releases = db.relationship(ArtistRelease, backref='artist')

    def __init__(self, name):
        self.name = name

    def set_aliases(self, aliases):
        aliases = self.get_all_by_names(aliases)
        aliases = [ArtistAlias(self.id, s.id)
                   for s in aliases if s.id != self.id]
        self.aliases = aliases

    def set_groups(self, groups):
        groups = self.get_all_by_names(groups)
        groups = [ArtistGroup(self.id, g.id)
                  for g in groups if g.id != self.id]
        self.groups = groups


class Release(db.Model):

    __tablename__ = 'release'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    master_id = db.Column(db.Integer, unique=True, index=True, nullable=True)
    release_id = db.Column(db.Integer, unique=True, index=True)
    artists = db.relationship(ArtistRelease, backref='releases')
    labels = db.relationship(LabelRelease, backref='releases')
    title = db.Column(db.Unicode(256), nullable=False)

    def __init__(self, title, release_id, master_id=None):
        self.title = title
        self.release_id = release_id
        self.master_id = master_id

    def add_artists(self, artists):
        artists = Artist.get_all_by_names(artists)
        existing = [artist.artist_id for artist in self.artists]
        artists = [artist for artist in artists if artist.id not in existing]
        artists = [ArtistRelease(artist.id, self.id) for artist in artists]
        self.artists += artists

    def add_labels(self, labels):
        labels = Label.get_all_by_names(labels)
        existing = [label.label_id for label in self.labels]
        labels = [label for label in labels if label.id not in existing]
        labels = [LabelRelease(label.id, self.id) for label in labels]
        self.labels += labels

    @classmethod
    def get_by_master_id(cls, master_id):
        return cls.query.filter(cls.master_id == master_id).first()

    @classmethod
    def get_by_release_id(cls, release_id):
        return cls.query.filter(cls.release_id == release_id).first()
