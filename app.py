import os
import sqlite3
import traceback

import sys
from PIL import Image, ExifTags
from flask import Flask, redirect, flash, request, render_template, url_for, g, session
from resizeimage import resizeimage
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'app.db'),
    PHOTOS=os.path.join('static', 'uploads/'),
    SECRET_KEY='app-key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('APP_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def init_db_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.route('/', methods=['GET'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('user_view'))
    return render_template('login.html')


@app.route('/user', methods=['POST'])
def user():
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE password = ? AND email = ?',
                     [request.form['password'], request.form['email']])
    auth_user = cur.fetchone()
    if auth_user is None:
        flash('Wrong email or password')
        return redirect(url_for('login'))
    else:
        session['logged_in'] = True
        session['password'] = auth_user[4]
        session['email'] = auth_user[3]
        flash('Welcome Back...')
        return render_template('user.html', user=auth_user)


@app.route('/user', methods=['GET'])
def user_view():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE password = ? AND email = ?',
                     [session['password'], session['email']])
    auth_user = cur.fetchone()
    flash('Welcome Back...')
    return render_template('user.html', user=auth_user)


@app.route('/register', methods=['POST'])
def add_user():
    photo = request.files['photo']

    with Image.open(photo) as image:
        if image.size[0] <= 2000:
            base_width = 250
        else:
            base_width = 500
        w_percent = (base_width / float(image.size[0]))
        h_size = int((float(image.size[1]) * float(w_percent)))

        if hasattr(image, '_getexif'):  # only present in JPEGs
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                e = image._getexif()  # returns None if no EXIF data
                if e is not None:
                    exif = dict(e.items())
                    orientation = exif[orientation]

                    if orientation == 3:
                        image = image.transpose(Image.ROTATE_180)
                    elif orientation == 6:
                        image = image.transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        image = image.transpose(Image.ROTATE_90)
            except:
                traceback.print_exc(file=sys.stdout)
        image.thumbnail((base_width, h_size), Image.ANTIALIAS)
        image.save(app.config['PHOTOS'] + secure_filename(photo.filename), image.format)
    try:
        db = get_db()
        db.execute('INSERT INTO users (first_name, last_name, email, password, phone_number, file_name)'
                   ' VALUES (?, ?, ?, ?, ?, ?)',
                   [request.form['first_name'], request.form['last_name'], request.form['email'],
                    request.form['password'], request.form['phone_number'], secure_filename(photo.filename)])
        db.commit()
    except sqlite3.IntegrityError:
        flash('Email taken by someone else')
        return redirect(url_for('register_view'))
    flash('Your have been successfully added. Please login')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET'])
def register_view():
    if 'logged_in' in session:
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
