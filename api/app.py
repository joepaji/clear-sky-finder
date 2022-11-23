#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
A RESTful API for the Clear Sky Finder app built using Flask.
This API works with a MySQL Database to provide app functions.
"""
from flask import Flask
from flask_marshmallow import Marshmallow
from db_config import HOST, USER, PASSWORD
from extensions import db, ma
from user import user as user_bp

app = Flask(__name__)
prefix = '/v1'
ma = Marshmallow(app)

def create_app():
    """
    Initializes the API
    """
    app = Flask(__name__)
    db_name = 'clear_sky_finder_db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    register_extensions(app)
    register_blueprints(app)
    return app

def register_extensions(app):
    """
    Initializes extensions
    """
    db.init_app(app)
    ma.init_app(app)
    return None

def register_blueprints(app):
    """
    Registers all blueprints
    """
    app.register_blueprint(user_bp, url_prefix=f'{prefix}/user/')
    return None

if __name__ == '__main__':
    app = create_app()
    app.run(port=8000, debug=True)
    