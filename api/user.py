#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
Code for routes and database for the '/v1/user' endpoint.
"""

from flask import Flask, Blueprint, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Resource, request, Api
from extensions import db, ma

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
    @user.route('/get/<user_id>', methods = ['GET'])
    def get_user(user_id=None):     
        user_schema = UserSchema()
        users_schema =UserSchema(many=True)
        if not user_id:
            users = User.query.all()
            return jsonify(users_schema.dump(users))
        user = User.query.get(user_id)
        return jsonify(user_schema.dump(user))

    @user.route('/post', methods = ['POST'])
    def add_user():
        email = request.json['email']
        username = request.json['username']
        password = request.json['password']
        first_name = request.json['first_name']
        last_name = request.json['last_name']

        user = User(email, username, password, first_name, last_name)

        db.session.add(user)
        db.session.commit()

        return jsonify({
            'Message': f'User {username} has been inserted.'
        })