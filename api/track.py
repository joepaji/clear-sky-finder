#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/23/2022
# version = '0.10'
# ------------------------------------------------------------------
from flask import Blueprint, jsonify, escape
from sqlalchemy import exc
from sqlalchemy.sql.expression import select
from flask_restful import Resource, request
from geopy import Nominatim
import re
from extensions import db, ma, session
from user import User
from location import get_location, generate_unique_location_id
from exceptions import APIException

track = Blueprint('track', __name__, template_folder='templates')

class Track(db.Model):
    """
    Database model for the User table
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
    @track.route('/get', methods=['GET'])
    def get_tracked_locations():
        try:
            user_id = request.args['id']
        except Exception as _:
            return jsonify({
                "Message": "User id required"
            })
        schema = TrackSchema(many=True)
        statement = select(Track).where(Track.user_id == user_id)
        locations = session.execute(statement).scalars().all()
        return jsonify(schema.dump(locations))
        
    @track.route('/post/', methods=["POST"])
    def add_location():
        try:
            user_id = request.args['user_id']
        except KeyError:
            return jsonify({'Message': 'Error! user_id is required.'})
        
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
                "Message": f"Location id {id[0]} already exists",
            })

        return jsonify({
            "Message": f"Inserted location id {location_id}"
        })

    @track.route('/delete/', methods=['DELETE'])
    def remove_location():
        try:
            location_id = request.args['location_id']
        except Exception as _:
            return jsonify({
                "Message": f"location_id is required"
            })
        location = session.get(Track, location_id)
        if not location:
            return jsonify({
                "Message": f"Location id {escape(location_id)} does not exist in the watchlist"
            })
        session.delete(location)
        session.commit()

        return jsonify({
            "Message": f"Location id {escape(location_id)} has been removed"
        })

    @track.route('/test/', methods=['GET'])
    def test():
        geolocator = Nominatim(user_agent='clear-sky-finder')
        result = geolocator.geocode("Laveen, AZ")
        lat = result.latitude
        long = result.longitude
        result = geolocator.reverse(f"{lat},{long}")
        lat = 33.3618813
        long = -112.1533861
        location_id = generate_unique_location_id(lat, long, 1)
        
        return jsonify({
            "Message": str(result),
            "City": result.raw['address']['city'],
            "State": result.raw['address']['state'],
            "Zip": result.raw['address']['postcode'],
            "lat:": lat,
            "long": long,
            "Location ID": location_id
        })