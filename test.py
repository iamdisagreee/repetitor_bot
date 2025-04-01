# @worker.task(task_name='student_mailing_lessons')
# async def student_mailing_lessons(context: Context = TaskiqDepends(),
#                                   bot: Bot = TaskiqDepends()):
#     await scheduler_storage.startup()
#
#     scheduled_tasks = defaultdict(lambda: defaultdict(list))
#     for task in await scheduler_storage.get_schedules():
#         if task.schedule_id[0:5] == 'b_l_s':
#             student_id, values = list(task.labels.items())[0]
#             lesson_start, week_date = values
#             scheduled_tasks[int(student_id)][give_date_format_fsm(week_date)] \
#                             .append(give_time_format_fsm(lesson_start[:-3]))
#     # print()
#     # print(scheduled_tasks)
#     print(await scheduler_storage.get_schedules())
#
#     async with (context.state.session_pool() as session):
#         list_students_id = await give_lessons_for_day_students(session)
#         # Смотрим расписание каждого студента по student_id
#         # {student_id: {week_date: [12:30, 13:30, ...], week_date: [..],}, student_id2: ...}
#         for student_id, dict_week_date in list_students_id.items():
#
#             # {week_date: [12:30, 13:30, ...]}
#             for week_date, lessons_day in dict_week_date.items():
#
#                 # Проверяем, что таска не удалена. Если удалена,
#                 # то меняем статус в обе стороны для всех занятий
#                 dict_lessons_day = dict((lesson_day.lesson_start, lesson_day)
#                                        for lesson_day in lessons_day)
#
#                 # print('Словарь существующих уроков', dict_lessons_day)
#                 # pri`nt('Список запланированных задач', scheduled_tasks[student_id])
#
#                 for task_lesson_start in scheduled_tasks[student_id][week_date]:
#                     # Если такого времени нет, то удаляем задачу и меняем статуса в левую и правую сторону
#                     if task_lesson_start not in dict_lessons_day.keys():
#                         await scheduler_storage.delete_schedule(f'b_l_s_{student_id}_{week_date}_{task_lesson_start}')
#                         # print('Я УДАЛиЛИЛИЛИЛИЛИ')
#                         left_time_lesson = task_lesson_start
#                         right_time_lesson = task_lesson_start
#                         while True:
#                             hour, minute = change_to_specified_time(left_time_lesson, timedelta(minutes=-30))
#                             left_time_lesson = time(hour=hour, minute=minute)
#                             give_result_time = dict_lessons_day.get(left_time_lesson)
#                             # print('GET_L', right_time_lesson, give_result_time)
#                             if give_result_time is not None and give_result_time.student_mailing_status == 1:
#                                 give_result_time.student_mailing_status = 0
#                             else:
#                                 break
#                         while True:
#                             # print('right_time_lesson', right_time_lesson)
#                             hour, minute = change_to_specified_time(right_time_lesson, timedelta(minutes=30))
#                             right_time_lesson = time(hour=hour, minute=minute)
#                             give_result_time = dict_lessons_day.get(right_time_lesson)
#                             # print('GET_R', right_time_lesson, give_result_time)
#                             if give_result_time is not None and give_result_time.student_mailing_status == 1:
#                                 # print("AAA")
#                                 give_result_time.student_mailing_status = 0
#                             else:
#                                 break
#
#                 print([x.student_mailing_status for x in lessons_day])
#                 if len(lessons_day) == 1:
#                     if lessons_day[0].student_mailing_status == 0:
#                         until_hour, until_minute = 0, 5
#                         #Устанавливаем для отправления уведомлений
#                         result_sent_time, until_hour, until_minute = \
#                                             give_correct_time_schedule_before_lesson(lessons_day[0].lesson_start,
#                                                                                      week_date,
#                                                                                      until_hour,
#                                                                                      until_minute)
#
#                         # меняем статус и устанавливаем уведомление + добавляем в текущее хранилище
#                         lessons_day[0].student_mailing_status = 1
#                         await scheduler_storage.add_schedule(
#                             create_scheduled_task(task_name='notice_lesson_certain_time_student',
#                                                   labels={str(student_id): [str(lessons_day[0].lesson_start),
#                                                           str(lessons_day[0].week_date)]},
#                                                   kwargs={'student_id': student_id,
#                                                           'lesson_start': str(lessons_day[0].lesson_start),
#                                                           'time_before_lesson': [until_hour, until_minute]
#                                                           },
#                                                   schedule_id=f'b_l_s_{student_id}_{week_date}_{lessons_day[0].lesson_start}',
#                                                   time=result_sent_time + timedelta(seconds=5))
#                                                   # cron='* * * * *',
#                                                   # cron_offset='Europe/Moscow')
#                         )
#                         # scheduled_tasks[student_id].append(lessons_day[0].lesson_start)
#                         print(f'Будет отправлено в {result_sent_time}')
#                         continue
#
#                 for index, lesson_day in enumerate(lessons_day):
#                     until_hour, until_minute = 0, 5
#                     # print("INFO", lesson_day.student_mailing_status, index, lesson_day.lesson_start)
#                     count_lessons = 0
#                     static_index = index
#                     if lesson_day.student_mailing_status == 0 and index + 1 < len(lessons_day):
#                         for lesson_day_next in lessons_day[static_index + 1:]:
#                             # print("INDEX", index)
#                             if check_is_30_minutes_between(lesson_day.lesson_start,
#                                                            lesson_day_next.lesson_start):
#                                 if lesson_day_next.student_mailing_status == 1:
#                                     # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
#                                     await scheduler_storage.delete_schedule(
#                                         f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}')
#                                     # print('Я DELETE')
#                                     break
#                                 else:
#                                     break
#                             else:
#                                 break
#
#                     if lesson_day.student_mailing_status == 1:
#                         # Если статус равен единице и слева нет соседей, то ставим уведомление
#                         if index != 0 and not check_is_30_minutes_between(lessons_day[index-1].lesson_start,
#                                                                           lesson_day.lesson_start):
#                             result_sent_time, until_hour, until_minute = \
#                                 give_correct_time_schedule_before_lesson(lesson_day.lesson_start,
#                                                                          week_date,
#                                                                          until_hour,
#                                                                          until_minute)
#                             await scheduler_storage.add_schedule(
#                                 create_scheduled_task(task_name='notice_lesson_certain_time_student',
#                                                       kwargs={'student_id': student_id,
#                                                               'lesson_start': lesson_day.lesson_start,
#                                                               'time_before_lesson': [until_hour, until_minute]
#                                                               },
#                                                       labels={str(student_id): [str(lesson_day.lesson_start),
#                                                                                 str(lesson_day.week_date)]},
#                                                       schedule_id=f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}',
#                                                       time=result_sent_time + timedelta(seconds=5)
#                                                       # cron='* * * * *',
#                                                       # cron_offset='Europe/Moscow'
#                                                       )
#                             )
#                             print(f'Будет отправлено в {result_sent_time}')
#                         continue
#
#                     only_change = False
#
#                     if index != 0 and lessons_day[index - 1].student_mailing_status == 1 and \
#                             check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
#                                                         lessons_day[index].lesson_start):
#                         only_change = True
#                         # print("ПОПАЛ")
#
#                     lesson_day.student_mailing_status = 1
#
#                     if not only_change:
#
#                         result_sent_time, until_hour, until_minute = \
#                                             give_correct_time_schedule_before_lesson(lesson_day.lesson_start,
#                                                                                      week_date,
#                                                                                      until_hour,
#                                                                                      until_minute)
#                         await scheduler_storage.add_schedule(
#                             create_scheduled_task(task_name='notice_lesson_certain_time_student',
#                                                   kwargs={'student_id': student_id,
#                                                           'lesson_start': lesson_day.lesson_start,
#                                                           'time_before_lesson': [until_hour, until_minute]
#                                                           },
#                                                   labels={str(student_id): [str(lesson_day.lesson_start),
#                                                                             str(lesson_day.week_date)]},
#                                                   schedule_id=f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}',
#                                                   time=result_sent_time + timedelta(seconds=5)
#                                                   # cron='* * * * *',
#                                                   # cron_offset='Europe/Moscow'
#                                                   )
#                         )
#                         print(f'Будет отправлено в {result_sent_time}')
#
#     # print(scheduled_tasks)
#     for x in await scheduler_storage.get_schedules():
#         print(x.schedule_id)
#     await scheduler_storage.shutdown()
