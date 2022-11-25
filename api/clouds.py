from flask import Blueprint, jsonify, escape
from sqlalchemy import exc
from sqlalchemy.sql.expression import select
from flask_restful import Resource, request
from geopy import Nominatim
from extensions import db, ma, session
from user import User
from track import Track
from exceptions import APIException
import re

clouds = Blueprint('clouds', __name__, template_folder='templates')

class Clouds(db.Model):
    """
    Database model for weatherdata table
    """
    location_id = db.Column(db.Integer, primary_key = True)
    hour1 = db.Column(db.JSON(120))
    hour2 = db.Column(db.JSON(120))
    hour3 = db.Column(db.JSON(120))
    hour4 = db.Column(db.JSON(120))
    hour5 = db.Column(db.JSON(120))
    hour6 = db.Column(db.JSON(120))
    hour7 = db.Column(db.JSON(120))
    hour8 = db.Column(db.JSON(120))
    hour9 = db.Column(db.JSON(120))
    hour10 = db.Column(db.JSON(120))

    def __init__(self, location_id, hour1, hour2, hour3, hour4, hour5, hour6, hour7, hour8, hour9, hour10):
        self.location_id = location_id
        self.hour1 = hour1
        self.hour2 = hour2
        self.hour3 = hour3
        self.hour4 = hour4
        self.hour5 = hour5
        self.hour6 = hour6
        self.hour7 = hour7
        self.hour8 = hour8 
        self.hour9 = hour9
        self.hour10 = hour10

class CloudsSchema(ma.Schema):
    class Meta: 
        fields = ('location_id', 'hour1', 'hour2', 'hour3', 'hour4', 'hour5', 'hour6', 'hour7', 'hour8', 'hour9', 'hour10')

class CloudsManager(Resource):
    @clouds.route('/get/', methods=['GET'])
    def get_clouds():
        try:
            location_id = request.args['location_id']
        except Exception as _:
            return jsonify({
                "Message": "Location id required"
            })
        schema = CloudsSchema(many=True)
        statement = select(Clouds).where(Clouds.location_id == location_id)
        data = session.execute(statement).scalars().all()
        return jsonify(schema.dump(data))


# Look at api and determine what data to keep

# Add timezone offset function

# Add data to database by location_id

# Add data to database by 