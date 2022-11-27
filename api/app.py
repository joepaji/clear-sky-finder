#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
A RESTful API for the Clear Sky Finder app built using Flask.
This API works with a MySQL Database to provide app functions.
It can add a user, locations to track, and get cloud data for 
tracked locations.
"""
from flask import Flask, Blueprint
from db_config import HOST, USER, PASSWORD
from extensions import db, ma
from user import user as user_bp
from track import track as track_bp
from clouds import clouds as clouds_bp
from exceptions import exception as exception_bp

def create_app():
    """
    Initializes the API.
    """
    app = Flask(__name__)
    db_name = 'clear_sky_finder_db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    register_extensions(app)
    register_blueprints(app)
    return app

def register_extensions(app:Flask):
    """
    Initializes extensions.
    """
    db.init_app(app)
    ma.init_app(app)
    
    return None

def register_blueprints(app:Flask):
    """
    Registers all blueprints.
    """
    parent = Blueprint('parent', __name__, url_prefix='/v1/')
    parent.register_blueprint(user_bp, url_prefix='/user/')
    parent.register_blueprint(track_bp, url_prefix='/track/')
    parent.register_blueprint(clouds_bp, url_prefix='/clouds/')
    parent.register_blueprint(exception_bp)
    app.register_blueprint(parent)
    return None

if __name__ == '__main__':
    app = create_app()
    app.run(port=8000, debug=True)
    