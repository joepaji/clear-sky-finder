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
    Database model for weatherdata table
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
    
    @clouds.route('/put/', methods=['PUT'])
    def update_clouds():
        try:
            user_id = request.args['id']
        except Exception as _:
            return jsonify({
                "Message": "Location id required"
            })
        update_all_cloud_data(user_id)
        return jsonify({
            "Message": f"Cloud data updated for user id {escape(user_id)}"
        })
    @clouds.route('/test/', methods=['GET'])
    def test():
        try:
            user_id = request.args['id']
        except Exception as _:
            return jsonify({
                "Message": "User id required"
            })

        update_all_cloud_data(user_id)
        
        return jsonify({
            "Message": "OK"
        })
    #@clouds.route('/post/', methods=['POST'])
    #def add_cloud_data():
     #   pass


# Look at api and determine what data to keep

# Add timezone offset function
API_URL = 'https://api.openweathermap.org/data/3.0/onecall'

def get_timestamp(tz, hour):
    timestamp = datetime.now(tz).replace(hour=hour, minute=0, second=0, microsecond=0).timestamp()
    now = datetime.now(tz)
    current_timestamp = datetime.now(tz).replace(hour=now.hour, minute=0, second=0, microsecond=0).timestamp()
    return int(timestamp), timestamp<current_timestamp

def add_cloud_data(location_id, lat, long):
    #data = session.get(Track, location_id)
    #if not data:
    #    raise APIException(f"Location id {location_id} not found", 404)
    cloud_data = get_cloud_data(lat, long)
   
    clouds = Clouds(location_id, cloud_data)
    try:
        session.add(clouds)
        session.commit()
    except exc.IntegrityError as err:
        session.rollback()
        raise APIException(f"Cloud data for location id {location_id} already exists. You may want to see update method instead.")

def get_cloud_data(lat, long):
    #statement = select(Track).where(Track.location_id == location_id)
    #data = session.execute(statement).fetchone()
    #if data == None:
    #    raise APIException(f"Location id {location_id} does not exist")
    #lat = data[0].lat
    #long = data[0].long

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
    for i in range(0, 24):
        timestamp, historical = get_timestamp(tz1, i)
        if not historical:
            break
        timestamps.append(timestamp)    
        
    cloud_data_list = asyncio.run(get_historical_data(timestamps, lat, long))
    for j in range(0, 24-i):
        data_dict = generate_cloud_dict(data_current[j])
        cloud_data_list.append(data_dict)
    
    cloud_data_dict = {}
    for i in range(len(cloud_data_list)):
        cloud_data_dict[i] = cloud_data_list[i]

    return cloud_data_dict

def generate_cloud_dict(data):
    data_dict = {}
    data_dict['dt'] = data['dt']
    data_dict['clouds'] = data['clouds']
    data_dict['main'] = data['weather'][0]['main']
    data_dict['description'] = data['weather'][0]['description']
    
    return data_dict
    
async def get_historical_data(timestamps, lat, long):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for timestamp in timestamps:
            task = asyncio.ensure_future(get_historical_data_helper(session, timestamp, lat, long))
            tasks.append(task)
        historical_data = await asyncio.gather(*tasks)
        
        return historical_data

async def get_historical_data_helper(session, timestamp, lat, long):
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

def update_cloud_data(location_id, data_current):
    cloud_data = session.get(Clouds, location_id)
    if not cloud_data:
        raise APIException(f"Location id {location_id} not found")
    hour_index = datetime.now().hour
    for i in range(0, 24-hour_index):
        curr_data = cloud_data.data[str(hour_index)]
        new_data = generate_cloud_dict(data_current[i])
        if curr_data != new_data:
            cloud_data.data[str(hour_index)] = new_data
        hour_index += 1
    flag_modified(cloud_data, "data")
    session.add(cloud_data)
    session.commit()

def update_all_cloud_data(user_id):
    from track import Track
    statement = select(Track).where(Track.user_id == user_id)
    result = session.execute(statement).fetchall()

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