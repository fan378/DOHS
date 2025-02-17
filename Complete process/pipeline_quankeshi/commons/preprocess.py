import sys
from .utils import *
import pandas as pd
from tqdm import tqdm
import re
from bs4 import BeautifulSoup,Tag
import bs4
import json
from copy import deepcopy
from collections import defaultdict
from xml.etree import ElementTree as ET
import time

# 通用函数，删除冗余空格
def process_duplicate_space(text):
    text = text.replace('\r','')
    text = text.replace('　','')
    text = text.strip()
    text = re.sub(r'(\n)+','\n',text)
    text  = re.sub(' +',' ',text)
    return text

# 处理病理
def process_bingli(value,columns = []):
    value = list(value)
    # 处理id
    ori_text = value[3]
    processed_text = process_duplicate_space(ori_text)
    value[3] = processed_text
    operate_time = value[8]
    if operate_time == '1900-01-01 00:00:00':
        value[8] = ''

    zylsh = value[0]
    report_time = value[9]

    # 使用zip和字典推导式合并两个列表
    ignore_keys = ['住院流水号']
    dict_value = {k: v for k, v in zip(columns, value)}
    res_text = ''
    for key,value in dict_value.items():
        if key in ignore_keys or value == '':
            continue
        res_text = res_text + '{}:{}\n\n'.format(key,value)
    json_text = {
        '报告时间':report_time,
        '内容':res_text.strip()
    }
    return zylsh,report_time,dict_value,json_text


def get_bingli(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    start_time = time.time()
    # 病理的列名
    print('处理病理记录')
    columns = ['住院流水号','临床诊断','病理类型','病理诊断结果','镜下所见','肉眼所见','免疫组化','报告内容','检查时间','报告时间']
    datas = load_excel_csv(data_dir)
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)
    print('数据大小:{}'.format(datas.shape))
    datas.fillna('',inplace=True)

    # 保留一个住院流水号的所有病理信息
    json_obj = []
    # 保留一个住院流水号的所有病理(文本)信息
    json_obj_text = []
    now_zylsh = datas.iat[0,0]
    # 返回的csv的当前行
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:
            # 遇到了一个新的流水号，排序，并赋值
            sorted_json_obj = sorted(json_obj, key=lambda x: x['报告时间'])
            sorted_json_obj_text = sorted(json_obj_text, key=lambda x: x['报告时间'])
            res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            now_res_index += 1
            json_obj = []
            json_obj_text = []
            now_zylsh = zylsh

        zylsh,report_time,value,json_text =  process_bingli(datas.iloc[i,:],columns=columns)    
        # processed_datas.loc[i] = [zylsh,report_time,json.dumps(value,ensure_ascii=False)]

        json_obj.append(value)
        json_obj_text.append(json_text)
    # 最后一个，处理一下
    sorted_json_obj = sorted(json_obj, key=lambda x: x['报告时间'])
    sorted_json_obj_text = sorted(json_obj_text, key=lambda x: x['报告时间'])
    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-start_time))
    return res_data



def process_xml(data,process_type=0):
    # str转xml
    xml_data = ET.XML(data)
    if process_type == 0:
        try:
            xml_data.remove(xml_data.find('高血压科出院小结'))
            xml_data.remove(xml_data.find('内分泌科出院小结'))
        except:
            pass

    elif process_type == 1:
        try:
            xml_data.remove(xml_data.find('内分泌科出院小结'))
        except:
            pass

    elif process_type == 2:
        try:
            xml_data.remove(xml_data.find('高血压科出院小结'))
        except:
            pass

    # xml转json
    return ET.tostring(xml_data, encoding="utf-8").decode("utf-8"),xml2json(xml_data,process_type)

# process_type=0 都不要
# process_type=1 保留高血压
# process_type=2 保留内分泌
def xml2json(node,process_type=0):
    if not isinstance(node, ET.Element):
        raise Exception("node format error.")

    if len(node) == 0:
        return node.tag, node.text

    data = {}
    temp = None
    for child in node:
        key, val = xml2json(child)
        if val == None:
            val = ""
        if '签名' in key:
            continue
        if process_type == 0:
            if '高血压科出院小结' == key or '内分泌科出院小结' == key:
                continue
        elif process_type == 1:
            if '高血压科出院小结' == key:
                continue
        elif process_type == 2:
            if '内分泌科出院小结' == key:
                continue
        if '预设' in key and '|' in val:
            if 'True' in val:
                data['内容'] = data.get('内容','') + val.split('|')[-1] + '；'
            continue
        if val != None and '|' in val:
            val = val.split('|')[0]
        if key in data:
            if type(data[key]) == list:
                data[key].append(val)
            else:
                temp = data[key]
                data[key] = [temp, val]
        else:
            data[key] = val

    return node.tag, data

