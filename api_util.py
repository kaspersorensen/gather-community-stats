from datetime import datetime

def included_in_date_range(datestr, filter_from: str = None, filter_to: str = None):
    if not filter_from and not filter_to:
        return True
    dt = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S%z")
    if filter_from and filter_from > dt:
        return False
    if filter_to and filter_to < dt:
        return False
    return True
def older_than_date_range(datestr, filter_from: str = None):
    if not filter_from:
        return False
    dt = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S%z")
    if filter_from and filter_from > dt:
        return True
    return False