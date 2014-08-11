import os
#import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

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

entries = Table('entries', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String, nullable=False),
    Column('text', String, nullable=False),
    sqlite_autoincrement=True
)


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
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html',entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
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