def process_weiji(data):
    finds = re.findall('<BodyText>(.*?)</BodyText>',data)
    if len(finds) == 1:
        text = finds[0]
        text = process_duplicate_space(text)
    else:
        text = ""
    return text
    
def process_vte(data):
    text = re.findall('<BodyText>(.*?)</BodyText>',data)[0]
    index_1 = text.find('外科住院患者院内VTE预防的推荐意见')
    index_2 = text.find('骨科大手术患者院内VTE预防的推荐意见')
    if index_1 != -1 and index_2 != -1:
        text = process_duplicate_space(text[index_1:index_2])
    return text

def get_hulijilu(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    '''
    '恶性肿瘤报告卡',                  正常
    '死亡病例报告卡',                  正常
    '特殊抗菌药物使用专家审核表',       正常
    '临床输血申请单',                  正常
    '死亡病例讨论本',                  正常
    '手术护理记录单',                  正常(处理一下术后注意事项，有预设和True False)
    '出院小结(死亡小结)',              正常(处理一下高血压等信息)
    '住院病案首页2012版',              正常(字段是拼音，用不到？)
    '危急值处理记录',                  不正常
    '住院患者VTE',                     不正常
    '危重病历讨论本'                   正常
    '''
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    xml_text_data = pd.DataFrame(columns=[0,1])
    start_time = time.time()
    print('处理护理记录')
    datas = load_excel_csv(data_dir)
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    print(datas.shape)
    datas.fillna('',inplace=True)
    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)

    json_obj = []
    json_obj_text = []
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    xml_index = 0
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:
            sorted_json_obj = sorted(json_obj, key=lambda x: x['时间'])
            sorted_json_obj_text = sorted(json_obj_text, key=lambda x: x['时间'])
            res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            now_res_index += 1
            json_obj = []
            json_obj_text = []
            now_zylsh = zylsh
        item_time = datas.iat[i,3]
        lrrq = datas.iat[i,4]
        zhxgrq = datas.iat[i,5]
        text_name = datas.iat[i,2]
        if text_name == '':
            continue
        if text_name == '危急值处理记录':
            value = process_weiji(datas.iat[i,1])
            res_text = value
        elif text_name == '住院患者VTE':
            value = process_vte(datas.iat[i,1])
            res_text = value
        else:
            try:
                clean_xml,(value_name,value) =  process_xml(datas.iat[i,1])    
                res_text = json_to_text(value)
                xml_text_data.loc[xml_index] = [clean_xml,'护理记录名:{}\n内容:{}'.format(text_name,res_text)]
                xml_index += 1
            except:
                value = datas.iat[i,1]
                res_text = 'error'

        # datas.iat[i,1] = json.dumps(value,ensure_ascii=False)
        if res_text != 'error':
            # 住院流水号
            json_obj.append({
                '护理记录名':text_name,
                '时间':item_time,
                '录入日期':lrrq,
                '最后修改日期':zhxgrq,
                '内容':value
                })
            json_obj_text.append({
                '护理记录名':text_name,
                '时间':item_time,
                '录入日期':lrrq,
                '最后修改日期':zhxgrq,
                '内容':res_text
                })
    # 最后一个 处理一下
    sorted_json_obj = sorted(json_obj, key=lambda x: x['时间'])
    sorted_json_obj_text = sorted(json_obj_text, key=lambda x: x['时间'])
    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-start_time))
    return res_data, xml_text_data

def process_jiancha(value, columns = []):
    value = list(value)
    ori_time = value[8]
    if ori_time == '1900-01-01 00:00:00':
        value[8] = ''
    ori_time = value[9]
    if ori_time == '1900-01-01 00:00:00':
        value[9] = ''
    ori_time = value[10]
    if ori_time == '1900-01-01 00:00:00':
        value[10] = ''
    # 处理id
    ori_text = value[5]
    processed_text = process_duplicate_space(ori_text)
    value[5] = processed_text
    ori_text = value[6]
    processed_text = process_duplicate_space(ori_text)
    value[6] = processed_text

    zylsh = value[0]
    request_time = value[8]

    # 使用zip和字典推导式合并两个列表
    dict_value = {k: v for k, v in zip(columns, value)}
    ignore_keys = ['住院流水号']
    res_text = ''
    for key,value in dict_value.items():
        if key in ignore_keys or value == '':
            continue
        res_text = res_text + '{}:{}\n\n'.format(key,value)
    json_text = {
        '报告时间':request_time,
        '内容':res_text.strip()
    }
    return zylsh,request_time,dict_value,json_text

