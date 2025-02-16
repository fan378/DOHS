import json
import os
import sys
import chardet
import traceback
import numpy as np
import pandas as pd
from commons.constants import *

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

# 检测文件编码
def detect_encoding(file):
    res_to_detest = b'' 
    with open(file, 'rb') as f:
        for line_idx,line in enumerate(f.readlines()):
            if line_idx == 10:
                break
            res_to_detest += line
    result = chardet.detect(res_to_detest)
    if result['encoding'] == 'GB2312':
        result['encoding'] = 'GB18030'
    return result

def load_excel_csv(file,columns=5,head=None):
    converters = {col:str for col in range(columns)}
    if file.endswith('csv'):
        result = detect_encoding(file)
        print('以{}编码格式加载csv文件:{}'.format(result['encoding'],file))
        ###############################################################################
        # 尝试读取文件的第一行以确定列数   yc添加
        with open(file, 'r', encoding=result['encoding']) as f:  
            first_line = f.readline().strip()  
            # 如果第一行是空的，则假设文件是空的  
            if not first_line:  
                return pd.DataFrame()  # 返回一个带有默认列名的空DataFrame  
        ################################################################################
        try:
            datas = pd.read_csv(file,header=head,converters=converters,encoding=result['encoding'],sep=',')
        except:
            datas = pd.read_csv(file,header=head,converters=converters,encoding=result['encoding'],sep='\t')
    else:
        print('加载excel文件:{}'.format(file))
        datas = pd.read_excel(file,header=head,converters=converters)
    if head!= None:
        datas.columns = list(range(len(datas.columns)))
    return datas

def transfer_value(val):
    '''
    load dataframe后，字符串转json
    '''
    if val == '':
        return []
    else:
        return json.loads(val)

def flatten_dict(d, merged, parent_key='', sep='---'):
    """递归函数，用于将嵌套的dict展平，并直接更新merged_dict"""
    for k, v in d.items():
        k = k.replace('TM员工名称TM','').strip()
        one_parent = parent_key.split('---')[0]
        new_key = f"{one_parent}{sep}{k}" if parent_key else k
        # new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            flatten_dict(v, merged, new_key, sep=sep)
        elif isinstance(v, list):
            # 如果值为list，需要考虑list内部是否还有dict
            for idx, item in enumerate(v):
                list_key = f"{new_key}"
                if isinstance(item, dict):
                    flatten_dict(item, merged, list_key)
                else:
                    if list_key in merged:
                        if not isinstance(merged[list_key], list):
                            merged[list_key] = [merged[list_key]]
                        merged[list_key].append(item)
                    else:
                        merged[list_key] = item
        else:
            if new_key in merged:
                if not isinstance(merged[new_key], list):
                    merged[new_key] = [merged[new_key]]
                merged[new_key].append(v)
            else:
                merged[new_key] = v

def get_cyxj(zylsh_list,keshi,processed_dir,doctor_dir):
    create_dir(os.path.join(doctor_dir,keshi))
    chinese_keshi = cons_chinese_keshis[keshi]
    for zylsh in zylsh_list:
        # print(processed_dir,keshi,zylsh,f'{zylsh}.json')
        # print(zylsh)
        try:
            read_dir = os.path.join(processed_dir,keshi,zylsh,'合并.json')
            out_dir =  os.path.join(doctor_dir,keshi,zylsh,f'{zylsh}.json')
            with open(read_dir,'r') as f:
                content = json.load(f)
            if '出院小结' not in content[zylsh].keys():
                continue
            doctor_content = content[zylsh]['出院小结']['内容']
            out_content = { zylsh : doctor_content}
            create_dir(os.path.join(doctor_dir,keshi,zylsh))
            with open(out_dir,'w',encoding='utf8') as f:
                json.dump(out_content,f,ensure_ascii=False,indent=4)
        except:
            traceback.print_exc()
            print(zylsh)

def get_cyxj_from_csv(zylsh_list,keshi,processed_dir,doctor_dir):
    create_dir(os.path.join(doctor_dir,keshi))
    
    data_name = 'new_最终处理并合并后数据.csv'
    for zylsh in zylsh_list:
        try:
            read_dir = os.path.join(processed_dir,keshi,zylsh,data_name)
            out_dir =  os.path.join(doctor_dir,keshi,zylsh,f'{zylsh}.json')

            datas = load_excel_csv(read_dir)
            datas.fillna('',inplace=True)
            for col in datas.columns[1:]:
                datas[col] = datas[col].apply(transfer_value)
            hulijilu_list = datas.iloc[0,:].iat[7]

            xiaojie = {}
            for data in hulijilu_list:
                if '出院小结' in data['护理记录名']:
                    xiaojie =  data['内容']
                    break

            out_content = { zylsh : xiaojie}
            create_dir(os.path.join(doctor_dir,keshi,zylsh))
            with open(out_dir,'w',encoding='utf8') as f:
                json.dump(out_content,f,ensure_ascii=False,indent=4)
        except:
            traceback.print_exc()
            print(zylsh)

if __name__=='__main__':
    zylsh = sys.argv[1]
    keshi = sys.argv[2]
    processed_dir = sys.argv[3]
    doctor_dir = sys.argv[4]
    data_dir = os.path.join(processed_dir,keshi)

    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    elif zylsh == '-2':
        zylshs = np.loadtxt(f'./流水号/{keshi}_新增源文件流水号.csv', delimiter=',',dtype='str')
    else:
        zylshs = [zylsh]
    # python get_patients_csv.py ruxianwaike 0 -1 original_csv
    print(f'抽取{len(zylshs)}份小结')
    # get_cyxj(zylshs,keshi,processed_dir,doctor_dir)
    # keshi = 'ruxianwaike'
    # zylshs = ['19031500000377']
    # processed_dir= './processed'
    # doctor_dir= './doctor_generated'
    get_cyxj_from_csv(zylshs,keshi,processed_dir,doctor_dir)
