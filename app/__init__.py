from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SECRET_KEY'] = 'mysecret'
    app.config['UPLOAD_FOLDER'] = 'static/covers'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from app import routes, models
        app.register_blueprint(routes.bp)
        db.create_all()
    
    return app

from app.models import User  # Add this line

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
