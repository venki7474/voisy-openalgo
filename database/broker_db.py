# database/broker_db.py

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import os
from utils.logging import get_logger
from cryptography.fernet import Fernet
import base64

logger = get_logger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and 'sqlite' in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={'check_same_thread': False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=50,
        max_overflow=100,
        pool_timeout=10
    )

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def _get_encryption_key():
    pepper = os.getenv('API_KEY_PEPPER', 'default-pepper-key')
    key = base64.urlsafe_b64encode(pepper.ljust(32)[:32].encode())
    return key

def _encrypt(data: str) -> str:
    if not data:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return encrypted.decode()

def _decrypt(encrypted_data: str) -> str:
    if not encrypted_data:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data.encode())
    return decrypted.decode()

class Broker(Base):
    __tablename__ = 'brokers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    broker_name = Column(String(100), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    status = Column(Boolean, default=True)
    user = relationship("User", backref="brokers")

def init_db():
    from database.db_init_helper import init_db_with_logging
    init_db_with_logging(Base, engine, "Broker DB", logger)

def add_broker(user_id, broker_name, api_key, api_secret):
    broker = Broker(
        user_id=user_id,
        broker_name=broker_name,
        api_key_encrypted=_encrypt(api_key),
        api_secret_encrypted=_encrypt(api_secret)
    )
    db_session.add(broker)
    db_session.commit()
    return broker

def get_broker(user_id, broker_identifier):
    if isinstance(broker_identifier, int):
        broker = Broker.query.filter_by(user_id=user_id, id=broker_identifier).first()
    else:
        broker = Broker.query.filter_by(user_id=user_id, broker_name=broker_identifier).first()

    if broker:
        return {
            'id': broker.id,
            'user_id': broker.user_id,
            'broker_name': broker.broker_name,
            'api_key': _decrypt(broker.api_key_encrypted),
            'api_secret': _decrypt(broker.api_secret_encrypted),
            'status': broker.status
        }
    return None

def get_all_brokers(user_id):
    brokers = Broker.query.filter_by(user_id=user_id).all()
    return [{
        'id': broker.id,
        'user_id': broker.user_id,
        'broker_name': broker.broker_name,
        'api_key': _decrypt(broker.api_key_encrypted),
        'api_secret': _decrypt(broker.api_secret_encrypted),
        'status': broker.status
    } for broker in brokers]

def update_broker_status(user_id, broker_name, status):
    broker = Broker.query.filter_by(user_id=user_id, broker_name=broker_name).first()
    if broker:
        broker.status = status
        db_session.commit()
        return True
    return False

def delete_broker(broker_id):
    broker = Broker.query.get(broker_id)
    if broker:
        db_session.delete(broker)
        db_session.commit()
        return True
    return False
