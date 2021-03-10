import json
import pytz
import time
import datetime
import pandas as pd
from datetime import datetime

data_file = 'mturk.json'
cur_time = time.time() * 1000
num_hours = 5
min_wage = 7.5
num_days = 1
date_format = "%Y-%m-%d"
time_format = "%H:%M:%S"
zone_format = '%H:%M:%S.%fZ'
delay = '05:00:00'
timezone_str = 'US/Eastern'
start_date = datetime.today().strftime(date_format)
start_time = 9
timezones = -4
working_hours = 8
time_rate = 0.33

date_time_zone_format = date_format + ' ' + time_format + ' ' + "%Z%z"
date_delay_format = date_format + ' ' + delay 
date_time_format = date_format + ' ' + time_format
conf_ini_date = start_date + ' ' + delay
conf_ini_date_gmt = start_date + ' 00:00:00'

tz = pytz.timezone(timezone_str)
time_ini = datetime.timestamp(datetime.now(tz))
time_end = cur_time + (num_hours * 60 * 60)


tasks = json.load(open(data_file, 'r'))
all_records = []
requirements_catalog = {
  'master_task': ['Masters'],
  'location_task': ['Location'],
  'rate_task': ['HIT approval rate (%)'],
  'approved_task': ['Total approved HITs'],
  'adult_task': ['Adult Content Qualification'],
  'our_task': ['CrowdCoach', 'Super Turker Users', 'GigOverhead Setup Diagnostic']
}
for task_id in tasks:
	record = tasks[task_id]
	record.update(record['monetary_reward'])
	record['requeriment_keywords'] = ''
	comma = ''
	has_other = False
	other_list = []
	record['other_requirements'] = 0
	record['id'] = record['hit_set_id']
	time_end_val = datetime.strptime(record['latest_expiration_time'],'%Y-%m-%dT%H:%M:%S.%fZ')
	record['time_end'] = datetime.timestamp(time_end_val)
	time_ini_val = datetime.strptime(record['creation_time'],'%Y-%m-%dT%H:%M:%S.%fZ')
	record['time_ini'] = datetime.timestamp(time_ini_val)
	record['time_block'] = record['assignment_duration_in_seconds'] * time_rate
	for requirement in record['project_requirements']:
	  if requirement['qualification_type']['visibility'] == False:
	    record['is_visible'] = False
	  if requirement['qualification_type']['is_requestable'] == False:
	    record['is_requestable'] = False
	  if requirement['qualification_type']['has_test'] == True:
	    record['has_test'] = True
	  keywords = requirement['qualification_type']['keywords'] if requirement['qualification_type']['keywords'] is not None else ''
	  record['requeriment_keywords'] += comma + keywords
	  comma = ','
	  found_name = False
	  for catalog_name in requirements_catalog:
	    if requirement['qualification_type']['name'] in requirements_catalog[catalog_name]:
	      record[catalog_name] = True
	      record[catalog_name + '_value'] = ','.join(requirement['qualification_values'])
	      found_name = True
	  if not found_name:
	    has_other = True
	    record['other_requirements'] += 1
	    other_list.append(','.join(requirement['qualification_values']))
	  if has_other:
	    record['other_task'] = True
	  record['other_task_value'] = ';'.join(other_list)
	  record['requeriment_keywords'] = ','.join(list(set(record['requeriment_keywords'].split(','))))
	all_records.append(record)
df_records = pd.DataFrame(all_records)

block_ids = []
records = df_records[(df_records['time_ini']<time_end) & (df_records['time_end']>time_ini)]
records = records.sort_values('amount_in_dollars', ascending=False)
cur_time_ini = time_ini
for i, record in records.iterrows():
	if (cur_time_ini + record['time_block']) <= time_end and (cur_time_ini + record['time_block']) <= record['time_end']:
	  block_ids.append(record['id'])
	  cur_time_ini += record['time_block']

json.dump(block_ids, open('results.json', 'w'))
print('DONE')