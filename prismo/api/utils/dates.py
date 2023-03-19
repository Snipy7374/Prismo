from typing import Optional

from datetime import datetime

def convert_to_date(date: Optional[str]) -> Optional[datetime]:
    if not date:
        return None
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")

