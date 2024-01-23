import json
import os

import jwt

from flask import Blueprint, request, redirect, current_app
from ..db import DBClient
from ..utils import APIUtils
from managers import S3Manager
from logger import createLog

logger = createLog(__name__)

fulfill = Blueprint("fulfill", __name__, url_prefix="/fulfill")


@fulfill.route("/<link_id>", methods=["GET"])
def itemFulfill(link_id):
    with DBClient(current_app.config["DB_CLIENT"]) as dbClient:
        link = dbClient.fetchSingleLink(link_id)
        if not link:
            return APIUtils.formatResponseObject(
                404, "fulfill", "No link exists for this ID"
            )

        requires_authorization = (
            # Might not have edd flag if edd is not true
            link.flags.get("edd", False) is False and link.flags["nypl_login"] is True
        )

        if requires_authorization:
            decodedToken = None
            try:
                bearer = request.headers.get("Authorization")
                if bearer is None:
                    return APIUtils.formatResponseObject(
                        401,
                        "fulfill",
                        "Invalid access token",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                token = bearer.split()[1]

                jwt_secret = os.environ["NYPL_API_CLIENT_PUBLIC_KEY"]
                decodedToken = jwt.decode(
                    token, jwt_secret, algorithms=["RS256"], audience="app_myaccount"
                )

            except jwt.exceptions.ExpiredSignatureError:
                return APIUtils.formatResponseObject(
                    401,
                    "fulfill",
                    "Expired access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except (
                jwt.exceptions.DecodeError,
                UnicodeDecodeError,
                IndexError,
                AttributeError,
            ):
                return APIUtils.formatResponseObject(
                    401,
                    "fulfill",
                    "Invalid access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if decodedToken["iss"] == "https://www.nypl.org":
                storageManager = S3Manager()
                storageManager.createS3Client()
                presignedObjectUrl = APIUtils.getPresignedUrlFromObjectUrl(
                    storageManager.s3Client, link.url
                )
                return redirect(presignedObjectUrl)
            else:
                return APIUtils.formatResponseObject(
                    401,
                    "fulfill",
                    "Invalid access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        else:
            # TODO: In the future, this could record an analytics timestamp
            # and redirect to URL of an item if authentication is not required.
            # For now, only use /fulfill endpoint in response if authentication is required.
            return APIUtils.formatResponseObject(400, "fulfill", "Bad request")
