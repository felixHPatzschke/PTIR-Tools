
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

def timestamp_to_datetime(timestamp, tzname:str=None):
    dt_utc = datetime(1, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=timestamp / 10)
    tzinfo = datetime.now().astimezone().tzinfo if tzname is None else ZoneInfo(tzname)
    return dt_utc.astimezone(tzinfo)
