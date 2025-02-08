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
from pipeline4fuza import HandleData
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
def extract_data_2(text):
    try:
        T = text.split("体温")[1].strip().split("℃")[0].strip()
        P = text.split("脉搏")[1].strip().split("次/分")[0].strip()
        R = text.split("呼吸")[1].strip().split("次/分")[0].strip()
        if len(text.split("血压")) != 2:
            BP_H = ""
            BP_L = ""
        else:
            BP_H = text.split("血压")[1].strip().split("mmHg")[0].split("/")[0].strip()
            BP_L = text.split("血压")[1].strip().split("mmHg")[0].split("/")[1].strip()
    except:
         T, P, R, BP_H, BP_L = ""
    return T, P, R, BP_H, BP_L


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


    suifang_keshi_dict = {}
    with open('病史随访科室对应.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过标题行
        for row in reader:
            suifang_keshi_dict[row[0]] = row[1]

    # print("suifang_keshi_dict:", suifang_keshi_dict)  # 打印随访科室字典

    result_jiwangshi_suifang = {}  # 存放既往史结果的随访字典

    # 获取患者入院记录中的“既往史”
    past_history = ""
    for wenshu in wenshu_list:
        if '入院记录' in wenshu['文书名']:
            if '既往史' in wenshu['内容']:
                past_history = wenshu['内容']['既往史']
                break
        if '新入院评估单' == wenshu['文书名']:
            if '一、基本信息' in wenshu['内容']:
                start_index = wenshu['内容']['一、基本信息'].find('特殊既往史')
                end_index = wenshu['内容']['一、基本信息'].find('既往不安全事件发生史')
                if start_index != -1 and end_index != -1:
                    past_history += "\t" + wenshu['内容']['一、基本信息'][start_index:end_index].strip()


    print("past_history:", past_history)  # 打印既往史内容

    # 处理每个既往史条目
    for history_item in past_history.strip().split("。"):
        history_item = history_item.strip()  # 去掉前后空格

        if '；' in history_item or '，' in history_item:
            sub_items = history_item.replace('；', '，').split('，')
        else:
            sub_items = [history_item]

        for sub_item in sub_items:
            sub_item = sub_item.strip()  # 去掉前后空格

            if '否认' not in sub_item and sub_item:  # 确保不是空字符串
                print("sub_item:", sub_item)  # 打印每个分割后的条目

                if '；' in sub_item:
                    final_items = sub_item.split('；')
                else:
                    final_items = [sub_item]

                for final_item in final_items:
                    final_item = final_item.strip()  # 去掉前后空格

                    if '否认' not in final_item and final_item:  # 确保不是空字符串
                        print("final_item:", final_item)  # 打印每个最终分割后的条目

                        # 按逗号或顿号分割条目
                        disease_sentences = final_item.replace('、', '，').split('，')
                        for sentence in disease_sentences:
                            sentence = sentence.strip()
                            if sentence:
                                # 在suifang_keshi_dict中匹配对应的科室
                                for key, value in suifang_keshi_dict.items():
                                    if key in sentence:
                                        if value not in result_jiwangshi_suifang:
                                            result_jiwangshi_suifang[value] = []
                                        result_jiwangshi_suifang[value].append(sentence)
                                        break

    print('--'*70)
    output_list = []
    for keshi, diseases in result_jiwangshi_suifang.items():
        unique_diseases = list(set(diseases))  # 去重
        output_list.append(f"患者{'；'.join(unique_diseases)}，建议{keshi}随访")

    final_output = "；".join(output_list)

    # 如果结果为空，处理传染病史
    if not final_output:
        for history_item in past_history.strip().split("。"):
            if '传染病史' in history_item:
                start_index = past_history.find('传染病史')
                end_index = past_history.find('。', start_index)
                infectious_disease_history = past_history[start_index:end_index].strip()
                print("infectious_disease_history:", infectious_disease_history)  # 打印传染病史内容

                disease_sentences = infectious_disease_history.split("，")
                for sentence in disease_sentences:
                    sentence = sentence.strip()
                    if sentence:
                        # 在suifang_keshi_dict中匹配对应的科室
                        for key, value in suifang_keshi_dict.items():
                            if key in sentence:
                                if value not in result_jiwangshi_suifang:
                                    result_jiwangshi_suifang[value] = []
                                result_jiwangshi_suifang[value].append(sentence)
                                break

        output_list = []
        for keshi, diseases in result_jiwangshi_suifang.items():
            unique_diseases = list(set(diseases))  # 去重
            output_list.append(f"患者{'；'.join(unique_diseases)}，建议{keshi}随访")

        final_output = "；".join(output_list)

    if final_output:
        final_output += "。"

    print(f"患者慢性病病史及建议的随访科室如下：{final_output}")






         
    #print(past_history)

    # # 矫正出院时间
    # if ori_datas['患者基本信息']['出院时间'] == '无法判断':
    #     ori_datas['患者基本信息']['出院时间'] = ori_source['患者基本信息'].split('医嘱时间:')[1].split('\n')[0]

    # # 住院期间医疗情况 = 简化过滤检验 + 全部检查
    # ori_datas['住院期间医疗情况'] = ori_source['住院期间医疗情况'].split('###简化过滤检验')[1].split('###')[0] + ori_source['住院期间医疗情况'].split('###全部检查')[1].split('###')[0]

    


    # # if ori_source['体检摘要'].split('\n')[5] != '':
    # #     ori_datas['体检摘要'] = ori_source['体检摘要'].split('\n')[5].split(":")[1]
    
    # # 矫正体征数据
    # tz_info = "" 
    # for info in ori_source['患者基本信息'].split('###'):
    #     if '体温' in info:
    #         tz_info = info
    #         break

    # T, P, R, BP_H, BP_L = extract_data_2(info)   
    # if T!="" and P!="" and R !="" and BP_H !="" and BP_L !="": 
    #     ori_datas['患者基本信息']['体温(T)'] = T
    #     ori_datas['患者基本信息']['脉搏(P)'] = P
    #     ori_datas['患者基本信息']['呼吸(R)'] = R
    #     ori_datas['患者基本信息']['高压(BP高)'] = BP_H
    #     ori_datas['患者基本信息']['低压(BP低)'] = BP_L
    

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


def postprocess(key_id,keshi,read_dir = '全部由模型生成',out_dir = '全部由模型生成', data_dir='全部由模型生成'):
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
        update_formats_with_ori_data(zylsh,keshi,processed_data,data_output, data_output_source)
            
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
