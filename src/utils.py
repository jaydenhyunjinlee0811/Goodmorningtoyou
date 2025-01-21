import boto3
import logging 
import sys

def get_logger(logger_fp: str):
    logger = logging.get_logger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s|%(name)s|%(levelname)s| >> %(message)s'
    )
    stream_handler = logging.StreamHandler(sys.stdout)

    if logger_fp:
        ...

    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger