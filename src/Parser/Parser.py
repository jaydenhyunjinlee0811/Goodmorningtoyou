import datetime
import boto3
import os 
import json
import sys
import psycopg2 as pg
from typing import List, Dict

from ..utils import get_logger 

class Parser(object):
    def __init__(
        self,
        access_key_id: str,
        access_key_pwd: str,
        bucket_name: str,
        db_host: str,
        db_port: str,
        db_name: str,
        db_user: str,
        db_pwd: str,
        logger_fp: str=None
    ):
        self.access_key_id = access_key_id
        self.access_key_pwd = access_key_pwd
        self.bucket_name = bucket_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_pwd = db_pwd

        self.logger = get_logger(logger_fp)
        self.stg_data: Dict[str, List[Dict[str, str]]] = {
            'news': list(),
            'onthisday': list()
        }

    def extract(self):
        self.logger.info('Extracting staged data from Minio buckets..')
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9010',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_pwd
        )
        # dt = datetime.datetime.now()
        dt = datetime.datetime(2025,1,23)
        dt_key = datetime.datetime.strftime(dt, '%Y%m%d')

        response = client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=f'news/{dt_key}'
        )
        contents = response.get('Contents', [])

        # If Bucket is empty
        if not contents:
            self.logger.info('No data could be found from staging bucket, aborting..')
            sys.exit(1)
        
        for content in contents:
            key = content['Key']
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            data = response['Body'].read().decode('utf-8')

            # JSON-ify the decoded content into List[Dict[str, dict]]
            parsed_data = json.loads(data)
            self.stg_data['news'].append(parsed_data)
        
        self.logger.info('Extraction result from Bucket(%s/%s): [%s] files', self.bucket_name, f'news/{dt_key}', len(self.stg_data))

    def parse(self):
        ...

    def ingest(self):
        ...