# 处理检查
def get_jiancha(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    start_time = time.time()
    # 病理的列名
    print('处理病理记录')
    columns = ['住院流水号','检查ID','检查类型','检查部位','检查子类型','图像所见','图像分析','检查描述','申请时间','检查时间','报告时间']
    datas = load_excel_csv(data_dir)
    ###############################################################################
    # yc添加
    if datas.empty:
        return res_data
    ###############################################################################
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)
    print(datas.shape)
    datas.fillna('',inplace=True)
    
    processed_datas = pd.DataFrame(columns=[0,1,2])
    json_obj = []
    json_obj_text = []
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:
            # 遇到了一个新的流水号，排序，并赋值
            sorted_json_obj = sorted(json_obj, key=lambda x: (x['报告时间'],x['检查时间']))
            sorted_json_obj_text = sorted(json_obj_text, key=lambda x: (x['报告时间']))
            res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            now_res_index += 1
            json_obj = []
            json_obj_text = []
            now_zylsh = zylsh

        zylsh,report_time,value,json_text =  process_jiancha(datas.iloc[i,:],columns = columns)    
        # processed_datas.loc[i] = [zylsh,report_time,json.dumps(value,ensure_ascii=False)]

        json_obj.append(value)
        json_obj_text.append(json_text)


    sorted_json_obj = sorted(json_obj, key=lambda x: (x['报告时间'],x['检查时间']))
    sorted_json_obj_text = sorted(json_obj_text, key=lambda x: (x['报告时间']))
    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-start_time))
    return res_data

def process_zhenduan(value, columns = []):
    value = list(value)
    zylsh = value[0]
    diag_time = value[3]
    # 使用zip和字典推导式合并两个列表
    dict_value = {k: v for k, v in zip(columns, value)}
    ignore_keys = ['住院流水号','ICD10编码','诊断编号','院内诊断编码']
    res_text = ''
    for key,value in dict_value.items():
        if key in ignore_keys or value == '':
            continue
        res_text = res_text + '{}:{}\n\n'.format(key,value)
    json_text = {
        '诊断时间':diag_time,
        '内容':res_text.strip()
    }
    return zylsh,dict_value,json_text

# 处理诊断
def get_zhenduan(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    start_time = time.time()
    # 病理的列名
    print('处理诊断')
    columns = ['住院流水号','ICD10编码','诊断编号','诊断时间','诊断名称','诊断类型','院内诊断编码']
    datas = load_excel_csv(data_dir,columns=7)
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)
    print(datas.shape)
    datas.fillna('',inplace=True)
    
    processed_datas = pd.DataFrame(columns=[0,1,2])
    json_obj = []
    json_obj_text = []
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:
            # 遇到了一个新的流水号，排序，并赋值
            sorted_json_obj = sorted(json_obj, key=lambda x: (x['诊断时间']))
            sorted_json_obj_text = sorted(json_obj_text, key=lambda x: (x['诊断时间']))
            try:
                res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            except:
                print('error at zylsh:{}'.format(now_zylsh))
                print('sorted_json_obj:{}'.format(sorted_json_obj))
                print('sorted_json_obj_text:{}'.format(sorted_json_obj_text))
            now_res_index += 1
            json_obj = []
            json_obj_text = []
            now_zylsh = zylsh

        zylsh,value,json_text =  process_zhenduan(datas.iloc[i,:],columns = columns)    
        # processed_datas.loc[i] = [zylsh,report_time,json.dumps(value,ensure_ascii=False)]

        json_obj.append(value)
        json_obj_text.append(json_text)


    sorted_json_obj = sorted(json_obj, key=lambda x: (x['诊断时间']))
    sorted_json_obj_text = sorted(json_obj_text, key=lambda x: (x['诊断时间']))
    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-start_time))
    return res_data

def process_tizheng(value, columns = []):
    value = list(value)
    zylsh = value[0]
    diag_time = value[1]
    # 使用zip和字典推导式合并两个列表
    dict_value = {k: v for k, v in zip(columns, value)}
    merge_val = ''
    for key in ['检测值_1','检测值_2','检测值_3']:
        if dict_value[key] == '0.000':
            continue
        merge_val = merge_val + '{}/'.format(dict_value[key])
    dict_value['检测值'] = merge_val.strip('/')
    for key in ['检测值_1','检测值_2','检测值_3']:
        dict_value.pop(key)

    merge_text = ''
    for key in ['说明_1','说明_2']:
        if dict_value[key] == '':
            continue
        merge_text = merge_text + '{}；'.format(dict_value[key])
    dict_value['说明'] = merge_text
    for key in ['说明_1','说明_2']:
        dict_value.pop(key)

    res_text = ''
    for key,value in dict_value.items():
        res_text = res_text + '{}:{}\n\n'.format(key,value)
    json_text = {
        '记录时间':diag_time,
        '内容':res_text.strip()
    }
    return zylsh,dict_value,json_text

