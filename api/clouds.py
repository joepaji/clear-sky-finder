#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
This module contains the database model for the clouds table, routes
for /v1/clouds/ endpoint to interact with the database and functions to
add, update the cloud table based on data from the Openweathermap API.
"""
from flask import Blueprint, jsonify, escape
from sqlalchemy import exc
from sqlalchemy.sql.expression import select
from sqlalchemy.orm.attributes import flag_modified
from flask_restful import Resource, request
from pytz import timezone
from timezonefinder import TimezoneFinder
from datetime import datetime
from extensions import db, ma, session
from exceptions import APIException
from api_config import API_KEY
import requests
import aiohttp
import asyncio

clouds = Blueprint('clouds', __name__, template_folder='templates')

class Clouds(db.Model):
    """
    Database model for clouds table.
    """
    location_id = db.Column(db.Integer, primary_key = True)
    data = db.Column(db.JSON)

    def __init__(self, location_id, data):
        self.location_id = location_id
        self.data = data

class CloudsSchema(ma.Schema):
    class Meta: 
        fields = ('location_id', 'data')

class CloudsManager(Resource):
    """
    Routes for /v1/clouds/
    """
    @clouds.route('/get/', methods=['GET'])
    def get_clouds():
        """
        Gets cloud data for given location_id
        """
        try:
            location_id = request.args['location_id']
        except Exception as _:
            return jsonify({
                "Message": "Location id required"
            })
        schema = CloudsSchema(many=True)
        statement = select(Clouds).where(Clouds.location_id == location_id)
        data = session.execute(statement).scalars().all()  
        if not data:
            raise APIException(f"Location id \'{escape(location_id)}\' does not exist", 404)

        return jsonify(schema.dump(data))
    
    @clouds.route('/put/', methods=['PUT'])
    def update_clouds():
        """
        Updates cloud data for given user id.
        """
        try:
            user_id = request.args['id']
        except Exception as _:
            return jsonify({
                "Message": "User id required"
            })

        update_all_cloud_data(user_id)

        return jsonify({
            "Message": f"Cloud data updated for user id \'{escape(user_id)}\'"
        })

API_URL = 'https://api.openweathermap.org/data/3.0/onecall'

def get_timestamp(tz, hour):
    """
    Gets epoch timestamp for given hour.
    Inputs:
    tz: pytz timezone object
    """
    timestamp = datetime.now(tz).replace(hour=hour, minute=0, second=0, microsecond=0).timestamp()
    now = datetime.now(tz)
    current_timestamp = datetime.now(tz).replace(hour=now.hour, minute=0, second=0, microsecond=0).timestamp()
    return int(timestamp), timestamp<current_timestamp

def add_cloud_data(location_id, lat, long):
    """
    Adds cloud data for given location_id.
    This function is called when a new location is added to the track table.
    Inputs: 
    location_id
    lat: latitude
    long: longitude
    """
    cloud_data = get_cloud_data(lat, long)
    clouds = Clouds(location_id, cloud_data)
    try:
        session.add(clouds)
        session.commit()
    except exc.IntegrityError as err:
        session.rollback()
        raise APIException(f"Cloud data for location id \'{location_id}\' already exists. You may want to see update method instead.")

def get_cloud_data(lat, long):
    """
    Gets historical and current cloud data for given latitude and longitude.
    Inputs:
    lat: latitude
    long: longitude
    """
    params = {
        'lat': lat, 
        'lon': long, 
        'exclude': 'current,minutely,daily,alerts',    
        'appid': API_KEY
        }

    tf = TimezoneFinder()
    tz = tf.timezone_at(lat=lat, lng=long)
    tz1 = timezone(tz)
    response = requests.get(API_URL, params=params) 
    data_current = response.json()['hourly']
    timestamps = []
    
    # Get list of historical timestamps
    for i in range(18, 24):
        timestamp, historical = get_timestamp(tz1, i)
        if not historical:
            break
        timestamps.append(timestamp)    

    # Get historical cloud data in a list    
    cloud_data_list = asyncio.run(get_historical_data(timestamps, lat, long))
    
    # If 6pm is in the future, timestamps is empty and we have to get the index of 6pm

    start_index = 0

    if len(timestamps) == 0:
        six_timestamp = datetime.now(tz1).replace(hour=18, minute=0, second=0, microsecond=0).timestamp()
        for index, item in enumerate(data_current):
            if item['dt'] == int(six_timestamp):
                start_index = index
                break
    
    # Get current and future cloud data and append to original list
    end_index = start_index + 12
    for j in range(start_index, start_index+end_index):
        data_dict = generate_cloud_dict(data_current[j])
        cloud_data_list.append(data_dict)

    # Get next day cloud data
    next_day_start_index =  end_index + 12
    for k in range(next_day_start_index, next_day_start_index+13):
        data_dict = generate_cloud_dict(data_current[k])
        cloud_data_list.append(data_dict)
    
    # Convert list to dict {hourInt: dataDict}
    cloud_data_dict = {}
    for i in range(len(cloud_data_list)):
        cloud_data_dict[i] = cloud_data_list[i]

    return cloud_data_dict

def generate_cloud_dict(data):
    """
    Generates cloud dict given API data.
    Inputs:
    data: JSON/dict data from API
    """
    data_dict = {}
    data_dict['dt'] = data['dt']
    data_dict['clouds'] = data['clouds']
    data_dict['main'] = data['weather'][0]['main']
    data_dict['description'] = data['weather'][0]['description']
    
    return data_dict
    
async def get_historical_data(timestamps, lat, long):
    """
    async coroutine function to get historical data. 
    This will run a coroutine with each timestamp without waiting for each to finish
    This improves runtime of add location function.
    Inputs: 
    session: SQLAlchemy Session Object
    timestamp: Epoch timestamp to get data for
    lat: Latitude
    long: Longitude
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for timestamp in timestamps:
            task = asyncio.ensure_future(get_historical_data_helper(session, timestamp, lat, long))
            tasks.append(task)
        historical_data = await asyncio.gather(*tasks)
        
        return historical_data

