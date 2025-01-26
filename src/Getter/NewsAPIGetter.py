import sys
import requests
import json
import boto3
import botocore
import datetime

from .GetterInterface import GetterInterface

class NewsAPIGetter(GetterInterface):
    def __init__(
        self, 
        source_endpoint: str, 
        bucket_name: str,
        bucket_key: str,
        source_key: str,
        access_key_id: str,
        access_key_pwd: str,
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

    def get(self):
        self.logger.info('Requesting..')

        try:
            res = requests.get(f'{self.source_endpoint}&apiKey={self.source_key}').json()
        except Exception as e:
            print('GET request from News API failed')
            print(f'Error msg: {str(e)}')

        if res['status'] != 'ok':
            print('Error; failed to GET data from the source')
            print(f'Error msg: {res.get('message', 'Unidentified error')}')
            sys.exit(1)

        for article in res['articles']:
            dt = article['publishedAt'].split('T')[0]
            tmp = {
                'publisher': article['source']['name'],
                'title': article['title'],
                'description': article['description'],
                'publishedDate': dt,
                'url': article['url']
            }
            self.data.append(tmp)

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
        filename = f'stg_news_{time}.json'

        client.put_object(
            Bucket=self.bucket_name,
            Key=f'{key}/{filename}',
            Body=bytes(json.dumps(self.data).encode('utf-8'))
        )
        print('Good!')