import sys
sys.path.append('./2024_5_31出院小结完整演示/')
from commons.utils import *
from commons.preprocess import *
from commons.constants import *
sys.path.append('../')
import pandas as pd
from tqdm import tqdm
import re
from bs4 import BeautifulSoup,Tag
import bs4
from copy import deepcopy
from collections import defaultdict
import pandas as pd
import json
import jsonlines
import random
from tqdm import tqdm
from transformers import AutoTokenizer
import jieba
random.seed(2023)

import json
import os
def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

def read_json(path):
    with open(path,'r') as f:
        content = json.load(f)
    return content

def save_json(path,content):
    with open(path,'w',encoding='utf8') as f:
        json.dump(content,f,ensure_ascii=False,indent=4)

def get_csv(zylsh_list,keshi):
    out_dir_name = '病人原始数据'
    os.makedirs(out_dir_name,exist_ok=True)

    data_dir_list = os.listdir(f'/HL_user01/emr_datas/{keshi}')
    if 'old' in data_dir_list:
        data_dir_list.remove('old')

    for data_dir in data_dir_list:
        final_data_dir = f'/HL_user01/emr_datas/{keshi}/{data_dir}'
        datas = load_excel_csv(final_data_dir)
        datas.fillna('',inplace=True)

        for zylsh in zylsh_list:
            out_dir = f'{out_dir_name}/{keshi}/{zylsh}'
            os.makedirs(out_dir,exist_ok=True)
            out_dir = f'{out_dir_name}/{keshi}/{zylsh}/{data_dir}'
            temp = datas.loc[datas[0] == zylsh]
            temp.to_csv(out_dir,header=None,index=False)

def get_cyxj(zylsh_list,keshi):
    create_dir(f'./2024_5_31出院小结完整演示/doctor_generated/{keshi}')
    chinese_keshi = cons_chinese_keshis[keshi]
    for zylsh in zylsh_list:
        # read_dir =  f'./2024_5_31出院小结完整演示/processed/{keshi}/{zylsh}/合并.json'
        read_dir =  f'/HL_user01/processed_emr_datas_json/{keshi}/{chinese_keshi}.json'

        out_dir =  f'./2024_5_31出院小结完整演示/doctor_generated/{keshi}/{zylsh}/{zylsh}.json'
        with open(read_dir,'r') as f:
            content = json.load(f)
        if '出院小结' not in content[zylsh].keys():
            continue
        doctor_content = content[zylsh]['出院小结']['内容']
        out_content = { zylsh : doctor_content}
        create_dir(f'./2024_5_31出院小结完整演示/doctor_generated/{keshi}/{zylsh}')
        with open(out_dir,'w',encoding='utf8') as f:
            json.dump(out_content,f,ensure_ascii=False,indent=4)

def generate_cyxj(zylsh):
    return


# print(data_dir_list)
# keshi = 'ruxianwaike'
# zylsh = '20070200000422'

keshi_number = 4
zylsh_number = 10
keshi_list = ['yanke', 'zhongyike', 'neifenmi', 'xiaohuaneike', 'huxineike', 'shenjingneike', 'shenzangneike', 'ruxianwaike', 'fuke', 'jiazhuangxianxueguanwaike', 'zhongliuke', 'xiaoerke', 'erbihouke', 'shenjingwaike', 'weichangwaike']
keshi_json_list = ['眼科.json','中医科.json','内分泌.json','消化内科.json','呼吸内科.json','神经内科.json','肾脏内科.json','乳腺外科.json','妇科.json','甲状腺血管外科.json','肿瘤科.json','小儿科.json','耳鼻喉科.json','神经外科.json','胃肠外科.json']
keshi_zylsh = read_json('科室to诊疗流水号.json')
keshi_index_list = [11]

for keshi_index in tqdm(keshi_index_list):
# for keshi_index in tqdm(range(keshi_number)):
    all_zylsh_list = keshi_zylsh[keshi_list[keshi_index]]
    all_zylsh_list = ['19030700000328']
    # get_csv(all_zylsh_list[:zylsh_number],keshi_list[keshi_index])  
    get_csv(all_zylsh_list,'ruxianwaike')  
    # get_cyxj(all_zylsh_list[:zylsh_number],keshi_list[keshi_index])
    # get_cyxj(all_zylsh_list[:zylsh_number],'ruxianwaike')


