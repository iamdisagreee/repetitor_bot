from datetime import datetime, timedelta, date, time
from pprint import pprint
NUMBER_FINES = 3
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


########################################## СТУДЕНТ ###############################
# Создаем словарь словарей в котором хранятся все ячейки для выбора студентом дат
def create_choose_time_student(lessons_week, lessons_busy, week_date):
    list_busy = [[lesson.lesson_start, lesson.lesson_finished] for lesson in lessons_busy]
    slots = {day: [] for day in range(1, 9)}
    page_slots = 1
    record = 0
    now = datetime.now()
    for lesson_week in lessons_week:

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

            if [cur_dict['lesson_start'], cur_dict['lesson_end']] in list_busy: #
                    # or \
                    # now > datetime(year=week_date.year, month=week_date.month, day=week_date.day,
                    #                hour=cur_dict['lesson_start'].hour, minute=cur_dict['lesson_end'].minute)):
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


def show_all_lessons_for_day(all_lessons_for_day):
    result = []
    all_lessons_for_day = list(all_lessons_for_day)
    cur_list = {'start': all_lessons_for_day[0].lesson_start,
                'finished': all_lessons_for_day[0].lesson_finished}

    for lesson in all_lessons_for_day[1:]:
        cur_start = lesson.lesson_start
        cur_finished = lesson.lesson_finished

        if cur_list['finished'] == cur_start:
            cur_list['finished'] = cur_finished
        else:
            result.append(cur_list)
            cur_list = {'start': cur_start,
                        'finished': cur_finished}
    result.append(cur_list)
    return result


# Функция, которая проверяет, оплачены или нет занятия для выбранного промежутка!
def give_result_status_timeinterval(information_of_status_lesson):
    counter_status = 0
    counter_len = 0
    # print(information_of_status_lesson)
    for lesson in information_of_status_lesson:
        if lesson.status:
            counter_status += 1
        counter_len += 1

    return counter_status == counter_len, counter_len


def give_result_info(result_status):
    if result_status:
        return '✅ Оплата принята ✅'
    else:
        return '❌ Ожидается оплата ❌'


############################################## УЧИТЕЛЬ #########################################3
def show_intermediate_information_lesson_day_status(list_lessons_not_formatted):
    cur_buttons = []
    last_one = {'lesson_on': -1,
                'lesson_off': -1,
                'student_id': -1,
                'list_status': []}
    for interval in list_lessons_not_formatted:
        if interval.lessons:
            lessons_sort = sorted(interval.lessons, key=lambda gap: gap.lesson_start)
            if lessons_sort[0].lesson_start == last_one['lesson_off'] and \
                    lessons_sort[0].student_id == last_one['student_id']:
                cur_buttons.remove(last_one)
                interval_result = {
                    'lesson_on': last_one['lesson_on'],
                    'lesson_off': lessons_sort[0].lesson_finished,
                    'student_id': last_one['student_id'],
                    'list_status': last_one['list_status']
                }
            else:
                interval_result = {'lesson_on': lessons_sort[0].lesson_start,
                                   'lesson_off': lessons_sort[0].lesson_finished,
                                   'student_id': lessons_sort[0].student_id,
                                   'list_status': [lessons_sort[0].status]
                                   }

            index = 1
            while index < len(lessons_sort):
                gap = lessons_sort[index]
                if interval_result['lesson_off'] == gap.lesson_start:
                    interval_result['lesson_off'] = gap.lesson_finished
                    interval_result['list_status'].append(gap.status)
                else:
                    cur_buttons.append(interval_result)
                    interval_result = {'lesson_on': gap.lesson_start,
                                       'lesson_off': gap.lesson_finished,
                                       'student_id': gap.student_id,
                                       'list_status': [gap.status]}
                index += 1

            cur_buttons.append(interval_result)
            last_one = interval_result
    #print(cur_buttons)
    return cur_buttons