# 处理体征
def get_tizheng(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    start_time = time.time()
    # 病理的列名
    print('处理体征')
    columns = ['住院流水号','记录时间','检测项','检测值_1','检测值_2','检测值_3','说明_1','说明_2','单位']
    datas = load_excel_csv(data_dir,columns=9)
    ###############################################################################
    # yc添加
    if datas.empty:
        return res_data
    ###############################################################################
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)
    print(datas.shape)
    datas.fillna('',inplace=True)
    
    processed_datas = pd.DataFrame(columns=[0,1,2])
    json_obj = []
    json_obj_text = []
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:
            # 遇到了一个新的流水号，排序，并赋值
            sorted_json_obj = sorted(json_obj, key=lambda x: (x['记录时间']))
            sorted_json_obj_text = sorted(json_obj_text, key=lambda x: (x['记录时间']))
            try:
                res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            except:
                print('error at zylsh:{}'.format(now_zylsh))
                print('sorted_json_obj:{}'.format(sorted_json_obj))
                print('sorted_json_obj_text:{}'.format(sorted_json_obj_text))
            now_res_index += 1
            json_obj = []
            json_obj_text = []
            now_zylsh = zylsh

        zylsh,value,json_text =  process_tizheng(datas.iloc[i,:],columns = columns)    
        # processed_datas.loc[i] = [zylsh,report_time,json.dumps(value,ensure_ascii=False)]

        json_obj.append(value)
        json_obj_text.append(json_text)


    sorted_json_obj = sorted(json_obj, key=lambda x: (x['记录时间']))
    sorted_json_obj_text = sorted(json_obj_text, key=lambda x: (x['记录时间']))
    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-start_time))
    return res_data

# 处理检验
def process_jianyan(value,columns=[]):
    value = list(value)
    ori_time = value[8]
    if ori_time == '1900-01-01 00:00:00':
        value[8] = ''
    ori_time = value[9]
    if ori_time == '1900-01-01 00:00:00':
        value[9] = ''
    ori_time = value[10]
    if ori_time == '1900-01-01 00:00:00':
        value[10] = ''
    # 处理id
    jianyan_id = value[1]
    # 返回 流水号，id，时间
    zylsh = value[0]
    request_time = value[8]

    # 使用zip和字典推导式合并两个列表
    dict_value = {k: v for k, v in zip(columns, value)}
    ignore_keys = ['住院流水号']
    res_text = ''
    for key,value in dict_value.items():
        if key in ignore_keys or value == '':
            continue
        res_text = res_text + '{}:{}\n\n'.format(key,value)
    json_text = {
        '报告时间':request_time,
        '检验ID':jianyan_id,
        '内容':res_text.strip()
    }
    return zylsh,jianyan_id,request_time,dict_value,json_text

def get_jianyan(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    process_start_time = time.time()
    print('处理检验')
    columns = ['住院流水号','检验ID','检验指标','检验结果','检测值','单位','上限','下限','申请时间','检验时间','报告时间']
    datas = load_excel_csv(data_dir)
    ###############################################################################
    # yc添加
    if datas.empty:
        return res_data
    ###############################################################################
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    print(datas.shape)
    datas.fillna('',inplace=True)
    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)
    
    processed_datas = pd.DataFrame(columns=[0,1,2])
    json_obj = defaultdict(list)
    json_obj_text = defaultdict(list)
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:

            all_data = list(json_obj.values())
            # 使用lambda函数将数据按照医嘱时间排序
            sorted_data = sorted(all_data, key=lambda x: x[0]['报告时间']+x[0]['检验ID'])
            # 插入新数据
            sorted_json_obj = []
            for data in sorted_data:
                sorted_json_obj.append({
                    '检验id':data[0]['检验ID'],
                    '报告时间':data[0]['报告时间'],
                    '检验详情':data,
                })
            all_data = list(json_obj_text.values())
            # 使用lambda函数将数据按照医嘱时间排序
            sorted_data = sorted(all_data, key=lambda x: x[0]['报告时间']+x[0]['检验ID'])
            # 插入新数据
            sorted_json_obj_text = []
            for data in sorted_data:
                sorted_json_obj_text.append({
                    '检验id':data[0]['检验ID'],
                    '报告时间':data[0]['报告时间'],
                    '检验详情':data,
                })

            res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            now_res_index += 1
            json_obj = defaultdict(list)
            json_obj_text = defaultdict(list)
            now_zylsh = zylsh

        zylsh,jianyan_id,start_time,value,json_text =  process_jianyan(datas.iloc[i,:],columns=columns)   
        if '' in value['检测值'] or '' in value['检验指标']:
            continue
        # processed_datas.loc[i] = [zylsh,jianyan_id,json.dumps(value,ensure_ascii=False)]
        # 住院流水号
        json_obj[jianyan_id].append(value)
        json_obj_text[jianyan_id].append(json_text)
    all_data = list(json_obj.values())
    # 使用lambda函数将数据按照医嘱时间排序
    sorted_data = sorted(all_data, key=lambda x: x[0]['报告时间']+x[0]['检验ID'])
    # 插入新数据
    sorted_json_obj = []
    for data in sorted_data:
        sorted_json_obj.append({
            '检验id':data[0]['检验ID'],
            '报告时间':data[0]['报告时间'],
            '检验详情':data,
        })
    all_data = list(json_obj_text.values())
    # 使用lambda函数将数据按照医嘱时间排序
    sorted_data = sorted(all_data, key=lambda x: x[0]['报告时间']+x[0]['检验ID'])
    # 插入新数据
    sorted_json_obj_text = []
    for data in sorted_data:
        sorted_json_obj_text.append({
            '检验id':data[0]['检验ID'],
            '报告时间':data[0]['报告时间'],
            '检验详情':data,
        })

    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-process_start_time))
    return res_data
    
