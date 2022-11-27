from flask import Blueprint, jsonify, escape
from sqlalchemy import exc
from sqlalchemy.sql.expression import select
from flask_restful import Resource, request
from pytz import timezone
from timezonefinder import TimezoneFinder
from datetime import datetime
from extensions import db, ma, session
from track import Track
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
    hour0 = db.Column(db.JSON(120))
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
    hour11 = db.Column(db.JSON(120))
    hour12 = db.Column(db.JSON(120))
    hour13 = db.Column(db.JSON(120))
    hour14 = db.Column(db.JSON(120))
    hour15 = db.Column(db.JSON(120))
    hour16 = db.Column(db.JSON(120))
    hour17 = db.Column(db.JSON(120))
    hour18 = db.Column(db.JSON(120))
    hour19 = db.Column(db.JSON(120))
    hour20 = db.Column(db.JSON(120))
    hour21 = db.Column(db.JSON(120))
    hour22 = db.Column(db.JSON(120))
    hour23 = db.Column(db.JSON(120))

    def __init__(self, location_id, hour0, hour1, hour2, hour3, hour4, hour5,\
         hour6, hour7, hour8, hour9, hour10, hour11, hour12, hour13, hour14, \
            hour15, hour16, hour17, hour18, hour19, hour20, hour21, hour22, \
                hour23):
        self.location_id = location_id
        self.hour0 = hour0
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
        self.hour11 = hour11
        self.hour12 = hour12
        self.hour13 = hour13
        self.hour14 = hour14
        self.hour15 = hour15
        self.hour16 = hour16
        self.hour17 = hour17
        self.hour18 = hour18
        self.hour19 = hour19
        self.hour20 = hour20
        self.hour21 = hour21
        self.hour22 = hour22
        self.hour23 = hour23
       

class CloudsSchema(ma.Schema):
    class Meta: 
        fields = ('location_id', 'hour0', 'hour1', 'hour2', 'hour3', 'hour4', \
            'hour5', 'hour6', 'hour7', 'hour8', 'hour9', 'hour10', 'hour11', \
                'hour12', 'hour13', 'hour14', 'hour15', 'hour16', 'hour17', \
                    'hour18', 'hour19', 'hour20', 'hour21', 'hour22', 'hour23')

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
        add_cloud_data(location_id)  
        return jsonify(schema.dump(data))
    
    
    #@clouds.route('/post/', methods=['POST'])
    #def add_cloud_data():
     #   pass


# Look at api and determine what data to keep

# Add timezone offset function
def get_timestamp(tz, hour):
    timestamp = datetime.now(tz).replace(hour=hour, minute=0, second=0, microsecond=0).timestamp()
    now = datetime.now(tz)
    current_timestamp = datetime.now(tz).replace(hour=now.hour, minute=0, second=0, microsecond=0).timestamp()
    return int(timestamp), timestamp<current_timestamp

def add_cloud_data(location_id):
    data = session.get(Track, location_id)
    if not data:
        raise APIException(f"Location id {location_id} not found", 404)
    cloud_data = get_cloud_data(location_id)
    hourly = {}
    
    for i in range(len(cloud_data)):
        hourly[i] = cloud_data[i]
    
    clouds = Clouds(location_id, hourly[0], hourly[1], hourly[2], hourly[3], hourly[4], hourly[5], \
        hourly[6], hourly[7], hourly[8], hourly[9], hourly[10], hourly[11], hourly[12], hourly[13], \
            hourly[14], hourly[15], hourly[16], hourly[17], hourly[18], hourly[19], hourly[20], \
                hourly[21], hourly[22], hourly[23])

    
    try:
        session.add(clouds)
        session.commit()
    except exc.IntegrityError as err:
        session.rollback()
        raise APIException(f"Cloud data for location id {location_id} already exists. You may want to see update method instead.")

def get_cloud_data(location_id):
    API_URL = 'https://api.openweathermap.org/data/3.0/onecall'
    statement = select(Track).where(Track.location_id == location_id)
    data = session.execute(statement).fetchone()
    if data == None:
        raise APIException(f"Location id {location_id} does not exist")
    lat = data[0].lat
    long = data[0].long

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
    cloud_data = []
    
    timestamps = []
    for i in range(0, 24):
        timestamp, historical = get_timestamp(tz1, i)
        timestamps.append(timestamp)    
        if not historical:
            break
    
    cloud_data = asyncio.run(get_historical_data(timestamps, lat, long))

    for j in range(0, 24-i):
        add_data = generate_cloud_dict(data_current[j])
        cloud_data.append(add_data)
    
    return cloud_data

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
    URL_HISTORICAL = 'https://api.openweathermap.org/data/3.0/onecall/timemachine'
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
# Add data to database by location_id

# Add data to database by 