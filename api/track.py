#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
This module contains the database model for the track table and routes
for /v1/track/ endpoint to interact with the database. This module adds 
a new location to the tracked list and adds the data in the Clouds table
for that location as well.
"""
from flask import Blueprint, jsonify, escape
from sqlalchemy import exc
from sqlalchemy.sql.expression import select
from flask_restful import Resource, request
from geopy import Nominatim
from extensions import db, ma, session
from user import User
from clouds import Clouds, add_cloud_data
from location import get_location, generate_unique_location_id
from exceptions import APIException
import re

track = Blueprint('track', __name__, template_folder='templates')

class Track(db.Model):
    """
    Database model for the Track table.
    """
    location_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    zip = db.Column(db.Integer)
    lat = db.Column(db.Float(8), nullable=False)
    long = db.Column(db.Float(8), nullable=False)

    def __init__(self, location_id, user_id, city, state, zip, lat, long):
        self.location_id = location_id
        self.user_id = user_id
        self.city = city
        self.state = state
        self.zip = zip
        self.lat = lat
        self.long = long

class TrackSchema(ma.Schema):
    class Meta:
        fields = ('location_id', 'user_id', 'city', 'state', 'zip', 'lat', 'long')

class TrackManager(Resource):
    """
    Routes for /v1/track/
    """
    @track.route('/get', methods=['GET'])
    def get_tracked_locations():
        """
        Gets all tracked locations for given user id.
        """
        try:
            user_id = request.args['id']
        except Exception as _:
            return jsonify({
                "Message": "User id required"
            })
        user = session.get(User, user_id)
        if not user:
            raise APIException("User does not exist", 404)
        schema = TrackSchema(many=True)
        statement = select(Track).where(Track.user_id == user_id)
        locations = session.execute(statement).scalars().all()
        
        return jsonify(schema.dump(locations))
        
    @track.route('/post/', methods=["POST"])
    def add_location():
        """
        Add a new location to the track table for given user id.
        """
        try:
            user_id = request.args['id']
        except KeyError:
            return jsonify({'Message': 'Error! id is required.'})
        
        user = session.get(User, user_id)
        if not user:
            raise APIException("User does not exist", 404)

        try:
            city = request.args['city']
        except KeyError:
            city = ""
        try:
            state = request.args['state']
        except KeyError:
            state = ""
        try:
            zip = request.args['zip']
        except KeyError:
            zip = None
        try:
            lat = request.args['lat']
        except KeyError:
            lat = None
        try:
            long = request.args['long']
        except KeyError:
            long = None
        
        # Check if at least one correct input combination is given
        # Should accept if zip or (lat and long) or (city and state) are provided
        if not (lat and long) and not zip:
            if (city=="" and state=="") or (city=="" and state != "") or (city!="" and state==""):
                raise APIException("Lat long or city, state, zip are required")

        if zip:
            # Get location by zip code
            l = get_location(zip=zip)
        elif (not lat and not long):
            # Get location by city and state
            l = get_location(city, state)
        else:
            # Get location by lat and long
            l = get_location(lat=lat, long=long)

        location_id = generate_unique_location_id(l.lat, l.long, int(user_id))
        track = Track(location_id, user_id, l.city, l.state, l.zip, l.lat, l.long)

        try:
            session.add(track)
            session.commit()
        except exc.IntegrityError as err:
            session.rollback()
            errorInfo = err.orig.args
            message = errorInfo[1]
            id = re.search('\'(.+?)\'', message)
            return jsonify({
                "Message": f"Location id \'{id[0]}\' already exists",
            })
        # Add cloud data for this new location_id
        add_cloud_data(location_id, l.lat, l.long)

        return jsonify({
            "Message": f"Inserted location id \'{location_id}\'"
        })

    @track.route('/delete/', methods=['DELETE'])
    def remove_location():
        """
        Removes location and corresponding cloud data from the track and cloud tables.
        """
        try:
            location_id = request.args['location_id']
        except Exception as _:
            return jsonify({
                "Message": f"location_id is required"
            })
        location = session.get(Track, location_id)
        cloud_data = session.get(Clouds, location_id)
        if not location:
            return jsonify({
                "Message": f"Location id \'{escape(location_id)}\' does not exist in the watchlist"
            })
        session.delete(location)
        session.delete(cloud_data)
        session.commit()

        return jsonify({
            "Message": f"Location id \'{escape(location_id)}\' has been removed"
        })