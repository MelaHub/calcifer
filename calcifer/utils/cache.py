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
                    file_name = file
                    break

            if file_name:
                logger.info(f"Found cache, reading data from {tmp_folder}/{file_name}")
                with open(os.path.join(tmp_folder, file_name), 'r') as f:
                    data = json.load(f)
            else:
                logger.info(f"No cache found, creating new one")
                data = func(*args, **kwargs)
        
                with tempfile.NamedTemporaryFile(mode='w', prefix=file_prefix, delete=False) as f:
                    logger.info(f"Saving cache to {f.name}")
                    json.dump(data, f)
        
        return wrapper

    return inner
 