# 处理文书
# 替换\table
re_table_label = re.compile(r'\</TABLE\>')
# 替换table
re_table_label_2 = re.compile(r'\<TABLE.*?\>')
# 替换 \td
re_td_label = re.compile(r'\</TD\>')
# 替换td
re_td_label_2 = re.compile(r'\<TD.*?\>')
# 有的table中，缺少key后面的冒号，查找table以补上
re_table_content = re.compile(r'\{TABLE\}.*?\{/TABLE\}')
re_td_content = re.compile(r'\{TD\}.*?\{/TD\}')
re_replace_td_content = re.compile(r'\{TD\} *([^ ]*?) *\{/TD\} *\{TD\} *([^ ]*?) *\{/TD\}')
re_replace_table_content = re.compile(r'\{TABLE\} *([^ ]*?) *\{/TABLE\}')
re_html_label = re.compile(r'\<.*?\>')

re_nbsp_content = re.compile(r'(\>[\u4e00-\u9fa5]+)(&nbsp;| )+([\u4e00-\u9fa5]+:)')
def process_duplicate_key_wenshu(json_obj,key):
    if key not in json_obj.keys():
        return key
    index = 1
    tmp_key = key+'_'+str(index)
    while tmp_key in json_obj.keys():
        index += 1
        tmp_key = key+'_'+str(index)
    return tmp_key
def process_table_content(text,re_table_content,re_td_content,re_replace_td_content,re_replace_table_content,index=-1):
    # 查找table与\table
    replaces = []
    for table_content in re_table_content.findall(text):
        processed_teble_content = re_html_label.sub('',table_content).strip()
        flag = 1
        td_contents = re_td_content.findall(processed_teble_content)
        if len(td_contents) == 0:
            if ':' in processed_teble_content:
                flag = 0
            else:
                flag = 2
        else:
            for td_content in td_contents:
                if ':' in td_content:
                    flag=0
                    break
        # 有TD并且缺乏冒号
        if flag == 1:
            correct_content = re_replace_td_content.sub(r'{TD}\1:{/TD}{TD}\2 {/TD}',processed_teble_content)
            replaces.append((table_content,correct_content))
            # correct_content = re_replace_td_content.sub(r'{TD}<span>thisisasplitseparator\1:{/key}</span>{/TD}{TD}<span>\2 </span>{/TD}',processed_teble_content)
            # replaces.append((table_content,correct_content))
        # 没有TD(只有TABLE)并且缺乏冒号
        elif flag == 2:
            correct_content = re_replace_table_content.sub(r'{TABLE}\1:{/TABLE}',processed_teble_content)
            # correct_content = re_replace_table_content.sub(r'{TABLE}<span>thisisasplitseparator\1:{/key}</span>{/TABLE}',processed_teble_content)
            replaces.append((table_content,correct_content))
    if len(replaces) != 0:
        pass
        # print(index)
    for table_content,correct_content in replaces:
        # print('BEFORE:{}'.format(table_content))
        # print('AFTER:{}'.format(correct_content))
        # print()
        text = text.replace(table_content,correct_content)
    text = text.replace('{TD}','<TD>').replace('{/TD}','</TD>').replace('{TABLE}','<TABLE>').replace('{/TABLE}','</TABLE>')
    return text
