from os import path

from decouple import config


BASEDIR = path.abspath(path.dirname(__file__))

# Connect to the database
DB_HOST = config("DB_HOST")
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_PORT = config("DB_PORT", cast=int)
SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}:{}/{}".format(
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {"isolation_level": "READ COMMITTED"}
