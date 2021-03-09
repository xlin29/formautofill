# generate HTML of email <input>s and <select>s
# distribute email addresses to 199 <select> elements.

from itertools import combinations
import random
import json

# max # of values
all_tests = [str(i) for i in range(40662)]
# max # of <select>s
all_menus = [i for i in range(199)]

comb_value2 = list(combinations(all_menus, 2))
comb_value3 = list(combinations(all_menus, 3))
menu_dt = {}
in_values = {}

for i in range(199):
    menu_dt[i] = [all_tests[i]]
    in_values[str(all_tests[i])] = [i]
index = 199
print('# of values after step 1', len(in_values.keys()))

for ind, each in enumerate(comb_value2):
    for k in each:
        menu_dt[k].append(all_tests[index+ind])
        if str(all_tests[index+ind]) in in_values.keys():
            in_values[str(all_tests[index+ind])].append(k)
        else:
            in_values[str(all_tests[index + ind])] = [k]


print('# of values after step 2', len(in_values.keys()))
print('# of menus', len(menu_dt.keys()))
print("1 menu value", index)

index = 19900
print("2 menu value", index-199)
times = {}
for i in range(199):
    times[i] = 199
count = 0

random.Random(3).shuffle(comb_value3)
for ind, each in enumerate(comb_value3):
    flag = 0
    for k in each:
        if times[k] >= 512:
            flag = 1
    if flag:
        continue
    for k in each:
        menu_dt[k].append(all_tests[index + count])
        times[k] += 1
        if str(all_tests[index + count]) in in_values.keys():
            in_values[str(all_tests[index + count])].append(k)
        else:
            in_values[str(all_tests[index + count])] = [k]
    count += 1


print("3 menu value", len(in_values.keys())-19900)
print('# of values after step 3', len(in_values.keys()))


freq_dist = [len(v) for i, v in menu_dt.items()]
sum_value = sum(freq_dist)
print('total # of options used--', sum_value)


with open('../select.txt', 'w', encoding='utf8') as f:
    count = 0
    for key, value in menu_dt.items():
        if count % 6 == 0:
            f.write('<br>')
        # set autocomplete type to email
        f.write(str(key) + '<select id="' + str(key) + '" autocomplete="email">' + '\n')
        for each in list(value):
            # define email address pattern
            f.write('<option value="email' + each + '">email' + each + '</option>' + '\n')
        f.write('</select>' + '\n')
        count += 1

empty_keys = [k for k, v in in_values.items() if not v]
for k in empty_keys:
    del in_values[k]
print("total # of values--", len(in_values.keys()))

with open('../dict.json', 'w', encoding='utf8') as f1:
    json.dump(in_values, f1)



