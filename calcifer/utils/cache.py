import tempfile
from datetime import date
from calcifer.utils.json_logger import logger
from os.path import exists
import os
import json


def cache_to_file(file_prefix: str):

    def inner(func):
     
        def wrapper(*args, **kwargs):
            tmp_folder = tempfile.gettempdir()
            file_name = None
            for file in os.listdir(tmp_folder):
                if file.startswith(file_prefix):
                    file_name = None
                    break

            if file_name:
                logger.info(f"Found cache, reading data from {file_name}")
                with open(file_name, 'r') as f:
                    data = json.load(f)
            else:
                logger.info(f"No cache found, creating new one")
                data = func(*args, **kwargs)
                with tempfile.NamedTemporaryFile(prefix=file_prefix, delete=False) as f:
                    json.dump(data, f)
        
        return wrapper

    return inner
 