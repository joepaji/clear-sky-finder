#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
Code for routes and database for the '/v1/user' endpoint.
"""

from flask import Blueprint, jsonify, escape
from sqlalchemy import exc
from sqlalchemy.sql.expression import select
from flask_restful import Resource, request
from extensions import db, ma, session
from exceptions import APIException
import re

user = Blueprint('user', __name__, template_folder='templates')

class User(db.Model):
    """
    Database model for the User table
    """
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(32))
    first_name = db.Column(db.String(32))
    last_name = db.Column(db.String(32))

    def __init__(self, email, username, password, first_name, last_name):
        self.email = email
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name

class UserSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'email', 'username', 'password', 'first_name', 'last_name')

class UserManager(Resource):
    """
    API calls pertaining to /api/v1/user/
    """
    @user.route('/get/', methods = ['GET'])
    #@user.route('/get/<user_id>', methods = ['GET'])
    def get_user(user_id=None):
        try:
            user_id = request.args['id']
        except Exception as _:
            user_id = None     
        user_schema = UserSchema()
        users_schema =UserSchema(many=True)
        if not user_id:
            statement = select(User)
            users = session.execute(statement).scalars().all()
            return jsonify(users_schema.dump(users))
        user = session.get(User, user_id)
        if not user:
            raise APIException("User does not exist", 404)
        return jsonify(user_schema.dump(user))

    @user.route('/post/', methods = ['POST'])
    def add_user():
        email = request.json['email']
        username = request.json['username']
        password = request.json['password']
        first_name = request.json['first_name']
        last_name = request.json['last_name']

        user = User(email, username, password, first_name, last_name)

        try:
            session.add(user)
            session.commit()
        except exc.IntegrityError as err:
            session.rollback()
            errorInfo = err.orig.args
            message = errorInfo[1]
            email = re.findall('\'(.+?)\'', message)
            if email:
                value = email[0]
                key = email[1].split('.')[1]
            return jsonify({
                'Message': f'Error! User with {key} \'{value}\' already exists.'
            })

        return jsonify({
            'Message': f'User {escape(username)} has been inserted.'
        })
    
    @user.route('/put/', methods=['PUT'])
    def update_user():
        try:
            id = request.args['id']
        except Exception as _:
            id = None
        
        if not id:
            return jsonify({'Message': 'Must provide user ID'})
        
        user = session.get(User, id)

        try:
            email = request.json['email']
        except Exception as _:
            email = user.email
        try:
            password = request.json['password']
        except Exception as _:
            password = user.password
        try:
            first_name = request.json['first_name']
        except Exception as _:
            first_name = user.first_name
        try:
            last_name = request.json['last_name']
        except Exception as _:
            last_name = user.last_name
        
        user.email = email
        user.password = password
        user.first_name = first_name
        user.last_name = last_name

        session.commit()

        return jsonify({
            'Message': f'User {user.username} altered'
        })

    @user.route('/delete/', methods=['DELETE'])
    def delete_user():
        try:
            id = request.args['id']
        except Exception as _: 
            id = None
        
        if not id:
            return jsonify({
                'Message': 'Must provide user ID to delete'
            })
        
        user = session.get(User, id)
        if not user:
            raise APIException("User does not exist", 404)
        
        session.delete(user)
        session.commit()

        return jsonify({
            'Message': f'User {escape(id)} deleted'
        })