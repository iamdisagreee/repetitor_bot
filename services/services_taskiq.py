import uuid
from collections import defaultdict
from datetime import timedelta, datetime, date, time, timezone
from typing import Dict, Any, List, Optional, Union
from zoneinfo import ZoneInfo

from numpy.version import full_version
from pydantic import Field
from sqlalchemy import result_tuple
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import ScheduledTask

from broker import scheduler_storage
from database import Teacher
from services.services import give_date_format_fsm, give_time_format_fsm


async def give_available_ids(scheduler_storage):
    return set(map(lambda x: x.schedule_id, await scheduler_storage.get_schedules()))


# Собираем информацию для учителя за день (заработок, еще выплатят, отработано)

def give_data_config_teacher(teacher: Teacher):
    result_debtors = []
    dict_debtors = {}
    general_information = {
        'amount_money_yes': 0,
        'amount_money_no': 0,
        'amount_time': 0,
    }
    for student in teacher.students:
        for lesson in sorted(student.lessons, key=lambda x: x.lesson_start):
            if lesson.status:
                general_information['amount_money_yes'] += student.price / 2
            else:
                if not dict_debtors:
                    dict_debtors = {'student_id': student.student_id,
                                    'student_name': student.name,
                                    'student_surname': student.surname,
                                    'lesson_on': lesson.lesson_start,
                                    'lesson_off': lesson.lesson_finished,
                                    'amount_money': student.price / 2}
                else:
                    if dict_debtors['lesson_off'] == lesson.lesson_start and \
                            dict_debtors['student_id'] == lesson.student_id:
                        dict_debtors['lesson_off'] = lesson.lesson_finished
                        dict_debtors['amount_money'] += student.price / 2
                    else:
                        result_debtors.append(dict_debtors)
                        dict_debtors = {'student_id': student.student_id,
                                        'student_name': student.name,
                                        'student_surname': student.surname,
                                        'lesson_on': lesson.lesson_start,
                                        'lesson_off': lesson.lesson_finished,
                                        'amount_money': student.price / 2}
                    general_information['amount_money_no'] += student.price / 2

            general_information['amount_time'] += 30
        if dict_debtors:
            result_debtors.append(dict_debtors)

    return result_debtors, general_information


def give_everyday_schedule(teacher: Teacher):
    result_schedule = []
    cur_lesson = {}
    for student in teacher.students:
        for lesson in sorted(student.lessons, key=lambda x: x.lesson_start):
            if not cur_lesson:
                cur_lesson = {
                    'student_id': student.student_id,
                    'student_name': student.name,
                    'student_surname': student.surname,
                    'lesson_on': lesson.lesson_start,
                    'lesson_off': lesson.lesson_finished,
                    'amount_money': student.price / 2,
                    'status_pay': lesson.status
                }
            else:
                if cur_lesson['lesson_off'] == lesson.lesson_start and \
                        cur_lesson['student_id'] == lesson.student_id:
                    cur_lesson['lesson_off'] = lesson.lesson_finished
                    cur_lesson['amount_money'] += student.price / 2
                else:
                    result_schedule.append(cur_lesson)
                    cur_lesson = {
                        'student_id': student.student_id,
                        'student_name': student.name,
                        'student_surname': student.surname,
                        'lesson_on': lesson.lesson_start,
                        'lesson_off': lesson.lesson_finished,
                        'amount_money': student.price / 2,
                        'status_pay': lesson.status
                    }
        if cur_lesson:
            result_schedule.append(cur_lesson)

    return result_schedule


def create_schedule_like_text(result_schedule):
    text = ''
    for lesson in result_schedule:
        status = '✅' if lesson['status_pay'] else '❌'
        text += f" - {status} {lesson['student_name']} {lesson['lesson_on'].strftime('%H:%M')}-" \
                f"{lesson['lesson_off'].strftime('%H:%M')} {lesson['amount_money']} р. " \
                f"\n"

    return text


def check_is_30_minutes_between(time_one, time_two):
    # time_one < time_two
    return (
            timedelta(hours=time_two.hour, minutes=time_two.minute) -
            timedelta(hours=time_one.hour, minutes=time_one.minute)
    ).total_seconds() == 1800  # 30 минут


def change_to_specified_time(cur_time: time, change_td: timedelta):
    now = date.today()
    dt_result = datetime(now.year, now.month, now.day, cur_time.hour, cur_time.minute) + change_td
    return dt_result.hour, dt_result.minute  # time(hour=dt_result.hour, minute=dt_result.minute)


def give_correct_time_schedule_before_lesson(lesson_start: time, week_date: date, until_hour: int, until_minute: int):
    now = datetime.now()
    until_time = timedelta(hours=until_hour, minutes=until_minute)
    sum_now_until = now + until_time
    dt_lesson = datetime(year=week_date.year, month=week_date.month, day=week_date.day,
                         hour=lesson_start.hour, minute=lesson_start.minute)
    # Случай, когда время уведомления уже наступило. Тогда отправляем текущее кол-во минут/часов до занятия
    if sum_now_until >= dt_lesson:
        result_sent_time_td = dt_lesson - now
        result_sent_time = dt_lesson - result_sent_time_td
        result_sent_time_interval = datetime.min + result_sent_time_td
        until_hour, until_minute = result_sent_time_interval.hour, result_sent_time_interval.minute
    # Если все же заданное ограничение по времени сохраняется
    else:
        result_sent_time = dt_lesson - until_time
    print('!', now, until_time, sum_now_until, dt_lesson, until_hour, until_minute, sep=' | ')
    timezone_set = ZoneInfo('Europe/Moscow')
    return result_sent_time.replace(tzinfo=timezone_set), until_hour, until_minute



