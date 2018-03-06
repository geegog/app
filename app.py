import os

from flask import Flask, g
from services import dao
from controllers import user, auth


app = Flask(__name__)
app.config.from_object(__name__)

app.register_blueprint(user.get_user)
app.register_blueprint(user.user_page)
app.register_blueprint(user.register_user)
app.register_blueprint(user.register_page)

app.register_blueprint(auth.login_page)
app.register_blueprint(auth.logout_user)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'app.db'),
    PHOTOS=os.path.join('static', 'uploads/'),
    SECRET_KEY='app-key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('APP_SETTINGS', silent=True)


def init_db():
    db = dao.get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def init_db_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


if __name__ == '__main__':
    app.run()