def process_duplicate_space_wenshu(value,br=True):
    value = re.sub(r'-{10,}','',value)
    value = re.sub(r'_{8,}','_____',value)
    value = re.sub(r' *\{BRBR\} *','{BRBR}',value)
    value = re.sub(r'(\{BRBR\})+','{BRBR}',value)
    value = value.strip()
    value = value.strip('{BRBR}')
    value = value.strip()
    value = re.sub(' +',' ',value)
    if br:
        value = value.replace('{BRBR}','\n')
    else:
        value = value.replace('{BRBR}','{BR}')
    value = re.sub(r'([:，。！？；]) *[:，。！？；]',r'\1',value)
    return value
def process_html(i,html_source):
    html_source = re.sub('<INPUT.*?>','<INPUT>',html_source)
    html_source = html_source.replace('：',':')
    # 处理一下特殊情况
    finds = re.findall('<BODY>[^<>]*?<BR>',html_source)
    if len(finds) == 0 or '。' not in finds[0]:
        html_source = re.sub(
            r'(([\u4e00-\u9fa5]|:)+)(<|&)+',   # 正则中的模式字符串
            r"\1{/key}\3",      # 替换的字符串，也可为一个函数 # 在匹配的汉字后面添加符号
            html_source,    # 要被查找替换的原始字符串
            count = 1  # 模式匹配后替换的最大次数，默认 0 表示替换所有的匹配
        )
    else:
        html_source = re.sub(
            r'<BODY>([^<>]*?<BR>)',   # 正则中的模式字符串
            r"<BODY>文本:{/key}\1",      # 替换的字符串，也可为一个函数 # 在匹配的汉字后面添加符号
            html_source,    # 要被查找替换的原始字符串
            count = 1  # 模式匹配后替换的最大次数，默认 0 表示替换所有的匹配
        )

    html_source = re_nbsp_content.sub(r'\1\3',html_source)


    html_source = re.sub(
        "(&nbsp;)+",   # 正则中的模式字符串
        " ",      # 替换的字符串，也可为一个函数
        html_source,    # 要被查找替换的原始字符串
        count = 0  # 模式匹配后替换的最大次数，默认 0 表示替换所有的匹配
    )

    ################################################################
    # TABLE处理
    html_source = re_td_label.sub('{/TD}',html_source).strip()
    html_source = re_td_label_2.sub('{TD}',html_source).strip()
    # 再替换<table>
    html_source = re_table_label.sub('{/TABLE}',html_source).strip()
    html_source = re_table_label_2.sub('{TABLE}',html_source).strip()
    html_source = process_table_content(html_source,re_table_content,re_td_content,re_replace_td_content,re_replace_table_content)
    ################################################################
    
    # 解析HTML源码
    soup = BeautifulSoup(html_source, 'html.parser')
    soup = soup.find('body')

    if not isinstance(soup, Tag):
        print('当前位置i为:{}\nsoup类型不正确:{}'.format(i,type(soup)))
        print('html内容为:{}'.format(html_source))
        return [None,None,None]

    remove_obj = []
    for tag in list(soup.descendants):
        if tag.name == 'tbody' and ('签名' in tag.text or '签字' in tag.text):
            remove_obj.append(tag)
    for tag in remove_obj:
        tag.extract()

        
    div_list = soup.find_all('div',recursive=False)
    if len(div_list) != 0:
        for div in div_list[:]:
            if div.text.strip():
                # div.insert_before('thisisasplitseparator')
                div_span_list = div.select('span[token="label"]:not(table span[token="label"])')
                for div_span in div_span_list:
                    if div_span.text.strip():
                        div_span.insert_before('thisisasplitseparator')
                        div_span.insert_after('{/key}')
                # _ = [(div_span.insert_before('thisisasplitseparator') and div_span.insert_after('{/key}')) for div_span in div_span_list if div_span.text.strip() ]
                # div.insert_after('{/key}')
    else:
        # 遍历所有<span>标签
        span_list = soup.find_all('span',attrs={'token': 'label'}) + soup.find_all('SPAN',attrs={'token': 'label'})
        for span in span_list[:]:
            # 检查<span>标签是否包含'token'属性且属性值为'label'
            if span.has_attr('token') and span['token'] == 'label':
                # 在该标签后面添加换行符
                if span.text.strip():
                    span.insert_before('thisisasplitseparator')
                    span.insert_after('{/key}')

    br_list = soup.find_all('BR') + soup.find_all('br')
    for BR in br_list:
        BR.insert_after('{BRBR}')

    # print(soup)
    soup_text = re.sub(
        "( )+",   # 正则中的模式字符串
        " ",      # 替换的字符串，也可为一个函数
        soup.text,    # 要被查找替换的原始字符串
        count = 0  # 模式匹配后替换的最大次数，默认 0 表示替换所有的匹配
    )
    soup_text = re.sub(
        "({/key} *)+",   # 正则中的模式字符串
        "{/key}",      # 替换的字符串，也可为一个函数
        soup.text,    # 要被查找替换的原始字符串
        count = 0  # 模式匹配后替换的最大次数，默认 0 表示替换所有的匹配
    )
    soup_text = soup_text.strip('{BRBR}')
    soup_text = soup_text.strip('{/key}')
    soup_text = soup_text.strip()
    soup_text = soup_text.strip('thisisasplitseparator')
    soup_list = soup_text.split('thisisasplitseparator')
    json_obj = {}
    res_text = ''
    for item in soup_list:
        item = item.strip('{BRBR}')
        item = item.strip('{/key}')
        if "{/key}" in item:  # 检查是否存在换行符
            if len(item.split("{/key}")) != 2:
                print('error at :{}'.format(i))
                print(item)
                continue
            json_key, value = item.split("{/key}")  # 如果存在，进行分割
            json_key = json_key.replace('{BRBR}','').strip()
            if json_key[-1] == ':':
                json_key = json_key[:-1]
            value_text = process_duplicate_space_wenshu(value,False)
            value = process_duplicate_space_wenshu(value)
            # 文本
            res_text = res_text + ' ' + json_key + ':' + value_text 
            # json对象
            json_key = process_duplicate_key_wenshu(json_obj,json_key)
            json_obj[json_key] = value
        else:
            item = process_duplicate_space_wenshu(item,False)
            res_text = res_text+item+' '
    res_text = process_duplicate_space_wenshu(res_text,False)
    return soup_list,json_obj, res_text
