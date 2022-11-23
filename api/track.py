from flask import Blueprint, jsonify
from sqlalchemy import exc
from flask_restful import Resource, request
import re
from extensions import db, ma
from user import User, UserSchema
from exceptions import APIException

track = Blueprint('track', __name__, template_folder='templates')

class Track(db.Model):
    """
    Database model for the User table
    """
    user_id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    zip = db.Column(db.Integer)
    lat = db.Column(db.Float(8), nullable=False)
    long = db.Column(db.Float(8), nullable=False)

    def __init__(self, user_id, city, state, zip):
        self.user_id = user_id
        self.city = city
        self.state = state
        self.zip = zip

class TrackSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'city', 'state', 'zip', 'lat', 'long')

class TrackManager(Resource):
    @track.route('/get', methods=['GET'])
    def get_tracked_locations():
        try:
            user_id = request.args['id']
        except Exception as _:
            user_id = None
        schema = TrackSchema(many=True)
        locations = Track.query.get(user_id)
        return jsonify(schema.dump(locations))
        
    @track.route('/post', methods=["POST"])
    def add_location():
        try:
            user_id = request.json['user_id']
        except KeyError:
            return jsonify({'Message': 'Error! user_id is required.'})
        user_schema = UserSchema()
        user = User.query.get(user_id)
        response = jsonify(user_schema.dump(user))
        if len(response.get_json()) == 0:
            raise APIException("User does not exist")
        
        user_id = request.json['user_id']
        try:
            city = request.json['city']
        except KeyError:
            city = ""
        try:
            state = request.json['state']
        except KeyError:
            state = ""
        try:
            zip = request.json['zip']
        except KeyError:
            zip = ""
        try:
            lat = request.json['lat']
        except KeyError:
            lat = None
        try:
            long = request.json['long']
        except KeyError:
            long = None
        
        if (not lat and not long) and ((city=="" and state=="") or zip == ""):
            raise APIException("Lat long or city, state, zip are required")

        if (not lat and not long):
            if city != "" and state != "":
                # TODO: Get zip, lat, long by city and state
                pass
            else:
                # TODO: Get city, state, lat, long by zip
                pass
        else:
            # TODO: Update city, state, zip by lat, long
            pass
        
        return jsonify({})

        

    @track.route('/test', methods=['GET'])
    def test():
        user_schema = UserSchema()
        user = User.query.get(0)
        response = jsonify(user_schema.dump(user))
        if len(response.get_json()) == 0:
            raise APIException("User does not exist")
        
        return jsonify(user_schema.dump(user))