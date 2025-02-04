from abc import ABC, abstractmethod
from typing import List, Dict

from ..utils import get_logger

class GetterInterface(ABC):
    def __init__(
        self,
        source_endpoint: str,
        source_key: str,
        bucket_name: str,
        bucket_key: str,
        access_key_id: str,
        access_key_pwd: str,
        logger_fp: str = None
    ):
        self.source_endpoint = source_endpoint
        self.source_key = source_key
        self.bucket_name = bucket_name
        self.bucket_key = bucket_key
        self.access_key_id = access_key_id  
        self.access_key_pwd = access_key_pwd
        self.logger = get_logger(logger_fp)

        self.data: List[Dict[str, str]] = list()

    def get(self):
        self.request()
        self.stage()

    @abstractmethod
    def request(self):
        pass

    @abstractmethod
    def stage(self):
        pass