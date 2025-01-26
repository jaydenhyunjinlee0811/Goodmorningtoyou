import boto3
import os 
import psycopg2 as pg

class Parser(object):
    def __init__(
        self,
        access_key_id: str,
        access_key_pwd: str,
        db_host: str,
        db_port: str,
        db_name: str,
        db_user: str,
        db_pwd: str
    ):
        self.access_key_id = access_key_id
        self.access_key_pwd = access_key_pwd