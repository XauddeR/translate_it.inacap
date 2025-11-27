from datetime import datetime, date

def format_date(value, fmt = '%d/%m/%Y'):
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    try:
        return datetime.fromisoformat(str(value)).strftime(fmt)
    except Exception:
        return str(value)
