import logging 
import sys
import psycopg2 as pg
from typing import List, Dict

def get_logger(logger_fp: str=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s|%(levelname)s| >> %(message)s',
        datefmt='%Y/%m/%d %I:%M%p'
    )
    stream_handler = logging.StreamHandler(sys.stdout)

    if logger_fp:
        fileHandler = logging.FileHandler(
            filename=logger_fp
        )
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger

def create_pgclient(
        host: str,
        port: str,
        db_name: str,
        user: str,
        pwd: str
    ):
    return pg.connect(
        host=host,
        port=port,
        dbname=db_name,
        user=user,
        password=pwd
    )

def sort_by_year(lst: List[Dict]):
    valid_yrs = sorted(
        [item for item in lst if isinstance(item.get('year', None), int)],
        key=lambda x: x['year']
    )
    invalid_yrs = [item for item in lst if not isinstance(item.get('year', None), int)]
    return valid_yrs + invalid_yrs