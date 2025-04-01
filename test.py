@worker.task(task_name='student_mailing_lessons')
async def student_mailing_lessons(context: Context = TaskiqDepends(),
                                  bot: Bot = TaskiqDepends()):
    await scheduler_storage.startup()

    scheduled_tasks = await give_dictionary_tasks_student()

    print(await scheduler_storage.get_schedules())

    async with context.state.session_pool() as session:
        list_students_id = await give_lessons_for_day_students(session)
        # Смотрим расписание каждого студента по student_id
        # {student_id: {week_date: [12:30, 13:30, ...], week_date: [..],}, student_id2: ...}
        for student_id, dict_week_date in list_students_id.items():

            # {week_date: [12:30, 13:30, ...]}
            for week_date, lessons_day in dict_week_date.items():


                # Проверяем, что таска не удалена. Если удалена,
                # то меняем статус в обе стороны для всех занятий
                await  delete_unnecessary_tasks_student(student_id,
                                                        week_date,
                                                        lessons_day,
                                                        scheduled_tasks)

                print([x.student_mailing_status for x in lessons_day])

                flag_status = False
                scheduled_tasks = await give_dictionary_tasks_student()
                print(scheduled_tasks)
                for index, lesson_day in enumerate(lessons_day):
                    if len(lessons_day) == 1: break
                    if lesson_day.lesson_start in scheduled_tasks[student_id][week_date] or\
                            lesson_day.student_mailing_status == 2:
                        print(f'{lesson_day.lesson_start} уже зареган!')
                        continue
                    static_index = index
                    if  lesson_day.student_mailing_status == 0 and index + 1 < len(lessons_day):
                        for lesson_day_next in lessons_day[static_index + 1:]:
                            if check_is_30_minutes_between(lesson_day.lesson_start,
                                                           lesson_day_next.lesson_start):
                                if lesson_day_next.student_mailing_status == 1:
                                    # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
                                    await scheduler_storage.delete_schedule(
                                        f'b_l_s_{student_id}_{week_date}_{lesson_day_next.lesson_start}')
                                    break
                                else:
                                    break
                            else:
                                break

                    if lesson_day.student_mailing_status == 1:
                        # Если статус равен единице и слева нет соседей, то ставим уведомление
                        if index != 0 and not check_is_30_minutes_between(lessons_day[index-1].lesson_start,
                                                                          lesson_day.lesson_start):
                            flag_status = True

                    only_change = False
                    if not flag_status and index != 0 and \
                        lessons_day[index - 1].student_mailing_status == 1 and \
                            check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                        lessons_day[index].lesson_start):
                        only_change = True

                    if lesson_day.student_mailing_status == 0:
                        lesson_day.student_mailing_status = 1

                    if not only_change or flag_status:
                        # until_hour, until_minute = lesson_day.student.until_hour, lesson_day.until_minute
                        until_hour, until_minute = 0, 30
                        await create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                                    labels={str(student_id): [lesson_day.lesson_start,
                                                                              lesson_day.week_date]},
                                                    kwargs={'student_id': student_id,
                                                            'lesson_start': lesson_day.lesson_start,
                                                            'week_date': week_date,
                                                            },
                                                    schedule_id=f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}',
                                                    until_hour=until_hour,
                                                    until_minute=until_minute,
                                                    lesson_start=lesson_day.lesson_start,
                                                    week_date=week_date
                                                    )

        await session.commit()
    for x in await scheduler_storage.get_schedules():
        print(x.schedule_id)
    await scheduler_storage.shutdown()