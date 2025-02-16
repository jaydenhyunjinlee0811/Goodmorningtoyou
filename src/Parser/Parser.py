import datetime
import re
import boto3
import json
import sys
import psycopg2 as pg
from typing import List, Dict

from ..utils import get_logger, create_pgclient

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

    def parse(self):
        self._extract()
        self._transform()
        self._ingest()

    def _extract(self):
        self.logger.info('Extracting staged data from Minio buckets..')
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9010',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_pwd
        )
        dt = datetime.datetime.now()
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

            elif len(contents) > 1:
                content = max(contents, key=lambda x:x['LastModified'])
            else:
                content = contents.pop(0)
            
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

    def _transform(self):
        url_patt = re.compile(r'https://www\.(\w+)\.com')
        for key in self.bucket_keys:
            contents = self.data[key]
            self.logger.info('Parsing [%s] staged data..', key)

            for content in contents:
                url = content.get('url')

                # Get rid of any leading/trailing whitespaces and single quotes
                for key,val in content.items():
                    content[key] = val.strip().replace('\'', '') if isinstance(val, str) else val
                
                ## News
                # `content` is a news content
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
                    shortened_description = description[:255].replace(description[-3:], '...')
                    content['description'] = shortened_description

                ## Onthisday
                if (event:=content.get('event', None)) and (len(event) > 255):
                    content['event'] = event[:255]
                
                if (year_str:=content.get('year', None)):
                    if isinstance(year_str, str):
                        content['year'] = None
                    else:
                        content['year'] = int(year_str)

            self.logger.info('Parsing [%s] complete!', key)

    def _ingest(self):
        conn = create_pgclient(
            host=self.db_host,
            port=self.db_port,
            db_name=self.db_name,
            user=self.db_user,
            pwd=self.db_pwd,
        )
        dt = str(datetime.date.today())

        with conn.cursor() as cursor:
            try:
                cursor.execute('BEGIN;')
                for key, lst in self.data.items():

                    if key == 'news':
                        select = f"SELECT COUNT(0) FROM {self.tbl_schema}.{key} WHERE publisheddate = '{dt}';"
                        insert = f"INSERT INTO {self.tbl_schema}.{key} (publisher, title, description, url, publisheddate) VALUES "
                        tmp_vals = [
                            (d['publisher'], d['title'], d['description'], d['url'], str(d['publishedDate'])) for d in lst
                        ]
                        vals = ', '.join(cursor.mogrify('(%s, %s, %s, %s, %s)', arg).decode('utf-8') for arg in tmp_vals)

                        # Overwrite existing records
                        _ = cursor.execute(select)
                        res = cursor.fetchall()
                        print(f'{res=}')
                        if res:
                            self.logger.info('Deleting stale news records..')
                            _ = cursor.execute(f"DELETE FROM {self.tbl_schema}.{key} WHERE publisheddate = '{dt}';")
                            self.logger.info('DELETION RESULT: [SUCCESS]')
                    else:
                        select = f"SELECT COUNT(0) FROM {self.tbl_schema}.{key} WHERE publisheddate = '{dt}';"
                        insert = f"INSERT INTO {self.tbl_schema}.{key} (year, event, publisheddate) VALUES "
                        tmp_vals = [
                            (d['year'], d['event'] ,d['publishedDate']) for d in lst
                        ]
                        vals = ', '.join(cursor.mogrify('(%s, %s, %s)', arg).decode('utf-8') for arg in tmp_vals)

                        # Overwrite existing records
                        _ = cursor.execute(select)
                        res = cursor.fetchall()
                        print(f'{res=}')
                        if res:
                            self.logger.info('Deleting stale onthisday records..')
                            _ = cursor.execute(f"DELETE FROM {self.tbl_schema}.{key} WHERE insertedAt::DATE = '{dt}';")
                            self.logger.info('DELETION RESULT: [SUCCESS]')

                    # print(json.dumps(vals, indent=4))
                    cursor.execute(insert+vals)
                    num_added = len(lst)

                    cursor.execute(f'SELECT COUNT(0) FROM {self.tbl_schema}.{key};')
                    num_total = cursor.fetchall().pop()[0]
                    self.logger.info('INGESTION RESULT: [SUCCESS]')
                    self.logger.info('Num. of [%s] Records Ingested: [%i]', key, num_added)
                    self.logger.info('Total Num. of [%s] Records Collected: [%i]', key, num_total)
                    self.logger.info('-'*60)

                cursor.execute('COMMIT;')
            except Exception as e:
                cursor.execute('ROLLBACK;')
                self.logger.error('[%s] INGESTION RESULT: [FAILED]', key.upper())
                self.logger.error('ERROR TYPE: [%s]', type(e))
                self.logger.error('ERROR MSG:')
                self.logger.error(e, exc_info=True)
            finally:
                conn.close()