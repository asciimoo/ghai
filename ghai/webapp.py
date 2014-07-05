#!/usr/bin/env python

'''
ghai is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ghai is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with ghai. If not, see < http://www.gnu.org/licenses/ >.

(C) 2014- by Adam Tauber, <asciimoo@gmail.com>
'''

if __name__ == '__main__':
    from sys import path
    from os.path import realpath, dirname
    path.append(realpath(dirname(realpath(__file__))+'/../'))

from flask import (
    Flask, request, render_template, url_for,
    redirect, session, flash
)

from rauth import OAuth2Service
from json import dumps
from functools import wraps
from collections import OrderedDict
from ghai.models import User, Item, Feed, db
from ghai import cfg

# Flask config

# Read secret keys from env vars
# # See: http://12factor.net/config
github_app_id = cfg.get('github', 'github_app_id')
github_app_secret = cfg.get('github', 'github_app_secret')

github = OAuth2Service(
    client_id=github_app_id,
    client_secret=github_app_secret,
    name='github',
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    base_url='https://api.github.com/')

app = Flask(__name__)
app.secret_key = cfg.get('app', 'secret')
app.config.from_object(__name__)
app.debug = True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.user is None:
            return render('login.html')
        return f(*args, **kwargs)
    return decorated_function


def render(template_name, **kwargs):

    # override url_for function in templates
    kwargs['user'] = request.user


    return render_template(template_name, **kwargs)


@app.before_request
def before_request():
    request.user = None
    if 'user_id' in session:
        if session['user_id']:
            user = User.query.get(session['user_id'])
            if user:
                request.user = user
            else:
                del session['user_id']

types = ('personal', 'star', 'repo', 'issue')


# views
@app.route('/')
@login_required
def index():
    if not request.user:
        return redirect(url_for('login'))

    d = OrderedDict({x:[] for x in types})
    unread_items = Item.query.filter(Item.feed.has(user=request.user)).filter(Item.archived==False).order_by(Item.date.desc()).all()
    for item in unread_items:
        item_type, item.rendered_content = item.render(request.user)
        if not item_type:
            continue
        d[item_type].append(item)
    return render('index.html', events=d)


@app.route('/query')
@login_required
def query():
    q = request.args.get('q', '')
    data = None
    if q:
        auth = github.get_session(token = session['token'])
        resp = auth.get(q)
        if resp.status_code == 200:
            data = resp.json()
    return render('query.html', data=dumps(data, indent=True), query=q)


@app.route('/archive/<ids>')
@login_required
def archive(ids):

    try:
        ids = map(int, map(unicode.strip, ids.split(',')))
    except:
        # TODO error handling
        return redirect(url_for('index'))

    for i in Item.query.filter(Item.feed.has(user=request.user)).filter(Item.id.in_(ids)).filter(Item.archived==False):
        i.archived = True
    db.commit()
    return redirect(url_for('index'))


@app.route('/login')
def login():
    redirect_uri = url_for('authorized', next=request.args.get('next') or
        request.referrer or None, _external=True)
    # More scopes http://developer.github.com/v3/oauth/#scopes
    # params = {'redirect_uri': redirect_uri, 'scope': 'user:email'}
    params = {'redirect_uri': redirect_uri}
    return redirect(github.get_authorize_url(**params))


# same path as on application settings page
@app.route('/callback')
def authorized():
    # check to make sure the user authorized the request
    if not 'code' in request.args:
        flash('You did not authorize the request')
        return redirect(url_for('index'))

    # make a request for the access token credentials using code
    redirect_uri = url_for('authorized', _external=True)

    data = dict(code=request.args['code'],
        redirect_uri=redirect_uri,
        scope='public_repo')

    auth = github.get_auth_session(data=data)

    # the "me" response
    me = auth.get('/user').json()

    user = User.get_or_create(me['login'], me['name'])

    session['token'] = auth.access_token
    session['user_id'] = user.id

    flash('Logged in as ' + me['name'])
    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    """
    Logout
    """

    # Delete session data
    session.pop('user_id')
    session.pop('token')

    return redirect(url_for('index'))


@app.route('/feeds')
@login_required
def feeds():
    """
    Feeds
    """
    feeds = Feed.query.filter(Feed.user==request.user).all()
    return render('feeds.html', feeds=feeds)


@app.route('/feed/add', methods=['POST'])
@login_required
def add_feed():
    """
    Add feeds
    """
    if not request.form.get('url'):
        return redirect(url_for('index'))
    feed = Feed(request.form['url'], request.user)
    db.add(feed)
    db.commit()
    return redirect(url_for('feeds'))



@app.route('/fetch')
@login_required
def fetch():
    if not request.user or not session.get('token'):
        return redirect(url_for('login'))
    auth = github.get_session(token = session['token'])
    for feed in request.user.feeds:
        resp = auth.get(feed.url).json()
        for resp_item in resp:
            Item.parse_and_add(resp_item, feed, request.user)
    return redirect(url_for('index'))

def run():

    app.run(
        debug=app.debug,
        use_debugger=app.debug,
        port=4444
    )


if __name__ == "__main__":
    run()
