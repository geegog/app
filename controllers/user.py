import sqlite3
import traceback

import sys

import os
from PIL import Image, ExifTags
from flask import Blueprint, request, flash, redirect, url_for, session, render_template
from werkzeug.utils import secure_filename

from app.services import dao

get_user = Blueprint('get_user',  __name__)
user_page = Blueprint('user_page',  __name__)
register_user = Blueprint('register_user',  __name__)
register_page = Blueprint('register_page',  __name__)


@register_page.route('/register', methods=['GET'])
def register_view():
    if 'logged_in' in session:
        return redirect(url_for('login'))
    return render_template('register.html')


@get_user.route('/user', methods=['POST'])
def user():
    db = dao.get_db()
    cur = db.execute('SELECT * FROM users WHERE password = ? AND email = ?',
                     [request.form['password'], request.form['email']])
    auth_user = cur.fetchone()
    if auth_user is None:
        flash('Wrong email or password')
        return redirect(url_for('login_page.login'))
    else:
        session['logged_in'] = True
        session['password'] = auth_user[4]
        session['email'] = auth_user[3]
        flash('Welcome Back...')
        return render_template('user.html', user=auth_user)


@user_page.route('/user', methods=['GET'])
def user_view():
    if 'logged_in' not in session:
        return redirect(url_for('login_page.login'))
    db = dao.get_db()
    cur = db.execute('SELECT * FROM users WHERE password = ? AND email = ?',
                     [session['password'], session['email']])
    auth_user = cur.fetchone()
    flash('Welcome Back...')
    return render_template('user.html', user=auth_user)


@register_user.route('/register', methods=['POST'])
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
        image.save(os.path.join('static', 'uploads/') + secure_filename(photo.filename), image.format)
    try:
        db = dao.get_db()
        db.execute('INSERT INTO users (first_name, last_name, email, password, phone_number, file_name)'
                   ' VALUES (?, ?, ?, ?, ?, ?)',
                   [request.form['first_name'], request.form['last_name'], request.form['email'],
                    request.form['password'], request.form['phone_number'], secure_filename(photo.filename)])
        db.commit()
    except sqlite3.IntegrityError:
        flash('Email taken by someone else')
        return redirect(url_for('register_view'))
    flash('Your have been successfully added. Please login')
    return redirect(url_for('login_page.login'))
