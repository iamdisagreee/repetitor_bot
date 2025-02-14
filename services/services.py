from datetime import datetime, timedelta, date, time

NUMERIC_DATE = {1: 'понедельник',
                2: 'вторник',
                3: 'среда',
                4: 'четверг',
                5: 'пятница',
                6: 'суббота',
                7: 'воскресенье'}

NUMBER_DAYS = 7


def give_list_with_days(get_date: datetime):
    result_date = []

    for days in range(NUMBER_DAYS):
        next_date = get_date + timedelta(days=days)
        # format_date = next_date.strftime('%d.%m')
        name_date = date(year=next_date.year, month=next_date.month, day=next_date.day)
        result_date.append(name_date)
    # day, month = list(map(int, '28.01 - пятница'[:5].split('.')))
    # print(day, month)
    return result_date


def give_date_format_callback(get_date: str):
    year, month, day = list(map(int, get_date.split('-')))
    return date(year=year, month=month, day=day)


def give_date_format_fsm(get_date: str):
    year, month, day = list(map(int, get_date.split('-')))
    return date(year=year, month=month, day=day)


def give_time_format_fsm(get_time: str):
    hour, minute = list(map(int, get_time.split(':')))
    return time(hour=hour, minute=minute)


def give_list_registrations_str(res_time):
    result_line = []
    for one_date in res_time:
        work_start_str = one_date.work_start.strftime("%H:%M")
        work_end_str = one_date.work_end.strftime("%H:%M")
        result_line.append(f'{work_start_str} - {work_end_str}')

    return '\n'.join(result_line)