async def get_historical_data_helper(session, timestamp, lat, long):
    """
    Function to perform the coroutine. 
    This is a helped for get_historical_data.
    Inputs: 
    session: SQLAlchemy Session Object
    timestamp: Epoch timestamp to get data for
    lat: Latitude
    long: Longitude
    """
    URL_HISTORICAL = API_URL + '/timemachine'
    params = {
                'lat': lat,
                'lon': long,
                'dt': timestamp,
                'appid': API_KEY
            }

    async with session.get(URL_HISTORICAL, params=params) as response:
        result_data = await response.json()
        result = result_data['data'][0]
        data_dict = generate_cloud_dict(result)

        return data_dict

def update_cloud_data(location_id, data_update):
    """
    Update cloud data for given location.
    Inputs: 
    location_id
    data_update: Updated data list from the API
    """
    cloud_data = session.get(Clouds, location_id)
    if not cloud_data:
        raise APIException(f"Location id \'{location_id}\' does not exist", 404)

    hour_index = datetime.now().hour
    for i in range(0, 24-hour_index):
        curr_data = cloud_data.data[str(hour_index)]
        new_data = generate_cloud_dict(data_update[i])
        # If curr data doesn't match the updated data, update the data.
        if curr_data != new_data:
            cloud_data.data[str(hour_index)] = new_data
        hour_index += 1
        
    # flag_modified allows us to let sqlalchemy know that we modified a JSON field
    flag_modified(cloud_data, "data")
    session.add(cloud_data)
    session.commit()

def update_all_cloud_data(user_id):
    """
    Updates cloud data for all locations for given user_id
    """
    # Importing here to avoid circular import issue as track.py imports cloud.py
    from track import Track
    statement = select(Track).where(Track.user_id == user_id)
    result = session.execute(statement).fetchall()
    if not result:
        raise APIException(f"User id \'{escape(user_id)}\' does not exist", 404)
    for location in result:
        params = {
        'lat': location[0].lat, 
        'lon': location[0].long, 
        'exclude': 'current,minutely,daily,alerts',    
        'appid': API_KEY
        }
        response = requests.get(API_URL, params=params)
        data_current = response.json()['hourly']
        update_cloud_data(location[0].location_id ,data_current)