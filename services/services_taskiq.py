from numpy.version import full_version
from sqlalchemy.ext.asyncio import AsyncSession

from database import Teacher


async def give_available_ids(scheduler_storage):
    return set(map(lambda x: x.schedule_id, await scheduler_storage.get_schedules()))


# Собираем информацию для учителя за день (заработок, еще выплатят, отработано)

# def give_data_config_teacher(information_day):
#     data_config_res = {}
#     amount_money_yes, amount_money_no, amount_time = 0, 0, 0
#     for teacher in information_day:
#         for student in teacher.students:
#             for lesson in student.lessons:
#                 # Если оплачено:
#                 if lesson.status:
#                     amount_money_yes += student.price / 2
#                 # Если не оплачено
#                 else:
#                     amount_money_no += student.price / 2
#             # Считаем время работы
#             amount_time = len(student.lessons) * 30
#
#         data_config_res[teacher.teacher_id] = {
#             'amount_money_yes': amount_money_yes,
#             'amount_money_no': amount_money_no,
#             'amount_time': amount_time
#         }
#         amount_money_yes, amount_money_no, amount_time = 0, 0, 0
#     return data_config_res

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
        result_debtors.append(dict_debtors)

    return result_debtors, general_information
