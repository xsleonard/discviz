#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from lxml import etree
from argparse import ArgumentParser
from functools import wraps
from discviz import db
from discviz.models import Label, Artist, Release
from utils import get_data_path, script


COMMIT_RATE = 5000


class Data(object):

    datestr = '20130601'
    files = ['artists', 'labels', 'masters']
    file_fmt = 'discogs_{date}_{name}.xml'

    def __init__(self, datestr=None):
        if datestr is None:
            datestr = self.datestr
        self.path = get_data_path(__file__)
        assert os.path.exists(self.path)
        files = [self.file_fmt.format(date=datestr, name=f)
                 for f in self.files]
        self.file_paths = [os.path.join(self.path, f) for f in files]
        assert all([os.path.exists(f) for f in self.file_paths])

    def get_path(self, name):
        try:
            index = self.files.index(name)
        except ValueError:
            raise ValueError('Unknown file: {0}'.format(name))
        return self.file_paths[index]


def fast_xml_iter(path, tag, func):
    # http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
    # Author: Liza Daly
    context = make_etree_context(path, tag)
    maxdepth = 1
    depth = 0
    ct = 0
    for event, elem in context:
        if event == 'start':
            depth += 1
            continue
        if depth <= maxdepth:
            ct = func(elem, ct)
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        if event == 'end':
            depth -= 1
    del context


def make_etree_context(path, tag):
    return etree.iterparse(path, tag=tag, events=('end', 'start',),
                           encoding='utf-8')


def print_element(elem, level=0):
    for e in elem.iterchildren():
        tabs = '\t' * level
        if e.text is None:
            print u'{tab}<{tag}>'.format(tab=tabs, tag=e.tag)
            print_element(e, level=level+1)
            continue
        print u'{tab}<{tag}> {text}'.format(tab=tabs, tag=e.tag, text=e.text)


def dbprocessor(f):
    @wraps(f)
    def wrapped(elem, ct):
        if f(elem) is not None:
            ct += 1
            if COMMIT_RATE and ct and (ct % COMMIT_RATE == 0):
                print 'Reached {0} elements, committing'.format(ct)
                db.session.commit()
                db.session.expunge_all()
        return ct
    return wrapped


@dbprocessor
def process_label_names(elem):
    name = None
    for e in elem.iterchildren():
        if e.tag == 'name' and e.text is not None:
            name = e.text
    if name is None:
        return
    label = Label(name)
    db.session.add(label)
    return label


@dbprocessor
def process_label_sublabels(elem):
    name = None
    sublabels = []
    for e in elem.iterchildren():
        if e.tag == 'name' and e.text is not None:
            name = e.text
        if e.tag == 'sublabels':
            for f in e.iterchildren(tag='label'):
                if f.text is not None:
                    sublabels.append(f.text)
    if name is None or not sublabels:
        return
    label = Label.get_by_name(name)
    if label is None:
        return
    label.set_sublabels(sublabels)
    return label


@dbprocessor
def process_parent_labels(elem):
    name = None
    parent_name = None
    for e in elem.iterchildren():
        if e.tag == 'name' and e.text is not None:
            name = e.text
        if e.tag == 'parentLabel' and e.text is not None:
            # We strip() because some parentLabels have erroneous whitespace
            parent_name = e.text.strip()
    if name is None or parent_name is None:
        return
    label = Label.get_by_name(name)
    if label is None:
        return
    label.set_parent_label(parent_name)
    return label


@dbprocessor
def process_artist_names(elem):
    name = None
    for e in elem.iterchildren():
        if e.tag == 'name' and e.text is not None:
            name = e.text
    if name is None:
        return
    artist = Artist(name)
    db.session.add(artist)
    return artist


@dbprocessor
def process_artist_aliases(elem):
    name = None
    aliases = []
    for e in elem.iterchildren():
        if e.tag == 'name' and e.text is not None:
            name = e.text
        if e.tag == 'aliases':
            for f in e.iterchildren(tag='name'):
                if f.text is not None:
                    aliases.append(f.text)
    if name is None or not aliases:
        return
    artist = Artist.get_by_name(name)
    if artist is None:
        return
    artist.set_aliases(aliases)
    return artist


@dbprocessor
def process_artist_groups(elem):
    name = None
    groups = []
    for e in elem.iterchildren():
        if e.tag == 'name' and e.text is not None:
            name = e.text
        if e.tag == 'groups':
            for f in e.iterchildren(tag='name'):
                if f.text is not None:
                    groups.append(f.text)
    if name is None or not groups:
        return
    artist = Artist.get_by_name(name)
    if artist is None:
        return
    artist.set_groups(groups)
    return artist


@dbprocessor
def process_master_names(elem):
    title = None
    release_id = None
    master_id = elem.attrib.get('id')
    if master_id is None:
        return
    for e in elem.iterchildren():
        if e.tag == 'title' and e.text is not None:
            title = e.text
        if e.tag == 'main_release' and e.text is not None:
            release_id = e.text
    if title is None or release_id is None:
        return
    release = Release(title, release_id, master_id=master_id)
    db.session.add(release)
    return release


