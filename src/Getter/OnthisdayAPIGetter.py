import sys
import requests
from bs4 import BeautifulSoup
import json
import boto3
import botocore
import datetime

from .GetterInterface import GetterInterface

class OnthisdayAPIGetter(GetterInterface):
    def __init__(
        self, 
        source_endpoint: str, 
        bucket_name: str,
        bucket_key: str,
        access_key_id: str,
        access_key_pwd: str,
        source_key: str=None,
        logger_fp: str=None
    ):
        super().__init__(
            source_endpoint=source_endpoint,
            source_key=source_key, 
            bucket_name=bucket_name,
            bucket_key=bucket_key,
            access_key_id=access_key_id,
            access_key_pwd=access_key_pwd,
            logger_fp=logger_fp
        )

    def request(self):
        self.logger.info('Requesting..')

        try:
            res = requests.get(self.source_endpoint)
        except Exception as e:
            print('GET request from OnThisDay API failed')
            print(f'Error msg: {str(e)}')

        if res.status_code != 200:
            print('Error; failed to GET data from the source')
            print(f'Error msg: {res.get('message', 'Unidentified error')}')
            sys.exit(1)

        soup = BeautifulSoup(res.text, 'html.parser')
        events = soup.find_all('li', class_='event')
        today = datetime.datetime.now()
        today_str = datetime.datetime.strftime(today, '%b%d')
        
        for event in events:
            if event.a:
                event_year = event.a.text
                try:
                    year = int(event_year)
                except ValueError:
                    year = 'Unknown'
                
                _ = event.a.decompose()

            desc = event.text.strip()
            if year == 'Unknown' and (substr:=desc.split(' ')[0]).isdigit():
                year = int(substr)
                desc = desc.replace(substr, '').strip()

            self.data.append({
                'year': year,
                'date': today_str,
                'event': desc
            })

    def stage(self):
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9010',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_pwd
        )

        try:
            client.head_bucket(Bucket=self.bucket_name)
        except botocore.exceptions.ClientError:
            print('Bucket does not exist; creating one')
            client.create_bucket(Bucket=self.bucket_name)

        date_suffix = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d %I%M%p')
        date,time = date_suffix.split()
        key=f'{self.bucket_key}/{date}'
        filename = f'stg_onthisday_{time}.json'

        client.put_object(
            Bucket=self.bucket_name,
            Key=f'{key}/{filename}',
            Body=bytes(json.dumps(self.data).encode('utf-8'))
        )
        print('Good!')