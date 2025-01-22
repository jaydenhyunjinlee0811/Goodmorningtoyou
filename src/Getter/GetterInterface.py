from abc import ABC, abstractmethod
from typing import List, Dict

from ..utils import get_logger

class GetterInterface(ABC):
    def __init__(
        self,
        source_endpoint: str,
        bucket_name: str,
        bucket_key: str,
        source_key: str = None,
        logger_fp: str = None
    ):
        self.source_endpoint = source_endpoint
        self.source_key = source_key
        self.bucket_name = bucket_name
        self.bucket_key = bucket_key
        self.logger = get_logger(logger_fp)

        self.data: List[Dict[str, str]] = list()

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def stage(self):
        pass