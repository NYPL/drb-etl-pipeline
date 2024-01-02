import json
import os

import jwt

from flask import Blueprint, request
from ..utils import APIUtils
from logger import createLog

JWT_ALGORITHM = ''
logger = createLog(__name__)

fulfill = Blueprint('fulfill', __name__, url_prefix='/fulfill')

@fulfill.route('/<uuid>', methods=['GET'])
def workFulfill(uuid):
    logger.info('Checking if authorization is needed for work {}'.format(uuid))

    requires_authorization = True

    if requires_authorization:
        try:
            bearer = request.headers.get('Authorization')
            token = bearer.split()[1]

            jwt_secret = os.environ['NYPL_API_CLIENT_PUBLIC_KEY']
            decoded_token =(jwt.decode(token, jwt_secret, 'RS256', 
                                   audience="app_myaccount"))
            if json.loads(json.dumps(decoded_token))['iss'] == "https://www.nypl.org":
                statusCode = 200
                responseBody = uuid
            else:
                statusCode = 401
                responseBody = 'Invalid access token'

        except jwt.exceptions.ExpiredSignatureError:
            statusCode = 401
            responseBody = 'Expired access token'
        except (jwt.exceptions.DecodeError, UnicodeDecodeError, IndexError, AttributeError):
            statusCode = 401
            responseBody = 'Invalid access token'
        except ValueError:
            logger.warning("Could not deserialize NYPL-issued public key")
            statusCode = 500
            responseBody = 'Server error'
    
    else:
        # TODO: In the future, this could record an analytics timestamp
        # and redirect to URL of a work if authentication is not required. 
        # For now, only use /fulfill endpoint in response if authentication is required.
        statusCode = 400
        responseBody = "Bad Request"

    response = APIUtils.formatResponseObject(
        statusCode, 'fulfill', responseBody
    )

    if statusCode == 401:
        response[0].headers['WWW-Authenticate'] = 'Bearer'

    return response

