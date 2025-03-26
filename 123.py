from datetime import time

from services.services_taskiq import check_is_30_minutes_between

a = [1, 2, 3]

print(a[2:])

for x,y in enumerate([11,2,3]):
    print(x,y)


print(check_is_30_minutes_between(time(hour=14, minute=00), time(hour=16, minute=30)))