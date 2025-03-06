import redis
import os
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv()) # read local .env file

def get_conn():
    redis_host=os.environ['REDIS_HOST']
    redis_password=os.environ['REDIS_PASSWORD']
    redis_port=os.environ['REDIS_PORT']
    if os.environ['REDIS_SELECT']:
        redis_select=os.environ['REDIS_SELECT']
    else:
        redis_select=0
    pool = redis.ConnectionPool(host=redis_host, port=int(redis_port), password=redis_password,db=redis_select, decode_responses=True)
    return redis.Redis(connection_pool=pool)