# Добавляем таску в хранилище задач
async def create_scheduled_task(task_name: str,
                              labels: Dict[str, Any] = None,
                              args: List[Any] = None,
                              kwargs: Dict[str, Any] = None,
                              schedule_id: str = Field(default_factory=lambda: uuid.uuid4().hex),
                              cron: Optional[str] = None,
                              cron_offset: Optional[Union[str, timedelta]] = None,
                              time: Optional[datetime] = None,
                              until_hour: int = None,
                              until_minute: int = None,
                              lesson_start: time = None,
                              week_date: date = None,

                          ):

    result_sent_time, until_hour, until_minute = \
        give_correct_time_schedule_before_lesson(lesson_start,
                                                 week_date,
                                                 until_hour,
                                                 until_minute)
    if labels is None:
        labels = dict()
    if args is None:
        args = []
    if kwargs is None:
        kwargs = dict()

    kwargs['time_before_lesson'] = [until_hour, until_minute]

    task = ScheduledTask(task_name=task_name,
                         labels=labels,
                         args=args,
                         kwargs=kwargs,
                         schedule_id=schedule_id,
                         cron=cron,
                         cron_offset=cron_offset,
                         time=result_sent_time + timedelta(seconds=5),
                         )
    print(f'Будет отправлено в {result_sent_time}')
    await scheduler_storage.add_schedule(task)

# Возвращаем словарь тасок для студента
async def give_dictionary_tasks_student():
    scheduled_tasks = defaultdict(lambda: defaultdict(list))
    for task in await scheduler_storage.get_schedules():
        if task.schedule_id[0:5] == 'b_l_s':
            student_id, values = list(task.labels.items())[0]
            lesson_start, week_date = values
            scheduled_tasks[int(student_id)][give_date_format_fsm(week_date)] \
                            .append(give_time_format_fsm(lesson_start[:-3]))
    return scheduled_tasks

# Возвращаем словарь тасок для учителя
async def give_dictionary_tasks_teacher():
    scheduled_tasks = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for task in await scheduler_storage.get_schedules():
        if task.schedule_id[0:5] == 'b_l_t':
            teacher_id, values = list(task.labels.items())[0]
            student_id, lesson_start, week_date = values
            scheduled_tasks[int(teacher_id)][student_id][give_date_format_fsm(week_date)] \
                .append(give_time_format_fsm(lesson_start[:-3]))
    return scheduled_tasks

# Удаляем отменившиеся задачи для студента
async def delete_unnecessary_tasks_student(student_id,
                                           week_date,
                                           lessons_day,
                                           scheduled_tasks):
    # Проверяем, что таска не удалена. Если удалена,
    # то меняем статус в обе стороны для всех занятий
    dict_lessons_day = dict((lesson_day.lesson_start, lesson_day)
                            for lesson_day in lessons_day)

    for task_lesson_start in scheduled_tasks[student_id][week_date]:
        # Если такого времени нет, то удаляем задачу и меняем статуса в левую и правую сторону
        if task_lesson_start not in dict_lessons_day.keys():
            await scheduler_storage.delete_schedule(f'b_l_s_{student_id}_{week_date}_{task_lesson_start}')
            left_time_lesson = task_lesson_start
            right_time_lesson = task_lesson_start
            while True:
                hour, minute = change_to_specified_time(left_time_lesson, timedelta(minutes=-30))
                left_time_lesson = time(hour=hour, minute=minute)
                give_result_time = dict_lessons_day.get(left_time_lesson)
                if give_result_time is not None and give_result_time.student_mailing_status == 1:
                    give_result_time.student_mailing_status = 0
                else:
                    break
            while True:
                hour, minute = change_to_specified_time(right_time_lesson, timedelta(minutes=30))
                right_time_lesson = time(hour=hour, minute=minute)
                give_result_time = dict_lessons_day.get(right_time_lesson)
                if give_result_time is not None and give_result_time.student_mailing_status == 1:
                    give_result_time.student_mailing_status = 0
                else:
                    break

# Удаляем отменившиеся задачи для учителя
async def delete_unnecessary_tasks_teacher(teacher_id,
                                           student_id,
                                           week_date,
                                           lessons_day,
                                           scheduled_tasks):

    dict_lessons_day = dict((lesson_day.lesson_start, lesson_day)
                            for lesson_day in lessons_day)

    for task_lesson_start in scheduled_tasks[teacher_id][student_id][week_date]:
        if task_lesson_start not in dict_lessons_day.keys():
            await scheduler_storage.delete_schedule(f'b_l_t_{teacher_id}_{week_date}'
                                                    f'_{task_lesson_start}')
            left_time_lesson = task_lesson_start
            right_time_lesson = task_lesson_start

            while True:
                hour, minute = change_to_specified_time(left_time_lesson, timedelta(minutes=-30))
                left_time_lesson = time(hour=hour, minute=minute)
                give_result_time = dict_lessons_day.get(left_time_lesson)
                if give_result_time is not None and give_result_time.student_mailing_status == 1:
                    give_result_time.student_mailing_status = 0
                else:
                    break

            while True:
                hour, minute = change_to_specified_time(right_time_lesson, timedelta(minutes=30))
                right_time_lesson = time(hour=hour, minute=minute)
                give_result_time = dict_lessons_day.get(right_time_lesson)
                if give_result_time is not None and give_result_time.student_mailing_status == 1:
                    give_result_time.student_mailing_status = 0
                else:
                    break