@dbprocessor
def process_release_names(elem):
    title = None
    has_master = False
    for e in elem.iterchildren():
        if e.tag == 'title' and e.text is not None:
            title = e.text
        if e.tag == 'master_id' and e.text is not None:
            has_master = True
    if title is None or has_master:
        return
    release = Release(title)
    db.session.add(release)
    return release


@dbprocessor
def process_release_artists(elem):
    artists = []
    master_id = None
    release_id = elem.attrib.get('id')
    if release_id is None:
        return
    for e in elem.iterchildren():
        if e.tag == 'master_id' and e.text is not None:
            master_id = e.text
        if e.tag in ['artists', 'extraartists']:
            for f in e.iterchildren(tag='artist'):
                for g in g.iterchildren():
                    if g.tag == 'name' and g.text is not None:
                        artists.append(g.text)
    if not artists:
        return
    if master_id is None:
        release = Release.get_by_release_id(release_id)
    else:
        release = Release.get_by_master_id(master_id)
    if release is None:
        return
    artists = list(set(artists))
    release.add_artists(artists)


@dbprocessor
def process_release_labels(elem):
    labels = []
    master_id = None
    release_id = elem.attrib.get('id')
    if release_id is None:
        return
    for e in elem.iterchildren():
        if e.tag == 'master_id' and e.text is not None:
            master_id = e.text
        if e.tag == 'labels':
            for f in e.iterchildren(tag='label'):
                label = f.attrib.get('name')
                if label:
                    labels.append(label)
    if not labels:
        return
    if master_id is None:
        release = Release.get_by_release_id(release_id)
    else:
        release = Release.get_by_master_id(master_id)
    if release is None:
        return
    labels = list(set(labels))
    release.add_labels(labels)


def _load_things(path, tag, things):
    for name, method in things:
        print 'Extracting {0}...'.format(name)
        fast_xml_iter(path, tag, method)
        print 'Saving {0}...'.format(name)
        db.session.commit()
        db.session.expunge_all()
        print 'Done'


def load_masters(path, masters=True):
    things = []
    if masters:
        things.append(('masters', process_master_names))
    if things:
        _load_things(path, 'master', things)


def load_releases(path, releases=True, artists=True):
    things = []
    if releases:
        things.append(('releases', process_release_names))
    if artists:
        things.append(('artists', process_release_artists))
    if things:
        _load_things(path, 'release', things)


def load_artists(path, artists=True, aliases=True, groups=True):
    things = []
    if artists:
        things.append(('artists', process_artist_names))
    if aliases:
        things.append(('aliases', process_artist_aliases))
    if groups:
        things.append(('groups', process_artist_groups))
    if things:
        _load_things(path, 'artist', things)


def load_labels(path, labels=True, parent_labels=True):
    things = []
    if labels:
        things.append(('labels', process_label_names))
    if parent_labels:
        things.append(('parent labels', process_parent_labels))
    if things:
        _load_things(path, 'label', things)


def run(args):
    data = Data()
    g = data.get_path
    load_labels(g('labels'), labels=args.labels,
                parent_labels=args.parent_labels)
    load_artists(g('artists'), artists=args.artists,
                 aliases=args.artist_aliases, groups=args.artist_groups)
    if args.masters:
        load_masters(g('masters'), masters=args.masters)
    if args.releases:
        load_releases(g('releases'), releases=args.releases,
                      artists=args.release_artists,
                      labels=args.release_labels)


def get_args():
    global COMMIT_RATE
    p = ArgumentParser()
    p.add_argument('--config', default='local_dev',
                   help='Name of config file to use for the discviz app')
    p.add_argument('--labels', action='store_true',
                   help='Load the labels')
    p.add_argument('--parent-labels', action='store_true',
                   help='Load the parent labels')
    p.add_argument('--artists', action='store_true',
                   help='Load the artists')
    p.add_argument('--artist-aliases', action='store_true',
                   help='Load the artists\' aliases')
    p.add_argument('--artist-groups', action='store_true',
                   help='Load the artists\' groups')
    p.add_argument('--masters', action='store_true',
                   help='Load the masters')
    p.add_argument('--releases', action='store_true',
                   help='Load the releases')
    p.add_argument('--release-artists', action='store_true',
                   help='Load the release artists')
    p.add_argument('--release-labels', action='store_true',
                   help='Load the release labels')
    p.add_argument('--all', action='store_true',
                   help='Load everything')
    p.add_argument('--commit-rate', type=int, default=COMMIT_RATE,
                   help='Commit to the database every N changes')
    args = p.parse_args()
    check = ['labels', 'parent_labels', 'artists', 'artist_aliases',
             'artist_groups', 'masters', 'releases', 'release_artists',
             'release_labels', 'all']
    if not any([getattr(args, c) for c in check]):
        p.error('Select something to load')
    if args.all:
        [setattr(args, c, True) for c in check]
    COMMIT_RATE = args.commit_rate
    return args


if __name__ == '__main__':
    args = get_args()
    script(config=args.config)(run)(args)
