import pandas as pd
import jsonlines
import os
from collections import defaultdict
from copy import deepcopy
import json
import sys


    
key_id = sys.argv[1]
input_file_fuza='演示示例/复杂字段'+key_id+'.json'
input_file_simple='演示示例/简单字段'+key_id+'.json'

with open(input_file_fuza, 'r') as f:
    fuza_data = json.load(f)

with open(input_file_simple, 'r') as f:
    simple_data = json.load(f)   

formats = {
    "基本信息": {
        "出院诊断": "出院诊断",
        "床号": "患者基本信息---床号",
        "科别": "患者基本信息---科别",
        "入院时间": "患者基本信息---入院时间",
        "出院时间": "患者基本信息---出院时间",
        "姓名": "患者基本信息---姓名",
        "性别": "患者基本信息---性别",
        "年龄": "患者基本信息---年龄",
        "住院号": "患者基本信息---住院号",
        "入院诊断": "患者基本信息---入院诊断"
    },
    "入院时简要病史": "患者基本信息---入院时简要病史",
    "体检摘要": "患者基本信息---体检摘要",
    "生命体征": {
        "T": "患者基本信息---体温(T)",
        "P": "患者基本信息---脉搏(P)",
        "R": "患者基本信息---呼吸(R)",
        "BP高": "患者基本信息---高压(BP高)",
        "BP低": "患者基本信息---低压(BP低)"
    },
    "住院期间医疗情况": "住院期间医疗情况",
    "出院时情况": "出院时情况",
    "病程与治疗情况": "病程与治疗情况",
    "出院后用药建议": "出院后用药建议",
    "病人信息": {
        "姓名": "患者基本信息---姓名",
        "性别": "患者基本信息---性别",
        "科室": "患者基本信息---科别",
        "床号": "患者基本信息---床号",
        "住院号": "患者基本信息---住院号",
        "住院流水号": "",
        "年龄": "患者基本信息---年龄",
        "出生年月": "",
        "入院时间": "患者基本信息---入院时间",
        "出院时间": "患者基本信息---出院时间"
    }
}

for patient_id,ziduan in fuza_data.items():
    for ziduan2,content in simple_data[patient_id].items():
        if ziduan2!='出院时情况':
            fuza_data[patient_id].setdefault(ziduan2,content)
            
# columns = 13
# converters = {col:str for col in range(columns)}

# datas = pd.read_csv('/data/zhongboyang/瑞金/ruxian/最终处理并合并后数据.csv',converters=converters,header=None)

import json
# def transfer_value(val):
#     if val == '':
#         return {}
#     else:
#         return json.loads(val)
# for col in datas.columns[1:]:
#     datas[col] = datas[col].apply(transfer_value)

    
    
# data = datas.loc[datas[0] == key_id]
# jiancha_list = data.iat[0,9]
# jianyan_list = data.iat[0,11]
# yiliao_str = ''
# for jiancha in jiancha_list:
#     if jiancha['检查描述'] == '':
#         desc = jiancha['检查子类型']
#     else:
#         desc = jiancha['检查描述']
#     yiliao_str = yiliao_str + '{} {}:{} '.format(jiancha['报告时间'].split(' ')[0],desc,jiancha['图像分析'])
# for jianyan in jianyan_list:
#     jianyan_details = jianyan['检验详情']
#     jianyan_time = jianyan_details[0]['报告时间'].split(' ')[0]
#     yiliao_str = yiliao_str + '{} '.format(jianyan_time)
#     for jianyan_item in jianyan_details:
#         yiliao_str = yiliao_str + '{} {}{} '.format(jianyan_item['检验指标'],jianyan_item['检测值'],jianyan_item['单位'])
# # break
# fuza_data[key_id]['住院期间医疗情况'] = yiliao_str

def update_formats_with_ori_data(formats, ori_datas):
    for key, value in formats.items():
        if isinstance(value, dict):
            for sub_key, path in value.items():
                path_parts = path.split('---')
                data = ori_datas
                for part in path_parts:
                    data = data.get(part, "")
                    if isinstance(data, list):
                        if len(data)>=1:
                            data=data[0]
                formats[key][sub_key] = data
        elif isinstance(value, str):
            path_parts = value.split('---')
            data = ori_datas
            for part in path_parts:
                data = data.get(part, "")
                if isinstance(data, list):
                    if len(data)>=1:
                        data=data[0]
            formats[key] = data
            
            
all_jsons={}
for k,data in fuza_data.items():
    all_jsons[k] = deepcopy(formats)
    update_formats_with_ori_data(all_jsons[k],fuza_data[k])
    # 住院流水号单独处理一下
    all_jsons[k]['病人信息']['住院流水号'] = k
def save_json(save_path, data):
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4,ensure_ascii=False)

rname="演示示例/"+key_id+".json"
save_json(rname,all_jsons)