import uuid
from datetime import datetime, timedelta, date, time
from pprint import pprint
from typing import Dict, List, Any, Optional, Union

from pydantic import Field
from taskiq import ScheduledTask

from broker import scheduler_storage
from database import Student
from lexicon.lexicon_everyone import LEXICON_ALL
from lexicon.lexicon_student import LEXICON_STUDENT

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
COUNT_BAN = 3


def give_week_day_by_week_date(week_date: date):
    return NUMERIC_DATE[date(
        year=week_date.year,
        month=week_date.month,
        day=week_date.day
    ).isoweekday()
    ]


def give_list_with_days(get_date: datetime):
    result_date = []

    for days in range(NUMBER_DAYS + 1):
        next_date = get_date + timedelta(days=days)
        name_date = date(year=next_date.year, month=next_date.month, day=next_date.day)
        result_date.append(name_date)
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
def create_choose_time_student(lessons_week, lessons_busy, week_date,
                               penalty_time):
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
            # Случаи:
            #    1. Текущий слот уже занят
            #    2. Текущий слот уже наступил
            #    3. Время для пенальти уже наступило(если penalty=0, то второй случай
            # автоматически проверится)
            cur_datetime = datetime(year=week_date.year, month=week_date.month, day=week_date.day,
                                    hour=cur_dict['lesson_start'].hour,
                                    minute=cur_dict['lesson_start'].minute)
            if [cur_dict['lesson_start'], cur_dict['lesson_end']] in list_busy:  # or \
                # now >= cur_datetime - timedelta(hours=penalty_time):
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
    # pprint(slots, indent=4)
    return slots


def show_all_lessons_for_day(all_lessons_for_day):
    result = []
    all_lessons_for_day = list(all_lessons_for_day)
    cur_list = {'start': all_lessons_for_day[0].lesson_start,
                'finished': all_lessons_for_day[0].lesson_finished,
                'count_gaps': 1,
                'count_is_formed': all_lessons_for_day[0].is_formed}

    is_formed_last = all_lessons_for_day[0].is_formed

    for lesson in all_lessons_for_day[1:]:
        cur_start = lesson.lesson_start
        cur_finished = lesson.lesson_finished
        is_formed = lesson.is_formed

        # Условие, когда занятие не сформировано
        if cur_list['finished'] == cur_start and not is_formed and not is_formed_last:
            cur_list['finished'] = cur_finished
            cur_list['count_gaps'] += 1
        elif cur_list['finished'] == cur_start and is_formed and is_formed_last:
            cur_list['finished'] = cur_finished
            cur_list['count_gaps'] += 1
            cur_list['count_is_formed'] += is_formed
        else:
            result.append(cur_list)
            is_formed_last = is_formed
            cur_list = {'start': cur_start,
                        'finished': cur_finished,
                        'count_gaps': 1,
                        'count_is_formed': is_formed}
        # print(cur_list)
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
        return LEXICON_ALL['payed_right']
    else:
        return LEXICON_ALL['payed_not_right']


