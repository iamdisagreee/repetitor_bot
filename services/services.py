from datetime import datetime, timedelta, date, time

NUMERIC_DATE = {1: 'понедельник',
                2: 'вторник',
                3: 'среда',
                4: 'четверг',
                5: 'пятница',
                6: 'суббота',
                7: 'воскресенье'}

NUMBER_DAYS = 7


def give_dict_with_days(get_date: datetime):
    result_date = {}

    for days in range(NUMBER_DAYS):
        next_date = get_date + timedelta(days=days)
        format_date = next_date.strftime('%d.%m')
        name_date = NUMERIC_DATE[
            date(year=next_date.year, month=next_date.month, day=next_date.day).isoweekday()
        ]
        result_date[format_date] = name_date
    # day, month = list(map(int, '28.01 - пятница'[:5].split('.')))
    # print(day, month)
    return result_date


# Из "12.01 - пятница" в 2024/12/01 (date)
def create_date_record(date_now: str):
    day, month = list(map(int, date_now[:5].split('.')))
    return date(year=date.today().year, month=month, day=day)


# Из "14:44" в 14:44:00 (time)
def create_time_record(time_now: str):
    hour, minute = list(map(int, time_now.split(':')))
    return time(hour=hour, minute=minute)
