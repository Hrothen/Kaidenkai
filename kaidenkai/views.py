from werkzeug import check_password_hash, generate_password_hash
from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash
from kaidenkai import app, query_db, get_db

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