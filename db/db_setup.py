# db/db_setup.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from db.models import db

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