############################################## УЧИТЕЛЬ #########################################3
def show_intermediate_information_lesson_day_status(list_lessons_not_formatted):
    cur_buttons = []
    empty_lessons = []
    last_one = {'lesson_on': -1,
                'lesson_off': -1,
                'student_id': -1,
                'list_status': [],
                'price': -1,
                }

    for interval in list_lessons_not_formatted:
        # Случай, когда ученик не выбрал уроков вообще
        if not interval.lessons:
            cur_empty = {'lesson_on': interval.work_start,
                         'lesson_off': interval.work_end,
                         'student_id': None,
                         'list_status': [-1],
                         'price': -1,
                         }
            empty_lessons.append(cur_empty)
        if interval.lessons:
            lessons_sort = sorted(interval.lessons, key=lambda gap: gap.lesson_start)
            if lessons_sort[0].lesson_start == last_one['lesson_off'] and \
                    lessons_sort[0].student_id == last_one['student_id']:
                cur_buttons.remove(last_one)
                interval_result = {
                    'lesson_on': last_one['lesson_on'],
                    'lesson_off': lessons_sort[0].lesson_finished,
                    'student_id': last_one['student_id'],
                    'list_status': last_one['list_status'],
                    'price': lessons_sort[0].student.price,
                }
            else:
                interval_result = {'lesson_on': lessons_sort[0].lesson_start,
                                   'lesson_off': lessons_sort[0].lesson_finished,
                                   'student_id': lessons_sort[0].student_id,
                                   'list_status': [lessons_sort[0].status,],
                                   'price': lessons_sort[0].student.price,
                                   }

            # Проверка на то, что занятия начинаются не с начала промежутка
            if interval_result['lesson_on'] != interval.work_start:
                cur_buttons.append(
                    {'lesson_on': interval.work_start,
                     'lesson_off': interval_result['lesson_on'],
                     'student_id': None,
                     'list_status': [-1],
                     'price': interval_result['price']
                     }
                )

            is_formed_last = True if lessons_sort[0].is_formed else False

            index = 1
            while index < len(lessons_sort):
                gap = lessons_sort[index]
                if interval_result['lesson_off'] == gap.lesson_start and not gap.is_formed  \
                        and not is_formed_last:
                    interval_result['lesson_off'] = gap.lesson_finished
                    interval_result['list_status'] = [-1]
                if interval_result['lesson_off'] == gap.lesson_start and gap.is_formed\
                        and is_formed_last:
                    interval_result['lesson_off'] = gap.lesson_finished
                    interval_result['list_status'].append(gap.status)
                else:
                    cur_buttons.append(interval_result)
                    # Добавляем промежуток, который не выбран учениками
                    cur_buttons.append(
                        {
                            'lesson_on': cur_buttons[-1]['lesson_off'],
                            'lesson_off': gap.lesson_start,
                            'student_id': None,
                            'list_status': [-1],
                            'price': gap.student.price
                        }
                    )
                    interval_result = {'lesson_on': gap.lesson_start,
                                       'lesson_off': gap.lesson_finished,
                                       'student_id': gap.student_id,
                                       'list_status': [gap.status],
                                       'price': gap.student.price}
                index += 1

            cur_buttons.append(interval_result)
            # Проверка на остаток пустого промежутка
            if interval_result['lesson_off'] != interval.work_end:
                cur_buttons.append(
                    {
                        'lesson_on': interval_result['lesson_off'],
                        'lesson_off': interval.work_end,
                        'student_id': None,
                        'list_status': [-1],
                        'price': interval_result['price']
                    }
                )
            last_one = interval_result

    # Последний промежуток пустой, но уже есть занятия
    if cur_buttons and len(empty_lessons) == 1:
        cur_buttons.append(empty_lessons[-1])

    # Ни одного занятого места
    if not cur_buttons and empty_lessons:
        start = empty_lessons[0]['lesson_on']
        end = empty_lessons[0]['lesson_off']
        price = empty_lessons[0]['price']
        for lesson in empty_lessons[1:]:
            if lesson['lesson_on'] == end:
                end = lesson['lesson_off']
            else:
                cur_buttons.append(
                    {'lesson_on': start,
                     'lesson_off': end,
                     'student_id': None,
                     'list_status': [-1],
                     'price': price})
                start = lesson['lesson_on']
                end = lesson['lesson_off']
        cur_buttons.append(
            {'lesson_on': start,
             'lesson_off': end,
             'student_id': None,
             'list_status': [-1],
             'price': price})
    elif not cur_buttons and empty_lessons:
        # Добавляем в начало пустой промежуток:
        cur_buttons.insert(0, empty_lessons[0])
    return cur_buttons



# Время до пенальти
def count_time_to_penalty_not_format(week_date: date,
                                     lesson_on: time,
                                     penalty: int):
    cur_dt = datetime(year=week_date.year,
                      month=week_date.month,
                      day=week_date.day,
                      hour=lesson_on.hour,
                      minute=lesson_on.minute)

    time_difference = (cur_dt - datetime.now()
                       - timedelta(hours=penalty)).total_seconds()
    return time_difference


