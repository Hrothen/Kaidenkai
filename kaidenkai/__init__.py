import os
#import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select
from sqlalchemy import create_engine, event, MetaData, Table, Column, \
     Integer, Text, ForeignKey
from werkzeug import check_password_hash, generate_password_hash

# create the application
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='sqlite:////' + os.path.join(app.root_path, 'kaidenkai.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD= generate_password_hash('default'),
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
    Column('username', Text, nullable=False, unique=True),
    Column('password', Text, nullable=False),
    Column('name', Text, nullable=False),
    Column('homepage', Text),
    Column('bio', Text),
    sqlite_autoincrement=True
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """tells sqlalchemy to use the foreign keys pragma if
    we're using sqlite3"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db():
    """initilize the database"""
    with app.app_context():
        metadata.drop_all()
        metadata.create_all()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context"""
    if not hasattr(g, 'sqlalchemy_db'):
        g.sqlalchemy_db = engine.connect()
    return g.sqlalchemy_db


def query_db(query, args=(), one=False):
    """helper function to open and then query the database"""
    cur = get_db().execute(query,args)
    rv = cur.first() if one else cur.fetchall()
    return rv


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from users where user_id = ?',
                         [session['user_id']],one=True)


@app.teardown_appcontext
def close_db(error):
    """Closes the database at the end of the request"""
    if hasattr(g, 'sqlalchemy_db'):
        g.sqlalchemy_db.close()


@app.route('/')
def show_entries():
    """shows all posts ordered from most to least recent"""
    entries = query_db('''select title, text from posts 
                          order by post_id desc''')
    return render_template('show_entries.html',entries=entries)


@app.route('/about')
def show_authors():
    """shows author bios ordered alphabetically by name"""
    authors = query_db('select name, homepage, bio from users order by name asc')
    return render_template('about.html',authors=authors)


@app.route('/add', methods=['POST'])
def add_entry():
    """adds a new post"""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        db = get_db()
        db.execute('''insert into posts (title, text, user_id) 
            values (?, ?, ?)''', (request.form['title'], request.form['text'],
                                  session['user_id']))
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """logs the user in"""
    if g.user:
        return redirect(url_for('show_entries'))
    error = None
    if request.method == 'POST':
        user = query_db('select * from users where username = ?',
                        [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash (user['password'], request.form['password']):
            error = 'Invalid password'
        else:
            session['user_id'] = user.user_id
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """logs the user out"""
    session.pop('user_id', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run()
