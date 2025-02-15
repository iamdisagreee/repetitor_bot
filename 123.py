from datetime import time, timedelta, datetime, date


#
#
# def a(time1: time, time2: time):
#     d1 = timedelta(hours=time1.hour, minutes=time1.minute)
#     d2 = timedelta(hours=time2.hour, minutes=time2.minute)
#
#     return d2 - d1
#
#
# time1 = time(14, 20)
# time2 = time(14, 20)
#
# d1 = timedelta(hours=time1.hour, minutes=time1.minute)
# d2 = timedelta(hours=time2.hour, minutes=time2.minute)
#
# print(d1 == d2)
# from datetime import date
#
#
# # days: возвращает количество дней
# #
# # seconds: возвращает количество секунд
# #
# # microseconds: возвращает количество микросекунд
# #
# # total_second()
# def b(b1: int, b2: int):
#     print(b1, b2)
#
#
# a = {'b1': 132,
#      'b2': 999}
#
# b(**a)
#
# a = date.today()
# print(a.year, a.day, a.month, a.isoweekday())

def b(**a):
    print(a)


a = {'1': '2',
     '2': '3'}
b(**a)


def c():
    return {'a': 1, "b": 2}


d = c()
print(d)

# tim = datetime.now()
#
# day_of_the_month = tim.strftime("%H:%M")
# print(day_of_the_month, type(day_of_the_month))
# def abc(t: time):
#     print(t)
#
#
# d = time(hour=12, minute=13)
# e = time(hour=13, minute=40)
# delta1 = timedelta(hours=d.hour, minutes=d.minute)
# delta2 = timedelta(hours=e.hour, minutes=e.minute)
# print((delta2 - delta1) > timedelta(minutes=30))

# def b(**a):
#     print(command)
# a= {'command':2}

a = timedelta(minutes=1)
b = time(hour=12, minute=12)
now = datetime.now()
c = datetime(year=now.year, month=now.month, day=now.day,
             hour=b.hour, minute=b.minute)

print((a+c).minute)
