from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import TypeDecorator, VARCHAR
from flask.ext.sqlalchemy import SQLAlchemy


REF_MAP = {'repository': 'repo'}
db = SQLAlchemy()


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


# Bases
class User(db.Model):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(80), unique=True)
    name = Column(String(120))

    def __init__(self, login, name):
        self.login = login
        self.name = name

    def __repr__(self):
        return '<User %r>' % self.login

    @staticmethod
    def get_or_create(login, name, feeds=None):
        user = User.query.filter_by(login=login).first()
        if user:
            return user

        feeds = feeds or []
        feeds.append('/users/{0}/received_events'.format(login))
        user = User(login, name)
        db.session.add(user)
        for feed in feeds:
            user_feed = Feed(feed, user)
            db.session.add(user_feed)
        db.session.commit()
        return user


class Feed(db.Model):

    __tablename__ = 'feeds'

    id = Column(Integer, primary_key=True)
    url = Column(String(120))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref=backref('feeds', lazy='dynamic'))

    def __init__(self, url, user):
        self.url = url
        self.user = user

    def __repr__(self):
        return '<Feed %r>' % self.url


class Item(db.Model):

    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    content = Column(JSONEncodedDict(1023))
    feed_id = Column(Integer, ForeignKey('feeds.id'))
    date = Column(DateTime)
    archived = Column(Boolean())
    feed = relationship('Feed',
                        backref=backref('items', lazy='dynamic'))

    def __init__(self, feed, content):
        self.feed = feed
        self.content = content
        self.archived = False

    def __repr__(self):
        return '<Item %r>' % self.content

    def render(self, request_user):
        resp_item = self.content
        act = ''
        repo = resp_item['repo']['name']
        user = resp_item['actor']['login']
        repo_user = repo.split('/')[0]
        if resp_item['type'] == 'WatchEvent':
            # starred repo
            t = 'star'
            act = 'starred'
        elif resp_item['type'] == 'CreateEvent':
            t = REF_MAP.get(resp_item['payload']['ref_type'])
            act = 'created {0}'.format(resp_item['payload']['ref_type'])
        elif resp_item['type'] == 'ForkEvent':
            t = 'repo'
            act = 'forked'
        elif resp_item['type'] == 'PushEvent':
            # TODO
            t = 'repo'
            act = 'pushed to'
        elif resp_item['type'] == 'PullRequestEvent':
            # TODO
            t = 'repo'
            act = '{0} pull request'.format(resp_item['payload']['action'])
        elif resp_item['type'] == 'DeleteEvent':
            # TODO
            t = 'repo'
            act = 'deleted {0} {1} at'.format(resp_item['payload']['ref_type'],
                                            resp_item['payload']['ref'])
        elif resp_item['type'] == 'IssuesEvent':
            t = 'issue'
            act = '{0} issue (<a href="{1}">#{2}</a>)'.format(resp_item['payload']['action'], resp_item['payload']['issue']['url'], resp_item['payload']['issue']['number'])
        elif resp_item['type'] == 'IssueCommentEvent':
            t = 'issue'
            act = 'commented issue (<a href="{0}">#{1}</a>)'.format(resp_item['payload']['issue']['url'], resp_item['payload']['issue']['number'])
        elif resp_item['type'] == 'CommitCommentEvent':
            t = 'issue'
            act = 'commented on commit <a href="{0}">{1}</a>'.format(resp_item['payload']['comment']['url'], resp_item['payload']['comment']['commit_id'])
        elif resp_item['type'] == 'GollumEvent':
            t = 'repo'
            # TODO multiple pages
            page = resp_item['payload']['pages'][0]
            act = '{0} wiki <a href="{1}">{2}</a>'.format(page['action'], page['html_url'], page['page_name'])
        else:
            print resp_item['type'], resp_item
            return False, False
        if repo_user == request_user.login:
            t = 'personal'
        return t, '<a href="https://github.com/{0}">{0}</a> {2} <a href="https://github.com/{1}">{1}</a>.'.format(user, repo, act)

    @staticmethod
    def parse_and_add(resp_item, feed, request_user):
        if Item.query.filter(Item.id==resp_item['id']).first():
            return False
        user = resp_item['actor']['login']
        if user == feed.user.login:
            return False
        item = Item(feed, resp_item)
        item.date = datetime.strptime(resp_item['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        item.id = resp_item['id']
        db.session.add(item)
        db.session.commit()
        return True
