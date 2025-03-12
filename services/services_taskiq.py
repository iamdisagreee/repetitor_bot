from sqlalchemy.ext.asyncio import AsyncSession


async def give_available_ids(scheduler_storage):
    return set(map(lambda x: x.schedule_id, await scheduler_storage.get_schedules()))

#Собираем информацию для учителя за день (заработок, еще выплатят, отработано)

def give_data_config_teacher(information_day):
    data_config_res = {}
    amount_money_yes, amount_money_no, amount_time = 0, 0, 0
    for teacher in information_day:
        for student in teacher.students:
            for lesson in student.lessons:
                # Если оплачено:
                if lesson.status:
                    amount_money_yes += student.price / 2
                # Если не оплачено
                else:
                    amount_money_no += student.price / 2
            # Считаем время работы
            amount_time = len(student.lessons) * 30

        data_config_res[teacher.teacher_id] = {
            'amount_money_yes': amount_money_yes,
            'amount_money_no': amount_money_no,
            'amount_time': amount_time
        }
        amount_money_yes, amount_money_no, amount_time = 0, 0, 0
    return data_config_res

