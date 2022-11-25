#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/24/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
Location class used to manage get location function and location object
"""
from geopy import Nominatim
from pairing_functions import cantor

class Location:
    def __init__(self, city, state, zip, lat, long):
        self.city = city
        self.state = state
        self.zip = zip
        self.lat = lat
        self.long = long
    
def get_location(city=None, state=None, zip=None, lat=None, long=None):
    """
    Get location by zip or city and state
    """
    geolocator = Nominatim(user_agent='clear-sky-finder')
    if zip:
        location = geolocator.geocode(f"{zip}")
        lat = location.latitude
        long = location.longitude
        location = geolocator.reverse(f"{lat},{long}")
        city = location.raw['address']['city']
        state = location.raw['address']['state']
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
    Generate a unique location id based on given coordinates.
    """
    lat = cantor.pair(abs(int(float(lat))),int(user_id))
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
        val = abs(lat_int << 16 & 0xffff0000 | lon_int & 0x0000ffff)
        val = val % 2147483647
        return val
    except Exception as e:
        print("marking OD_LOC_ID as -1 getting exception inside get_unique_number function")
        print("Exception while generating od loc id")
        print(e)
        return None