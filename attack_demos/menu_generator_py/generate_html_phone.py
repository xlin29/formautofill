# generate HTML of phone number <input>s and <select>s
# distribute phone numbers to 198 <select> elements.

from itertools import combinations
from collections import defaultdict
import random
import json

# max size of each <select>
max_size = 1420
# # of <select>s
num_menu = 199
# max # of values
num_values = num_menu * max_size
all_tests = [str(i) for i in range(num_values)]
# max # of <select>s
all_menus = [i for i in range(num_menu)]


comb_value2 = list(combinations(all_menus, 2))
comb_value3 = list(combinations(all_menus, 3))

menu_dt = {}
in_values = {}

for i in range(num_menu):
    menu_dt[i] = [all_tests[i]]
    in_values[str(all_tests[i])] = [i]
new_values = {}
for i in range(num_menu):
    new_values[i] = []

index1 = num_menu
print('# of values after step 1', len(in_values.keys()))

for ind, each in enumerate(comb_value2):
    for k in each:
        menu_dt[k].append(all_tests[index1+ind])
        if str(all_tests[index1+ind]) in in_values.keys():
            in_values[str(all_tests[index1+ind])].append(k)
        else:
            in_values[str(all_tests[index1 + ind])] = [k]


print('# of values after step 2', len(in_values.keys()))
print('# of menus', len(menu_dt.keys()))
print("1 menu value", index1)

index2 = len(in_values.keys())
print("2 menu value", index2-num_menu)

# # of times values put into this <select>
times = {}
for i in range(num_menu):
    times[i] = num_menu
count = 0

random.Random(2).shuffle(comb_value3)

for ind, each in enumerate(comb_value3):
    flag = 0
    for k in each:
        if times[k] >= max_size:
            flag = 1
    if flag:
        continue
    for k in each:
        menu_dt[k].append(all_tests[index2 + count])
        times[k] += 1
        if str(all_tests[index2 + count]) in in_values.keys():
            in_values[str(all_tests[index2 + count])].append(k)
        else:
            in_values[str(all_tests[index2 + count])] = [k]
    count += 1

new_in_values = defaultdict(list)
for ind, each in menu_dt.items():
    for val in each:
        val_str = '1234' + str(val).zfill(6)
        new_values[ind].append(val_str)
        new_in_values[val_str].append(ind)

for ind, each in new_values.items():
    print(ind, each)


print("3 menu value", len(in_values.keys())-index2-num_menu)
print('# of values after step 3', len(in_values.keys()))


freq_dist = [len(v) for i, v in menu_dt.items()]
sum_value = sum(freq_dist)
print('total # of options used--', sum_value)


with open('../input_phone.txt', 'w', encoding='utf8') as f:
    count = 0
    for key, value in menu_dt.items():
        if count % 5 == 0:
            f.write('<br>')
        f.write('<input name="PHONE">' + '\n')
        count += 1

with open('../select_phone.txt', 'w', encoding='utf8') as f:
    count = 0
    for key, value in new_values.items():
        if count % 5 == 0:
            f.write('<br>')
        f.write('  '+str(key) + '<select id="' + str(key) + '">' + '\n')
        for each in list(value):
            f.write('<option value="' + each + '">' + each + '</option>' + '\n')
        f.write('</select>' + '\n')
        count += 1

empty_keys = [k for k, v in new_in_values.items() if not v]
for k in empty_keys:
    del new_in_values[k]
print("total # of values--", len(new_in_values.keys()))

min_phone, max_phone = min(list(new_in_values.keys())), max(list(new_in_values.keys()))
print(f"min phone: {min_phone}, max phone: {max_phone}")

with open('../dict_phone.json', 'w', encoding='utf8') as f1:
    json.dump(new_in_values, f1)

