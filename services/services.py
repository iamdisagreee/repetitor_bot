from datetime import datetime, timedelta, date, time
from pprint import pprint

NUMERIC_DATE = {1: 'понедельник',
                2: 'вторник',
                3: 'среда',
                4: 'четверг',
                5: 'пятница',
                6: 'суббота',
                7: 'воскресенье'}

NUMBER_DAYS = 7
NUMBER_ENTRIES = 9


def give_list_with_days(get_date: datetime):
    result_date = []

    for days in range(NUMBER_DAYS + 1):
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


# Создаем словарь словарей в котором хранятся все ячейки для выбора студентом дат
def create_choose_time_student(lessons_week, lessons_busy):
    list_busy = [[lesson.lesson_start, lesson.lesson_finished] for lesson in lessons_busy]
    slots = {day: [] for day in range(1, 9)}
    page_slots = 1
    record = 0

    for lesson_week in lessons_week:

        now = datetime.now()

        start_time = datetime(year=now.year, month=now.month, day=now.day,
                              hour=lesson_week.work_start.hour, minute=lesson_week.work_start.minute)
        end_time = datetime(year=now.year, month=now.month, day=now.day,
                            hour=lesson_week.work_end.hour, minute=lesson_week.work_end.minute)
        delta_30 = timedelta(minutes=30)

        while start_time + delta_30 <= end_time:

            cur_dict = {}

            if record == 6:
                record = 0
                page_slots += 1

            cur_dict['lesson_start'] = time(hour=start_time.hour, minute=start_time.minute)
            start_time += delta_30
            cur_dict['lesson_end'] = time(hour=start_time.hour, minute=start_time.minute)

            if [cur_dict['lesson_start'], cur_dict['lesson_end']] in list_busy:
                continue

            slots[page_slots].append(cur_dict)
            record += 1

    return slots


# Создаем словарь словарей в котором хранятся удаляемое время
def create_delete_time_student(lessons_busy):
    slots = {day: [] for day in range(1, 9)}
    page_slots = 1
    record = 0

    for lesson in lessons_busy:
        if record == 6:
            record = 0
            page_slots += 1
        slots[page_slots].append(lesson)
        record += 1
    pprint(slots, indent=4)
    return slots
