from os import getenv, path

basedir = path.abspath(path.dirname(__file__))


class Config(object):

    # ==== POSTGRES / SQLALCHEMY ====
    DBUSERNAME = getenv("POSTGRES_USER", "doctrina")
    DBPASSWORD = getenv("POSTGRES_PASSWORD")

    DBDATABASE = getenv("POSTGRES_DB", "doctrina")

    DBHOST = getenv("POSTGRES_HOST", "postgres")
    DBPORT = getenv("POSTGRES_PORT", "5432")

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DBUSERNAME}:{DBPASSWORD}@{DBHOST}:{DBPORT}/{DBDATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATABASE_DEBUG = False
    DATABASE_VERBOSE = False

    # ==== REDIS ====
    REDIS_URL = getenv("REDIS_URL", "redis://NOT_SET")

    # ==== SESSIONS ====
    SECRET_KEY = b"\xbdOhV3\x93\x1e\x1a\xca\xdb/\xd0"
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # ==== FLASK DEBUG ====
    FLASK_ENV = "development"
    DEBUG = True

    # ==== Doctrina ====
    DEMO_MODE = True

    # ==== File Upload ====
    UPLOAD_FOLDER = path.join(basedir, "static")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    MAX_CONTENT_PATH = 50  # 50 chars long
