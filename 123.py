from datetime import datetime, time, timedelta, date

my_dict = {'a': [1, 2, 3]}

print(my_dict['a'] + [4])


a = time(hour=13, minute=12)
b = time(12, 11)
td = (timedelta(hours=a.hour, minutes=a.minute) - timedelta(hours=b.hour, minutes=b.minute)).total_seconds()
# print(f'{int(td // 3600)} ч. {int(td // 60 % 60)} мин.')

print(len('a;Петр;Петров;fey;2025-03-13;10:00;10:30;500'.encode()))

print(datetime.now().date() == date.today())

a = {'a': 1,
     'b': 2}
b = iter(a)

for el in b:
    print(el)
    break
for el in b:
    print(el)

print(type(date.today()))