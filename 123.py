from datetime import time, datetime, timedelta

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


a1 = time(23, 47)
hour = 0
minute = 5

print(give_correct_time_schedule_before_lesson(a1, hour, minute))

# print(d)ф

