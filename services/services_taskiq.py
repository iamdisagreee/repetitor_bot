from numpy.version import full_version
from sqlalchemy.ext.asyncio import AsyncSession

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