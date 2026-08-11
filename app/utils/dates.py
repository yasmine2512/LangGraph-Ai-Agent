from datetime import datetime, timedelta


def parse_date(date_string):
    if not date_string:
        return None

    return datetime.fromisoformat(
        date_string.replace("Z", "+00:00")
    )

def get_period_dates(period):
    now = datetime.now()

    if period == "today":
        start = datetime(now.year, now.month, now.day)
        return start, now

    if period == "this_week":
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day)
        return start, now

    if period == "this_month":
        return datetime(now.year, now.month, 1), now

    if period == "last_month":
        if now.month == 1:
            start = datetime(now.year - 1, 12, 1)
            end = datetime(now.year, 1, 1)
        else:
            start = datetime(now.year, now.month - 1, 1)
            end = datetime(now.year, now.month, 1)

        return start, end

    if period == "this_year":
        return datetime(now.year, 1, 1), now

    if period == "last_year":
        return (
            datetime(now.year - 1, 1, 1),
            datetime(now.year, 1, 1)
        )

    if period == "last_7_days":
        return now - timedelta(days=7), now

    if period == "last_30_days":
        return now - timedelta(days=30), now

    if period == "last_7_months":
        start = datetime(now.year, now.month, 1)

        for _ in range(6):
            if start.month == 1:
                start = datetime(start.year - 1, 12, 1)
            else:
                start = datetime(start.year, start.month - 1, 1)

        return start, now

    return None, None