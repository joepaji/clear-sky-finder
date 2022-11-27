#!/usr/bin/env python3
# ------------------------------------------------------------------
# Created By : Joheb Rahman
# Created Date: 11/22/2022
# version = '0.10'
# ------------------------------------------------------------------
"""
This module contains the class for a custom APIException and its exception handler.
"""
from flask import Blueprint, jsonify

exception = Blueprint('exception', __name__, template_folder='templates')

class APIException(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code

@exception.app_errorhandler(APIException)
def exception_handler(e):
    response = jsonify({'Message': str(e)})
    response.status_code = e.status_code
    return response