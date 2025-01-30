import datetime
import re
import boto3
import os 
import json
import sys
import psycopg2 as pg
from typing import List, Dict, Union

from ..utils import get_logger 

class Parser(object):
    def __init__(
        self,
        access_key_id: str,
        access_key_pwd: str,
        bucket_name: str,
        bucket_keys: List[str],
        db_host: str,
        db_port: str,
        db_name: str,
        db_user: str,
        db_pwd: str,
        tbl_schema: str,
        logger_fp: str=None
    ):
        self.access_key_id = access_key_id
        self.access_key_pwd = access_key_pwd
        self.bucket_name = bucket_name
        self.bucket_keys = bucket_keys
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.tbl_schema = tbl_schema

        self.logger = get_logger(logger_fp)
        self.data: Dict[str, List[Dict[str, str]]] = {
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

        for prefix in self.bucket_keys:
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f'{prefix}/{dt_key}'
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
                self.data[prefix]+=parsed_data
        
        self.logger.info('Extraction result from Bucket(%s/%s): [%s] files', self.bucket_name, f'{prefix}/{dt_key}', len(self.data))

    def parse(self):
        url_patt = re.compile(r'https://www\.(\w+)\.com')
        for key in self.bucket_keys:
            contents = self.data[key]
            self.logger.info('Parsing [%s] staged data..', key)

            for content in contents:
                url = content.pop('url', None)

                # Get rid of any leading/trailing whitespaces and single quotes
                for key,val in content.items():
                    content[key] = val.strip().replace('\'', '') if isinstance(val, str) else val
                
                ## News
                # `content` is a news content
                # `publisher` was not found from the API response
                # `url` is not None
                if (
                    ((publisher:=content.get('publisher', None)) is None) and
                    (url is not None)
                ):
                    if (match:=url_patt.match(url)):
                        content['publisher'] = match.groups().pop().title()
                    else:
                        content['publisher'] = publisher

                if (publishedDt:=content.get('publishedDate', None)):
                    content['publishedDate'] = datetime.datetime.strptime(publishedDt, '%Y-%m-%d')

                if (description:=content.get('description', None)) and (len(description) > 255):
                    content['description'] = description[:255]
                
                ## Onthisday
                if (event:=content.get('event', None)) and (len(event) > 255):
                    content['event'] = event[:255]
                
                if (year_str:=content.get('year', None)):
                    content['year'] = int(year_str)

            self.logger.info('Parsing [%s] complete!', key)

    def ingest(self):
        conn = pg.connect(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_pwd
        )

        with conn.cursor() as cursor:
            try:
                cursor.execute('BEGIN;')
                for key, lst in self.data.items():
                    if key == 'news':
                        insert = f'INSERT INTO {self.tbl_schema}.{key} (publisher, title, description, publisheddate) VALUES '
                        # tmp_lst = list()
                        # for d in lst:
                        #     tmp_lst.append(str((d['publisher'], d['title'], d['description'], d['publishedDate'])))

                        vals = ', '.join([str((d['publisher'], d['title'], d['description'], str(d['publishedDate']))) for d in lst])
                        # vals = ', '.join(tmp_lst)
                        # vals = ', '.join(
                        #     cursor.mogrify(
                        #         '(%s, %s, %s, %s)', tuple([d['publisher'], d['title'], d['description'], d['publishedDate']])
                        #     ).decode('utf-8') for d in lst
                        # )
                    else:
                        sys.exit(0)
                        insert = ...

                    print(insert + vals)
                    cursor.execute(insert + vals)
                    self.logger.info('[%s] data successfully ingested!', key)
                
                cursor.execute('COMMIT;')
            except Exception as e:
                cursor.execute('ROLLBACK;')
                self.logger.error('Failed to database load')
                self.logger.error('Error msg: %s', str(e))
            finally:
                conn.close()