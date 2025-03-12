from datetime import datetime, time, timedelta

my_dict = {'a': [1, 2, 3]}

print(my_dict['a'] + [4])


a = time(hour=13, minute=12)
b = time(12, 11)
td = (timedelta(hours=a.hour, minutes=a.minute) - timedelta(hours=b.hour, minutes=b.minute)).total_seconds()
# print(f'{int(td // 3600)} ч. {int(td // 60 % 60)} мин.')

print(0+timedelta(minutes=1))