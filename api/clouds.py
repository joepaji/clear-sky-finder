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
    
    
    #@clouds.route('/post/', methods=['POST'])
    #def add_cloud_data():
     #   pass


# Look at api and determine what data to keep

# Add timezone offset function
def get_timestamp(lat,long):
    tf = TimezoneFinder()
    tz = tf.timezone_at(lat=lat, lng=long)
    tz1 = timezone(tz)
    timestamp = datetime.now(tz1).replace(hour=20, minute=0, second=0, microsecond=0).timestamp()

    return int(timestamp)

def add_cloud_data(location_id):
    data = session.get(Track, location_id)
    if not data:
        raise APIException(f"Location id {location_id} not found", 404)
    cloud_data = get_cloud_data(location_id)
    hourly = {}
    hour = 1
    for data in cloud_data:
        hourly[hour] = data
        hour += 1

    clouds = Clouds(location_id, hourly[1], hourly[2], hourly[3], hourly[4], hourly[5], \
        hourly[6], hourly[7], hourly[8], hourly[9], hourly[10])

    try:
        session.add(clouds)
        session.commit()
    except exc.IntegrityError as err:
        session.rollback()
        raise APIException("Error occurred trying to insert cloud data.")
    
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

    response = requests.get(API_URL, params=params) 
    data = response.json()['hourly']
    timestamp = get_timestamp(lat, long)

    for i in range(len(data)):
        if data[i]['dt'] == timestamp:
            break
    
    start_index = i 
    cloud_data = []
    while i<start_index+10:
        data_dict = {}
        data_dict['dt'] = data[i]['dt']
        data_dict['clouds'] = data[i]['clouds']
        data_dict['main'] = data[i]['weather'][0]['main']
        data_dict['description'] = data[i]['weather'][0]['description']
        cloud_data.append((data_dict))
        i+=1
    
    return cloud_data
    
    
    
    
    
# Add data to database by location_id

# Add data to database by 