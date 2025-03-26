import uuid
from datetime import timedelta, datetime, date, time
from typing import Dict, Any, List, Optional, Union

from numpy.version import full_version
from pydantic import Field
from sqlalchemy import result_tuple
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import ScheduledTask

from database import Teacher


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
    #time_one < time_two
    return (
            timedelta(hours=time_two.hour, minutes=time_two.minute) -
            timedelta(hours=time_one.hour, minutes=time_one.minute)
           ).total_seconds() ==  1800 #30 минут

def change_to_specified_time(cur_time: time, change_td: timedelta):
    now = date.today()
    dt_result = datetime(now.year, now.month, now.day, cur_time.hour, cur_time.minute) + change_td
    return dt_result.hour, dt_result.minute#time(hour=dt_result.hour, minute=dt_result.minute)

def give_correct_time_schedule_before_lesson(lesson_start: time, until_hour: int, until_minute: int):
    now = datetime.now()
    until_time = timedelta(hours=until_hour, minutes=until_minute)
    sum_now_until = now + until_time

    #Случай, когда время уведомления уже наступило. Тогда отправляем текущее кол-во минут до занятия
    if time(hour=sum_now_until.hour, minute=sum_now_until.minute) >= lesson_start:

        result_sent_time = datetime(year=now.year, month=now.month, day=now.day,
                                    hour=lesson_start.hour, minute=lesson_start.minute) - \
                            timedelta(hours=now.hour, minutes=now.minute)
        until_hour, until_minute = result_sent_time.hour, result_sent_time.minute
    #Если все же заданное ограничение по времени сохраняется
    else:
        result_sent_time = datetime(year=now.year, month=now.month, day=now.day,
                                    hour=lesson_start.hour, minute=lesson_start.minute) - until_time

    return result_sent_time, until_hour, until_minute

def create_scheduled_task(task_name: str,
                        labels: Dict[str, Any] = None,
                        args: List[Any] = None,
                        kwargs: Dict[str, Any] = None,
                        schedule_id: str = Field(default_factory=lambda: uuid.uuid4().hex),
                        cron: Optional[str] = None,
                        cron_offset: Optional[Union[str, timedelta]] = None,
                        time: Optional[datetime] = None
                        ):
    if labels is None:
        labels = dict()
    if args is None:
        args = []
    if kwargs is None:
        kwargs = dict()
    return ScheduledTask(task_name = task_name,
                        labels = labels,
                        args = args,
                        kwargs = kwargs,
                        schedule_id = schedule_id,
                        cron = cron,
                        cron_offset = cron_offset,
                        time = time,
    )
