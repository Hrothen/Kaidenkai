import os
#import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select
from sqlalchemy import create_engine, event, MetaData, Table, Column, \
     Integer, Text, ForeignKey

# create the application
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='sqlite:////' + os.path.join(app.root_path, 'kaidenkai.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('KAIDENKAI_SETTINGS', silent=True)

engine = create_engine(app.config['DATABASE'], convert_unicode=True)
metadata = MetaData(bind=engine)

posts = Table('posts', metadata,
    Column('post_id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey("users.user_id"), nullable=False),
    Column('title', Text, nullable=False),
    Column('text', Text, nullable=False),
    sqlite_autoincrement=True
)

users = Table('users', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('user_login', Text, nullable=False),
    Column('password', Text, nullable=False),
    Column('name', Text, nullable=False),
    Column('homepage', Text),
    Column('bio', Text),
    sqlite_autoincrement=True
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db():
    with app.app_context():
        metadata.drop_all()
        metadata.create_all()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context"""
    if not hasattr(g, 'sqlalchemy_db'):
        g.sqlalchemy_db = engine.connect()
    return g.sqlalchemy_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database at the end of the request"""
    if hasattr(g, 'sqlalchemy_db'):
        g.sqlalchemy_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from posts order by post_id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html',entries=entries)


@app.route('/about')
def show_authors():
    db = get_db()
    cur = db.execute('select name, homepage, bio from users order by name asc')
    authors = cur.fetchall()
    return render_template('about.html',authors=authors)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    usr = session.get('user_id')
    db.execute('insert into posts (title, text, user_id) values (?, ?, ?)',
                 [request.form['title'], request.form['text'], usr])
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        db = get_db()
        s = select([users.c.user_id, users.c.user_login, users.c.password])\
           .where(users.c.user_login == username)
        #cur = db.execute('select user_id, user_login, password from users where user_login = ' + username)
        cur = db.execute(s)
        user = cur.first()
        if user == None:
            error = 'Invalid username'
        elif request.form['password'] != user.password:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['user_id'] = user.user_id
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run()
