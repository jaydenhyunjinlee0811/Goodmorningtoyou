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
        bucket_key: str
    ):
        super().__init__(
            source_endpoint=source_endpoint, 
            bucket_name=bucket_name,
            bucket_key=bucket_key
        )

    def get(self):
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
                'event': desc
            })

    def stage(self):
        ...