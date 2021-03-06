from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pathlib
from os import path
from flask_login import LoginManager, current_user
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed

db = SQLAlchemy()
DB_NAME = "database.db"

UPLOAD_FOLDER = pathlib.Path(__file__).parent.joinpath("uploads")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "helloworld"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import User, Post, Comment, Like

    create_database(app)

    login_manager = LoginManager()

    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    Principal(app)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Set the identity user object
        identity.user = current_user

        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        if getattr(current_user, 'is_admin', False):
            identity.provides.add(RoleNeed('admin'))

    return app


def create_database(app):
    if not path.exists("website/" + DB_NAME):
        db.create_all(app=app)
        print("Created database!")

admin_permission = Permission(RoleNeed('admin'))
