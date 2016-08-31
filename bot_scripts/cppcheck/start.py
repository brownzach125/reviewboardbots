import os
import shutil
import difflib
import subprocess
import sys
import re
import json
from reviewboardbots.responseagent import ResponseAgent

def get_latest_revision(path):
	get_request_id
	latest_id = -1

	#match digits at end of string
	digits = re.compile('.*?(\d+)$')
	for folder_name in os.listdir(path):
		full_path = os.path.join(path, folder_name)
		if os.path.isdir(full_path):
			rev_id = int(re.match(digits, folder_name).group(1))
			if rev_id > latest_id:
				latest_id = rev_id
				latest_id_path = full_path
	return latest_id_path, latest_id

def get_request_id(path):
	with open(os.path.join(path, 'info')) as info_file:
		return json.load(info_file)['id']

def call_cppcheck(filename):

	#TODO: add cpplint
	cppcheck = os.path.join(os.path.dirname(__file__), 'cppcheck')
	return subprocess.Popen([cppcheck, "--enable=style,performance,portability", filename],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[1]

def split_line_info(line_list):
	split_lines = [x.split(':') for x in line_list]
	
	return ([x[-1] for x in split_lines], [x[:-1] for x in split_lines])

def process_change(folder_path):
	
	with open(os.path.join(folder_path, 'metadata.json')) as metadata_file:
		json_obj = json.load(metadata_file)
		filename = json_obj['name']
		file_id = json_obj['id']

	old_filename = os.path.join(folder_path, 'original')
	new_filename = os.path.join(folder_path, 'patched')

	output_old = call_cppcheck(old_filename)
	output_new = call_cppcheck(new_filename)
	output_old_list, output_new_list =  output_old.split('\n'), output_new.split('\n')
	
	output_old_warnings, output_old_line_info = split_line_info(output_old_list)
	output_new_warnings, output_new_line_info = split_line_info(output_new_list)
	differ = difflib.Differ()
	diff_lines = differ.compare(output_old_warnings, output_new_warnings)
	print output_new_warnings
	comments = []

	#match digits at beginning of string
	digits = re.compile('(\d+)')

	for diff, line_info in zip(diff_lines, output_new_line_info):
		if diff.startswith('+'):
			print "diff: %s" % diff
			if len(line_info) > 0:
				line_number = line_info[-1]
			else:
				line_number = "0"

			match = re.match(digits,line_number)
			if match:
				first_line = match.group(1)
			else:
				first_line = 0

			comments.append({
				"filediff_id":file_id,
				"first_line":int(first_line),
				"num_lines":1,
				"text": diff[2:]	
			})

	return comments

def run(path):
	revision_path, revision_id = get_latest_revision(path)
	request_id = get_request_id(path)

	comments = []
	for folder_name in os.listdir(revision_path):
		full_path = os.path.join(revision_path, folder_name)
		print full_path
		if os.path.isdir(full_path):
			comments += process_change(full_path)

	agent = ResponseAgent('http://pds-rbdev01', 'cppcheck', 'fpRocks')
	response = {
		'request_id':request_id, 
		'revision_id':revision_id,
		'comments':comments,
		'message': "See comments",
		'ship_it': len(comments) == 0
	}
	agent.respond(response)




if __name__ == "__main__":
	run(sys.argv[1])