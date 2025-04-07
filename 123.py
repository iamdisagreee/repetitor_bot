from datetime import time, datetime, timedelta, date

from services.services_taskiq import check_is_30_minutes_between, give_correct_time_schedule_before_lesson

#
# a = [1, 2, 3]
#
# print(a[2:])
#
# for x,y in enumerate([11,2,3]):
#     print(x,y)
#
#
# print(check_is_30_minutes_between(time(hour=14, minute=00), time(hour=16, minute=30)))
#
# a = {time(12, 30): '123'}
#
# print(a.get(time(12,31)))


# def a():
#     return 12, 12
#
# h, m = a()
# a = {time(12, 12): '123123'}
#
# print(a.get(time(12,12)))


# a = {1: 123}
#
# c, d = list(a.items())[0]
# print(c, d)
# e = [123, 456]
# i1, i2 = e
# print(i1, i2)
#
# for x, y in enumerate([1,2,3]):
#     z = x
#     z += 1
#     print(x)

# lesson_start = time(22, 0)
# week_date = date(2025, 3, 28)
# until_hour = 30
# until_minute = 0
#
# result_sent_time, until_hour, until_minute = give_correct_time_schedule_before_lesson(
#     lesson_start, week_date, until_hour, until_minute
# )
#
# print(result_sent_time, until_hour, until_minute)

#
# a = {(1,2,3): 'a'}
# print(a)

# print(datetime.now() + timedelta(minutes=10) > datetime.now())

# dt_lesson = datetime(year=week_date.year, month=, day=,
#                      hour=lesson_start.hour, minute=lesson_start.minute)
