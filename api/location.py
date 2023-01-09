#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
Location class used to manage get location function and location object.
This module gets and structures location data such as city,state,zip,lat,long.
"""
from flask import Blueprint, jsonify, escape
from flask_restful import Resource, request
import json
from geopy import Nominatim
from exceptions import APIException

location = Blueprint('location', __name__, template_folder='templates')

class Location:
    def __init__(self, city, state, zip, lat, long):
        self.city = city
        self.state = state
        self.zip = zip
        self.lat = lat
        self.long = long

class LocationManager(Resource):
    @location.route('/get', methods=['GET'])
    def get_lat_long():
        try:
            city = request.args['city']
            state = request.args['state']
        except Exception as _:
            return jsonify({
                "Message": "City, State required."
            })
        geolocator = Nominatim(user_agent='clear-sky-finder')
        location = geolocator.geocode(f"{city}, {state}")
        if not location: 
            raise APIException("City not found", 404)
        lat = location.latitude
        long = location.longitude
        location = geolocator.reverse(f"{lat},{long}")
        zip = location.raw['address']['postcode']
        location = Location(city, state, zip, lat, long)

        return {
            'lat': lat,
            'long': long,
            'city': city,
            'state': state,
            'zip': zip
        }

def get_location(city=None, state=None, zip=None, lat=None, long=None):
    """
    Get location by zip or city and state
    """
    geolocator = Nominatim(user_agent='clear-sky-finder')
    # Get location by zip
    if zip:
        location = geolocator.geocode(f"{zip}")
        lat = location.latitude
        long = location.longitude
        location = geolocator.reverse(f"{lat},{long}")
        city = location.raw['address']['city']
        state = location.raw['address']['state']
    # Get location by lat and long
    elif lat and long:
        if city == "" or state == "" or zip == "":
            location = geolocator.reverse(f"{lat},{long}")
            try:
                city = location.raw['address']['city']
            except KeyError:
                city = ""
            state = location.raw['address']['state']
            try:
                zip = location.raw['address']['postcode']
            except KeyError:
                zip = None
    # Get location by city and state
    elif city and state:
        location = geolocator.geocode(f"{city}, {state}")
        lat = location.latitude
        long = location.longitude
        location = geolocator.reverse(f"{lat},{long}")
        zip = location.raw['address']['postcode']
        
    location = Location(city, state, zip, lat, long)

    return location

def generate_unique_location_id(lat, long, user_id):
    """
    Generate a unique location id based on given coordinates and user_id.
    """
    try:
        lat_double = None
        lon_double = None
        if isinstance(lat, str):
            lat_double = float(lat)
        else:
            lat_double = lat
        if isinstance(long, str):
            lon_double = float(long)
        else:
            lon_double = long

        lat_int = int((lat_double * 1e7))
        lon_int = int((lon_double * 1e7))
        val = abs(lat_int + user_id << 16 & 0xffff0000 | lon_int + user_id & 0x0000ffff)
        val = val % 2147483647
        return val
    except Exception as e:
        print("marking OD_LOC_ID as -1 getting exception inside get_unique_number function")
        print("Exception while generating od loc id")
        print(e)
        return None