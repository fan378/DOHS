import os
import json
from commons.utils import *
from commons.preprocess import *
from commons.constants import *
from tqdm import tqdm
import random
random.seed(2023)
import numpy as np

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

def get_csv(keshi,start_num=0,end_num=-1,out_dir_name = '病人原始数据',flag=True):
    os.makedirs(out_dir_name,exist_ok=True)

    data_dir_list = os.listdir(f'/HL_user01/emr_datas/{keshi}')
    if 'old' in data_dir_list:
        data_dir_list.remove('old')

    keshi_zylsh = read_json('/HL_user01/yc_ruxianwaike_test/科室to诊疗流水号.json')
    all_zylsh_list = keshi_zylsh[keshi]
    need = int(len(all_zylsh_list)*0.85)
    all_zylsh_list = all_zylsh_list[need:]
    zylsh_list = all_zylsh_list[start_num:end_num]
    a = np.array(zylsh_list)
    np.savetxt(f'./流水号/{keshi}_新增源文件流水号.csv', a, fmt="%s", delimiter=',')

    if flag:
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

def get_csv_with_zylsh(zylsh,keshi,out_dir_name):
    os.makedirs(out_dir_name,exist_ok=True)
    data_dir_list = os.listdir(f'/HL_user01/emr_datas/{keshi}')
    if 'old' in data_dir_list:
        data_dir_list.remove('old')

    for data_dir in data_dir_list:
        final_data_dir = f'/HL_user01/emr_datas/{keshi}/{data_dir}'
        datas = load_excel_csv(final_data_dir)
        datas.fillna('',inplace=True)

        out_dir = f'{out_dir_name}/{keshi}/{zylsh}'
        os.makedirs(out_dir,exist_ok=True)
        out_dir = f'{out_dir_name}/{keshi}/{zylsh}/{data_dir}'
        temp = datas.loc[datas[0] == zylsh]
        temp.to_csv(out_dir,header=None,index=False)

if __name__=='__main__':
    print(sys.argv)
    keshi = sys.argv[1]
    zylsh = sys.argv[2]
    start_num = int(sys.argv[3])
    end_num = int(sys.argv[4])
    out_dir_name = sys.argv[5]
    flag = bool(int(sys.argv[6]))
    print(flag)
    if zylsh=='-2':
        get_csv(keshi,start_num=start_num,end_num=end_num,out_dir_name=out_dir_name,flag = flag)
    elif zylsh == '-1':
        get_csv(keshi,start_num=0,end_num=-1,out_dir_name=out_dir_name,flag = flag)
    else:
        get_csv_with_zylsh(zylsh,keshi,out_dir_name)
    # python get_patients_csv.py ruxianwaike 0 -1 original_csv

