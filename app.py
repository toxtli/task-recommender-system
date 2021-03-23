import sys
import json
import pytz
import time
import datetime
import pandas as pd
from datetime import datetime
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
	return '''
	<form action="/upload" method="post" enctype="multipart/form-data">
	  Select data file:
	  <input type="text" name="user" value="1">
	  <input type="file" name="file">
	  <input type="submit" value="Upload">
	</form>
	'''

@app.route('/upload', methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		data_file = 'mturk.json'
		if 'file' in request.files:
			try:
				print('FILE LOADED')
				tasks = json.load(request.files['file'])
			except:
				print(sys.exc_info())
				return '[]'
		else:
			print('DEFAULT FILE')
			tasks = json.load(open(data_file, 'r'))

		cur_time = time.time() * 1000
		num_hours = 5
		timezone_str = 'US/Eastern'
		time_rate = 0.33

		tz = pytz.timezone(timezone_str)
		time_ini = datetime.timestamp(datetime.now(tz))
		time_end = cur_time + (num_hours * 60 * 60)

		all_records = []
		block_ids = []

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

		df_records = df_records[df_records['caller_meets_requirements']==True]
		#df_records = df_records[df_records['caller_meets_preview_requirements']==True]
		records = df_records[(df_records['time_ini']<time_end) & (df_records['time_end']>time_ini)]
		records = records.sort_values('amount_in_dollars', ascending=False)
		cur_time_ini = time_ini
		for i, record in records.iterrows():
			if (cur_time_ini + record['time_block']) <= time_end and (cur_time_ini + record['time_block']) <= record['time_end']:
			  block_ids.append(record['id'])
			  cur_time_ini += record['time_block']
		urls = []
		for i,block_id in enumerate(block_ids):
			# url = '<a target="_blank" href=https://worker.mturk.com/projects/' + block_id + '/tasks?ref=w_pl_prvw>' + str(i) + '</a>'
			url = block_id
			urls.append(url)
		return json.dumps(urls)
	else:
		return index()

if __name__ == '__main__':
        app.run(host='0.0.0.0')