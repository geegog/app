from flask import Blueprint, session, flash, redirect, url_for, render_template


login_page = Blueprint('login_page',  __name__)
logout_user = Blueprint('logout_user',  __name__)


@login_page.route('/', methods=['GET'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('user_page.user_view'))
    return render_template('login.html')


@logout_user.route('/logout')
def logout():
    session.clear()
    flash('You were logged out')
    return redirect(url_for('login_page.login'))