def get_wenshu(data_dir:str,data_type=1,data_nums = 2000,patient_nums = 20):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    html_text_data = pd.DataFrame(columns=[0,1])
    start_time = time.time()
    print('处理文书')
    datas = load_excel_csv(data_dir)
    if data_type == 0:
        patient_zylsh = list(set(datas[0]))[:patient_nums]
        print('筛选的住院流水号:{}'.format(patient_zylsh))
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    else:
        patient_zylsh = []
    print(datas.shape)

    datas = datas.sort_values(by=[0],ascending=[False])
    datas = datas.reset_index(drop=True)
    datas.fillna('',inplace=True)
    # datas_text = deepcopy(datas)
    json_obj = []
    json_obj_text = []
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:
            sorted_json_obj = sorted(json_obj, key=lambda x: x['时间'])
            sorted_json_obj_text = sorted(json_obj_text, key=lambda x: x['时间'])
            res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            now_res_index += 1
            json_obj = []
            json_obj_text = []
            now_zylsh = zylsh

        item_time = datas.iat[i,3].split('.')[0]
        text_name = datas.iat[i,2]
        soup_list,final_json, res_text =  process_html(i,datas.iat[i,1])
        if final_json == None:
            continue
        html_text_data.loc[i] = [datas.iat[i,1],'文书名:{}\n内容:{}'.format(text_name,res_text)]
        # final_text = '{/value}'.join(soup_list)
        # datas.iat[i,1] = '{split}'.join(process_html(datas.iat[i,1]))
        
        # datas.iat[i,1] = final_text
        # datas_text.iat[i,1] = res_text
        id = datas.iat[i,0]
        text_name = datas.iat[i,2]
        json_obj.append({
            '文书名':text_name,
            '时间':item_time,
            '内容':final_json,
        })
        json_obj_text.append({
            '文书名':text_name,
            '时间':item_time,
            '内容':res_text
        })
    # 最后一个 处理一下
    sorted_json_obj = sorted(json_obj, key=lambda x: x['时间'])
    sorted_json_obj_text = sorted(json_obj_text, key=lambda x: x['时间'])
    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-start_time))
    return res_data, html_text_data, patient_zylsh

