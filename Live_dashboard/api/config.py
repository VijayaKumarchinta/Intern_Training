import os
import sys
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

basedir = os.path.abspath(os.path.dirname(__file__))


class ProductionConfig:
    NAME = 'production'
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError("Missing required configuration: SECRET_KEY is not set.")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'postgresql+psycopg2://localhost/line_speed_30_prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = 'WARNING'
    MQTT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST', 'localhost')
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT', 1883))
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME', '')
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', '')
    MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'line/speed/30')
    MQTT_QOS = int(os.environ.get('MQTT_QOS', 1))

    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        return {
            "pool_pre_ping": True,
            "pool_size": 5,
            "max_overflow": 10,
        }


class TestingConfig:
    NAME = 'testing'
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = 'INFO'
    WTF_CSRF_ENABLED = False

    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        return {
            "pool_pre_ping": True,
            "pool_size": 2,
            "max_overflow": 5,
        }


config_by_name = {
    'production': ProductionConfig,
    'testing': TestingConfig,
}