# Возвращаем время до пенальти в нужном для нас формате
def give_my_penalty_format(count_time_to_penalty):
    hour = int(count_time_to_penalty // 3600)
    minute = int(count_time_to_penalty // 60 % 60)
    if hour < 10:
        hour = '0' + str(hour)
    if minute < 10:
        minute = '0' + str(minute)
    return f'{hour}:{minute}'


# Получаем информацию об уроке в зависимости от системы пенальти
def give_text_information_lesson(student: Student,
                                 week_date: date,
                                 lesson_on: time,
                                 lesson_off: time,
                                 result_status,
                                 counter_lessons):
    # Смотрим, что со статусом
    status_info = give_result_info(result_status)

    # Проверяем, есть установлен ли режим пенальти
    if student.teacher.penalty:
        # Количество секунд до занятия
        count_time_to_penalty = count_time_to_penalty_not_format(week_date,
                                                                 lesson_on,
                                                                 student.teacher.penalty)
        # Если <= 0 -> уже наступило
        if count_time_to_penalty <= 0:
            text_penalty = LEXICON_STUDENT['text_penalty_expired']
        # Если > 0 -> выводим время до пенальти
        else:
            text_penalty = (LEXICON_STUDENT['text_penalty_not_expired']
                            .format(give_my_penalty_format(count_time_to_penalty))
                            )
        # Формирует текст об ученике
        text = LEXICON_STUDENT['information_about_lesson_penalty'].format(
            student.teacher.surname, student.teacher.name, lesson_on.strftime("%H:%M"),
            lesson_off.strftime("%H:%M"),
            student.teacher.phone, student.teacher.bank, student.price * counter_lessons / 2,
            text_penalty, status_info
        )
    else:
        # Случай, когда система пенальти не установлена
        text = LEXICON_STUDENT['information_about_lesson'].format(
            student.teacher.surname, student.teacher.name, lesson_on.strftime("%H:%M"),
            lesson_off.strftime("%H:%M"),
            student.teacher.phone, student.teacher.bank, student.price * counter_lessons / 2,
            status_info)

    return text


def course_class_choose(class_learning,
                        course_learning):
    return f'{class_learning} класс' if class_learning \
        else f'{course_learning} класс'


# Получаем список всех интервалов из заданного интервала: [lesson_on; lesson_off]
def create_list_gaps_by_time_on_and_off(week_date: date,
                                        lesson_on: time,
                                        lesson_off: time):
    lesson_on_dt = datetime(year=week_date.year, month=week_date.month,
                            day=week_date.day, hour=lesson_on.hour,
                            minute=lesson_on.minute)
    lesson_off_dt = datetime(year=week_date.year, month=week_date.month,
                             day=week_date.day, hour=lesson_off.hour,
                             minute=lesson_off.minute)
    list_gaps_time = []
    while lesson_on_dt != lesson_off_dt:
        list_gaps_time.append(time(hour=lesson_on_dt.hour,
                                   minute=lesson_on_dt.minute))
        lesson_on_dt += timedelta(minutes=30)

    return list_gaps_time

# Добавилось / удалилось занятие
def is_correct_sent_notification_lesson_for_teacher(days: int,
                                                    week_date):
    return days and datetime.now() \
        + timedelta(days=days - 1) >= \
        datetime(year=week_date.year, month=week_date.month, day=week_date.day)


# Создаем таску с предварительной проверкой, что она не создана
async def create_scheduled_task_handler(task_name: str,
                                        labels: Dict[str, Any] = None,
                                        args: List[Any] = None,
                                        kwargs: Dict[str, Any] = None,
                                        schedule_id: str = Field(default_factory=lambda: uuid.uuid4().hex),
                                        cron: Optional[str] = None,
                                        cron_offset: Optional[Union[str, timedelta]] = 'Europe/Moscow',
                                        time: Optional[datetime] = None,
                                        ):
    if labels is None:
        labels = dict()
    if args is None:
        args = []
    if kwargs is None:
        kwargs = dict()

    task = ScheduledTask(task_name=task_name,
                         labels=labels,
                         args=args,
                         kwargs=kwargs,
                         schedule_id=schedule_id,
                         cron=cron,
                         cron_offset=cron_offset,
                         time=time,
                         )

    await scheduler_storage.add_schedule(task)
