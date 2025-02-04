import boto3
import logging 
import sys

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