from pathlib import Path
from csv import DictWriter
from calcifer.utils.json_logger import logger


def write_to_file(file_name: Path, data: list):
    logger.info(f"Saving output to {file_name}")
    with open(file_name, "w") as csvfile:
        writer = DictWriter(csvfile, fieldnames=data[0].keys())

        writer.writeheader()
        for d in data:
            writer.writerow(d)