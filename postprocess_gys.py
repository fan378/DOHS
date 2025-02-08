# 全部由模型生成结果后的后处理步骤
import csv
import pandas as pd
import jsonlines
import os
import shutil
from collections import defaultdict
from copy import deepcopy
import json
import sys
import re

from tqdm import tqdm

from commons.utils import load_excel_csv
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
    "入院时简要病史": "入院时简要病史",
    "体检摘要": "体检摘要",
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

import re

def extract_data(text):
    print(text)
    pattern = r'体温([\d.]+) ?°C|脉搏(\d+)次/分|呼吸(\d+)次/分|血压(\d+)/(\d+)mmHg'
    matches = re.findall(pattern, text)
    print(matches)
    # 提取匹配结果并去除None值
    results = [match for group in matches for match in group if match]
    return results

def transfer_value(val):
    '''
    load dataframe后，字符串转json
    '''
    if val == '':
        return []
    else:
        return json.loads(val)

def get_source_wenshu_list(zylsh, keshi):
    processed_file = f"./processed/{keshi}/{zylsh}/new_最终处理并合并后数据.csv"
    datas = load_excel_csv(processed_file)
    datas.fillna('', inplace=True)

    for col in datas.columns[1:]:
        datas[col] = datas[col].apply(transfer_value)
    
    # processed 后的数据
    data_processed = datas.iloc[0,:].copy()
    wenshu_list = data_processed.iat[5]

    return wenshu_list



def update_formats_with_ori_data(zylsh, keshi, formats, ori_datas, ori_source):
    if ori_datas['患者基本信息'] == '输入数据过长，模型无法输出！':
        ori_datas['患者基本信息'] = {
            "住院号": "over_length",
            "床号": "over_length",
            "入院时间": "over_length",
            "出院时间": "over_length",
            "科别": "over_length",
            "科室": "over_length",
            "姓名": "over_length",
            "年龄": "over_length",
            "性别": "over_length",
            "低压(BP低)": "over_length",
            "高压(BP高)": "over_length",
            "脉搏(P)": "over_length",
            "呼吸(R)": "over_length",
            "体温(T)": "over_length",
            "入院诊断": "over_length",
        }
    # 获取患者的原始文书
    wenshu_list = get_source_wenshu_list(zylsh, keshi)


    # 【病史随访】读取病史随访科室对应CSV文件
    suifang_keshi_dict = {}
    with open('病史随访科室对应.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过标题行
        for row in reader:
            suifang_keshi_dict[row[0]] = row[1]
    # 获取患者入院记录中的 “既往史”
    for wenshu in wenshu_list:
        if '入院记录' in wenshu['文书名']:
            if '既往史' in wenshu['内容']:
                past_history = wenshu['内容']['既往史']
                break   


    # 如果出院时间无法判断，直接使用最近的医嘱时间作为出院时间
    if ori_datas['患者基本信息']['出院时间'] == '无法判断':
        ori_datas['患者基本信息']['出院时间'] = ori_source['患者基本信息'].split('医嘱时间:')[1].split('\n')[0]


    # 住院期间医疗情况 = 简化过滤检验 + 全部检查
    temp = ori_source['住院期间医疗情况'].split('###简化过滤检验:')[1].split('###')[0] + ori_source['住院期间医疗情况'].split('###全部检查:')[1].split('###')[0]
    ori_datas['住院期间医疗情况'] = temp.replace("报告时间:", "").strip('\n')


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


def save_json(save_path, data):
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4,ensure_ascii=False)         


def postprocess(key_id, keshi,read_dir = '全部由模型生成',out_dir = '全部由模型生成', data_dir='全部由模型生成'):
    input_file = os.path.join(read_dir,'{}.json'.format(key_id))

    with open(input_file, 'r',encoding='utf8') as f:
        datas = json.load(f)

    # output取output字段，溯源取source字段
    zylshs = list(datas.keys())
    # os.remove(os.path.join(read_dir,'{}.json'.format(key_id)))
    for zylsh in zylshs:
        data_save_dir = os.path.join(data_dir,zylsh)
        if not os.path.exists(data_save_dir):
            os.makedirs(data_save_dir)
        save_json(os.path.join(data_save_dir,'{}.json'.format(zylsh)),{zylsh:datas[zylsh]})
        data = datas[zylsh]

        data_output = data['output']
        data_output_source = data['find_source']
        data_source = {
            zylsh:data['find_source']
        }
        
        # 处理成医院格式
        processed_data = deepcopy(formats)
        update_formats_with_ori_data(zylsh, keshi, processed_data,data_output, data_output_source)
            
        # 处理一下住院流水号
        processed_data['病人信息']['住院流水号'] = zylsh
        processed_json = {
            zylsh:processed_data
        }
        # 输出
        rname=os.path.join(data_save_dir,"{}_postprocessed.json".format(zylsh))
        save_json(rname,processed_json)
        rname=os.path.join(data_save_dir,"{}_findsource.json".format(zylsh))
        save_json(rname,data_source)
    return zylshs


if __name__ == '__main__':
    print('构造指令数据')
    data_dir = sys.argv[1]
    keshi = sys.argv[2]
    zylsh = sys.argv[3]
    out_dir = sys.argv[4]
    data_dir = os.path.join(data_dir,keshi)

    show_dir = '/HL_user01/2024_03_24_生成出院小结_演示/演示/全部由模型生成'

    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    else:
        zylshs = [zylsh]

    print('处理{}个病例'.format(len(zylshs)))
    for zylsh in zylshs:
        read_dir = os.path.join(data_dir,zylsh)
        now_out_dir = os.path.join(out_dir,keshi,zylsh)
        tmp_zylshs = postprocess(zylsh,keshi,read_dir,now_out_dir,data_dir)
        for tmp_zylsh in tmp_zylshs:
            data_save_dir = os.path.join(data_dir,tmp_zylsh)

            source = os.path.join(data_save_dir,'{}.json'.format(tmp_zylsh))
            target = os.path.join(show_dir,'{}.json'.format(tmp_zylsh))
            shutil.copy(source,target)

            source = os.path.join(data_save_dir,'{}_postprocessed.json'.format(tmp_zylsh))
            target = os.path.join(show_dir,'{}_postprocessed.json'.format(tmp_zylsh))
            shutil.copy(source,target)

            source = os.path.join(data_save_dir,'{}_findsource.json'.format(tmp_zylsh))
            target = os.path.join(show_dir,'{}_findsource.json'.format(tmp_zylsh))
            shutil.copy(source,target)
