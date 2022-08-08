import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger


class DateTimeJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(DateTimeJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


logger = logging.getLogger()

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(
    DateTimeJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
