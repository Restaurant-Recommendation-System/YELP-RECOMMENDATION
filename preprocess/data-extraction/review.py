import os
import datetime
import json
import re
import math
import numpy as np
import operator
import collections

file_name = "yelp_academic_dataset_review.json"
path = "./" + file_name

review = []

fInput = open(path,'r')
for line in fInput:
	txt = "[" + line.rstrip() + "]"
	json_txt = json.loads(txt)
	review.append([json_txt[0]["review_id"], json_txt[0]["stars"], json_txt[0]["text"]])

fInput.close()

print review