# 处理医嘱
def process_yizhu(value,id_idx,columns=[]):
    value = list(value)
    # 处理id
    ori_id = value[id_idx]
    processed_id = ori_id.split('|')[0]
    value[id_idx] = processed_id
    # 处理结束时间
    end_time = value[5]
    if end_time == '1900-01-01 00:00:00':
        value[5] = ''
    # 如果某个医嘱 xxxx 跳过

    # 返回 流水号，id，时间
    zylsh = value[0]
    value[3] = value[3].split('.')[0]
    start_time = value[3]

    # 使用zip和字典推导式合并两个列表
    dict_value = {k: v for k, v in zip(columns, value)}
    ignore_keys = ['住院流水号']
    res_text = ''
    for key,value in dict_value.items():
        if key in ignore_keys or value == '':
            continue
        res_text = res_text + '{}:{}\n\n'.format(key,value)
    json_text = {
        '医嘱时间':start_time,
        '医嘱ID':processed_id,
        '内容':res_text.strip()
    }
    return zylsh,processed_id,start_time,dict_value,json_text
def get_yizhu(data_dir:str,data_type=1,data_nums = 2000,patient_zylsh = []):
    res_data = pd.DataFrame(columns=['zylsh','结构化数据','非结构化数据'])
    process_start_time = time.time()
    print('处理医嘱')
    columns = ['住院流水号','医嘱类型名称','医嘱类型','医嘱时间','状态','停止时间','医嘱ID','医嘱项类别','医嘱项名称','医嘱项规格','单次剂量数量','单次给药数量','给药途径','给药频次']
    id_idx = columns.index('医嘱ID')
    datas = load_excel_csv(data_dir)
    if data_type == 0:
        mask = datas[0].isin(patient_zylsh)
        datas = datas[mask]
    print(datas.shape)
    datas.fillna('',inplace=True)
    datas = datas.sort_values(by=[0,id_idx],ascending=[False,True])
    datas = datas.reset_index(drop=True)
    
    processed_datas = pd.DataFrame(columns=[0,1,2])
    json_obj = defaultdict(list)
    json_obj_text = defaultdict(list)
    now_zylsh = datas.iat[0,0]
    now_res_index = 0 
    for i in tqdm(range(datas.shape[0])):
        zylsh = datas.iat[i,0]
        # 检查当前流水号
        if zylsh != now_zylsh:

            all_data = list(json_obj.values())
            # 使用lambda函数将数据按照医嘱时间排序
            sorted_data = sorted(all_data, key=lambda x: x[0]['医嘱时间']+x[0]['医嘱ID'])
            # 插入新数据
            sorted_json_obj = []
            for data in sorted_data:
                sorted_json_obj.append({
                    '医嘱id':data[0]['医嘱ID'],
                    '医嘱时间':data[0]['医嘱时间'],
                    '医嘱详情':data,
                })
            all_data = list(json_obj_text.values())
            # 使用lambda函数将数据按照医嘱时间排序
            sorted_data = sorted(all_data, key=lambda x: x[0]['医嘱时间']+x[0]['医嘱ID'])
            # 插入新数据
            sorted_json_obj_text = []
            for data in sorted_data:
                sorted_json_obj_text.append({
                    '医嘱id':data[0]['医嘱ID'],
                    '医嘱时间':data[0]['医嘱时间'],
                    '医嘱详情':data,
                })

            res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
            now_res_index += 1
            json_obj = defaultdict(list)
            json_obj_text = defaultdict(list)
            now_zylsh = zylsh

        zylsh,processed_id,start_time,value,json_text =  process_yizhu(datas.iloc[i,:],id_idx=id_idx,columns=columns)    
        # processed_datas.loc[i] = [zylsh,processed_id,json.dumps(value,ensure_ascii=False)]
        # 住院流水号
        json_obj[processed_id].append(value)
        json_obj_text[processed_id].append(json_text)
    all_data = list(json_obj.values())
    # 使用lambda函数将数据按照医嘱时间排序
    sorted_data = sorted(all_data, key=lambda x: x[0]['医嘱时间']+x[0]['医嘱ID'])
    # 插入新数据
    sorted_json_obj = []
    for data in sorted_data:
        sorted_json_obj.append({
            '医嘱id':data[0]['医嘱ID'],
            '医嘱时间':data[0]['医嘱时间'],
            '医嘱详情':data,
        })
    all_data = list(json_obj_text.values())
    # 使用lambda函数将数据按照医嘱时间排序
    sorted_data = sorted(all_data, key=lambda x: x[0]['医嘱时间']+x[0]['医嘱ID'])
    # 插入新数据
    sorted_json_obj_text = []
    for data in sorted_data:
        sorted_json_obj_text.append({
            '医嘱id':data[0]['医嘱ID'],
            '医嘱时间':data[0]['医嘱时间'],
            '医嘱详情':data,
        })

    res_data.loc[now_res_index] = [now_zylsh,json.dumps(sorted_json_obj,ensure_ascii=False),json.dumps(sorted_json_obj_text,ensure_ascii=False)]
    print('处理结束')
    print('花费:{}秒'.format(time.time()-process_start_time))
    return res_data
