import sys
sys.path.append('../../')
from commons.utils import *
from commons.preprocess import *
from commons.constants import *
from tqdm import tqdm
import re
from bs4 import BeautifulSoup,Tag
import bs4
from copy import deepcopy
from collections import defaultdict
import pandas as pd
import json
import jsonlines
from datetime import timedelta,datetime
import random
from tqdm import tqdm
from transformers import AutoTokenizer
from copy import deepcopy
# 一些预定义的/人工定义的数据

all_data_maps = {}


'''
注意
1. 病理判断的时候，使用最后修改日期，如果病理的报告时间在最后修改日期之后，那就mask掉
'''

tips = {
    'detail':[
        '请以标准的json格式输出，并包含{detail_keys}这些字段。',
        '输出应符合标准的json格式，包含字段{detail_keys}。',
        '请按照标准json格式输出，并且包含字段{detail_keys}。',
        '确保输出遵循标准的json格式，包括字段{detail_keys}。',
        '以标准的json格式进行输出，并且包含字段{detail_keys}。',
        '输出应为标准json格式，字段为{detail_keys}。',
        '请确保输出遵守标准json格式，并包含字段{detail_keys}。',
        '输出要求为标准json格式，包含字段{detail_keys}。',
        '按照标准json格式输出并包含字段{detail_keys}。',
        '输出标准json格式数据，请包含字段{detail_keys}。',
        '使用标准的json格式进行输出，确保包含字段{detail_keys}。',
    ],
    'normal':[
        '请以文本格式输出。',
        '输出应为一段文本。',
        '请按标准的文本格式输出。',
        '确保输出为一段文本。',
        '使用文本格式输出。',
    ]
}

key_desps = {
    '患者基本信息':[
        '从所给的输入信息中，抽取所需要的字段内容。',
        '分析提供的字符串，识别并提取出所需字段内容。',
        '读取输入文本，识别所需的特定字段信息。',
        '对给定文本进行处理，抽取所需的关键字段',
        '解析输入数据，提取所需的字段信息',
    ],
    '住院期间医疗情况':[
        '从输入中识别并选择该患者住院期间的关键检验检查信息，具体报告内容不用进行摘要和修改。',
        '分析患者住院期间的全部检查和检验记录，提取其中关键的检验和检查信息，不要修改具体的报告描述和内容。',
        '对患者的检查和检验信息进行综合分析，选取并展示关键的检验和检查信息，详细的报告内容和描述不要修改。',
        '从患者的检查和检验记录中，抽取出关键的检查和检验信息，并保持报告的详细内容和描述不进行修改。',
    ],
    '出院诊断':[
        '分析患者的诊断和病程记录，输出患者的出院诊断，名称应为标准诊断术语，若有相关的描述信息，在括号内注明。',
        '分析患者的诊断和病程记录，输出出院诊断信息，确保使用标准诊断术语，若需要注明相关的描述信息，在括号内说明。',
        '综合患者的诊断及病情信息，确定标准的诊断术语作为出院诊断，并在诊断名称旁用括号注释额外的描述信息。',
        '分析患者的病程和诊断资料，确定其出院时的标准诊断名称，并在括号内附加详细的描述信息。',
        '对患者的诊断和病情进行综合评估，明确标准的出院诊断名称，并在该诊断旁用括号插入重要的描述信息。',
    ],
    '病程与治疗情况':[
        '综合分析患者的医疗记录，包括手术、化疗、报告和当前情况等，以一段文本总结患者住院期间的整体治疗进展。',
        '从提供的医疗信息中，详细梳理并总结患者在住院期间接受的所有治疗措施，包括手术、化疗、报告及当前情况等。',
        '分析患者的住院病历，提取并概述其在住院期间经历的治疗过程，如手术、化疗、报告和当前情况等。',
        '处理并总结患者在住院期间的病程信息，关注手术、化疗、报告以及和当前情况等关键治疗环节。',
        '对患者的住院病程数据进行分析，集中呈现其在医院期间接受的主要治疗方式，包括手术、化疗、报告及当前情况等信息。',
    ],
    '出院时情况':[
        '分析患者的病历文书，总结其在出院时的健康状况，可以包括精神状态、伤口愈合情况及其他相关健康指标。',
        '从患者病历中提取关键信息，以明确其出院时的总体健康情况，如精神状况、身体恢复情况等。',
        '综合患者的病历信息，描述其出院时的健康状态，包括精神清晰度、伤口愈合程度及其他重要健康指标。',
        '从患者的医疗记录中分析并总结出院时的健康状况，如精神状态、伤口恢复、整体健康情况等信息。',
    ],
    '出院后用药建议':[
        '以编号列表格式呈现结果，每项建议前标注数字序号，如“1.”, “2.”, “3.”等，以清晰区分不同的建议项。',
        '建议以有序列表形式组织输出内容，每条建议前应添加序号，例如‘1.’, ‘2.’, ‘3.’等，以便于阅读和理解各项指示。',
        '输出结果应以数字化的清单形式展示，每条用药建议前标明数字编号，如‘1.’, ‘2.’, ‘3.’，确保信息条理清晰。',
        '出院用药建议应按照数字列表的格式进行编排，每项均以一个新的数字序号开始，如‘1.’, ‘2.’, ‘3.’，以此类推。',
        '为了清楚展示该字段，应以逐条编号的格式呈现，例如用‘1.’, ‘2.’, ‘3.’等数字明确标出每一项建议。',
    ],
}

def replace_space(text):
    '''
    去除多余空格
    '''
    text = str(text)
    text = text.replace('\n',' ')
    text = text.replace('\r',' ')
    text = re.sub(' +',' ',text)
    return text.strip()

# 把医嘱转为字符串类型
def transfer_yizhu_to_str(data):
    columns = ['医嘱时间','医嘱类型名称','医嘱类型','医嘱项类别','医嘱项名称','医嘱项规格','单次剂量数量','单次给药数量','给药途径','给药频次']
    res_str = ''
    key = '医嘱时间'
    res_str = res_str + '{}:{}\n'.format(key,replace_space(data[key]))
    for detail in data['医嘱详情']:
        for need_key in columns:
            if need_key in detail.keys() and detail[need_key] != '':
                res_str = res_str + '{}:{}\t'.format(need_key,replace_space(detail[need_key]))
    return res_str.strip()

def transfer_chuyuandaiyao_yizhu_to_str(data):
    '''
    把出院带药医嘱转为字符串类型，因为出院带药医嘱里面很多都是一样的，所以删掉了"医嘱类型","医嘱项类别"
    '''
    columns = ['医嘱时间','医嘱类型名称','医嘱项名称','医嘱项规格','单次剂量数量','单次给药数量','给药途径','给药频次']
    res_str = ''
    key = '医嘱时间'
    res_str = res_str + '{}:{}\n'.format(key,replace_space(data[key]))
    for detail in data['医嘱详情']:
        for need_key in columns:
            if need_key in detail.keys() and detail[need_key] != '':
                res_str = res_str + '{}:{}\t'.format(need_key,replace_space(detail[need_key]))
    return res_str.strip()


# 拿到三类医嘱（出院带药；常规；出院医嘱）
def get_chuyuandaiyao(yizhu_list):
    chuyuandaiyao_list = []
    not_chuyuandaiyao_list = []
    chuyuanyizhu_list = []
    for data in yizhu_list:
        # 检查一下
        data_item = data['医嘱详情'][0]
        if '出院' in data_item['医嘱项名称']:
            # 第一个是出院，那就是出院医嘱
            chuyuanyizhu_list.append(data)
        elif data_item['医嘱类型'] == '出院带药':
            # 第一个是出院带药，那就全部是出院带药，经过自动化分析
            chuyuandaiyao_list.append(data)
        else:
            not_chuyuandaiyao_list.append(data)
    return chuyuandaiyao_list,not_chuyuandaiyao_list,chuyuanyizhu_list


# 把检查转为字符串类型
def transfer_jiancha_to_str(data):
    # 全部的
    columns = ['检查ID','报告时间','检查类型','检查部位','检查描述','检查子类型','图像所见','图像分析']
    # 太多了 筛选
    data['描述'] = data['检查类型'].strip() + '|' + data['检查部位'].strip() + '|' + data['检查子类型'].strip() + '|' + data['检查描述']
    columns = ['检查ID','报告时间','描述','图像所见','图像分析']
    res_str = ''
    for need_key in columns:
        if need_key in data.keys() and data[need_key] != '':
            res_str = res_str + '{}:{}\n'.format(need_key,replace_space(data[need_key]))
    return res_str.strip()


# 只保留部分的字段
def transfer_masked_jiancha_to_str(data):
    # 太多了 筛选
    data['描述'] = data['检查类型'].strip() + '|' + data['检查部位'].strip() + '|' + data['检查子类型'].strip() + '|' + data['检查描述']
    columns = ['检查ID','检查时间','描述']
    res_str = ''
    for need_key in columns:
        if need_key in data.keys() and data[need_key] != '':
            res_str = res_str + '{}:{}\n'.format(need_key,replace_space(data[need_key]))
    return res_str.strip()


# 把检验转为字符串
def transfer_jianyan_to_str(data):
    columns = ['检验指标','检测值','单位','检验结果','下限','上限','单位']
    res_str = '报告时间:{}\n检验详情:'.format(data['检验详情'][0]['报告时间'])
    for jianyan_item in data['检验详情']:
        res_str = res_str + '{}:{}{},{}({}—{}{});\t'.format(*tuple([replace_space(jianyan_item[k]) for k in columns]))
    return res_str.strip()


# 把病理转为字符串
def transfer_bingli_to_str(data):
    columns = ['检查时间','报告时间','临床诊断','病理类型','病理诊断结果','病理报告结果','镜下所见','肉眼所见','免疫组化','报告内容']
    res_str = ''
    for need_key in columns:
        if need_key in data.keys() and data[need_key] != '':
            res_str = res_str + '{}:{}\n'.format(need_key,replace_space(data[need_key]))
    return res_str.strip()


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

# 拿到并分类检查
def get_jiancha_list(jiancha_list,discharge_time):
    '''
    拿到三类检查: 正确的检查、出院时没出的检查、随访检查
    '''
    true_jiancha_list = []
    masked_jiancha_list = []
    suifang_jiancha_list = []
    for index,jiancha in enumerate(jiancha_list):
        try:
            report_time = jiancha['报告时间'].split(' ')[0]
            report_time = datetime.strptime(report_time, "%Y-%m-%d")
            if report_time > discharge_time:
                jiancha['报告时间'] = ""
                jiancha['图像所见'] = ""
                jiancha['图像分析'] = ""
                masked_jiancha_list.append(jiancha)
            else:
                true_jiancha_list.append(jiancha)
                if '随访'  in jiancha['图像分析'] or '随诊' in jiancha['图像分析']:
                    suifang_jiancha_list.append(jiancha)
        except:
                true_jiancha_list.append(jiancha)
                if '随访' in jiancha['图像分析'] or '随诊' in jiancha['图像分析']:
                    suifang_jiancha_list.append(jiancha)
    return true_jiancha_list,masked_jiancha_list,suifang_jiancha_list

# 拿到未出的病理
def get_weichu_bingli_list(bingli_list,discharge_time):
    '''
    返回 正常病理、未出病理
    '''
    discharge_time = datetime.strptime(discharge_time, "%Y-%m-%d")
    masked_bingli_list = []
    true_bingli_list = []
    skip_bingli_list = []
    columns = ['检查时间','临床诊断','病理类型']
    for index,bingli in enumerate(bingli_list):
        try:
            report_time = bingli['报告时间'].split(' ')[0]
            report_time = datetime.strptime(report_time, "%Y-%m-%d")
            if report_time > discharge_time:
                # 如果时间差超过30天
                if (report_time - discharge_time).days >= 30:
                    skip_bingli_list.append(bingli)
                    # print('时间超过30天，跳过这个病理')
                    continue
                # print('找到未出的病理')
                processed_bingli = {}
                for need_key in columns:
                    if need_key in bingli.keys() and bingli[need_key] != '':
                        processed_bingli[need_key] = bingli[need_key]
                masked_bingli_list.append(processed_bingli)
                # print('加入未出病理:{}'.format(processed_bingli))
            else:
                true_bingli_list.append(bingli)
        except Exception as e:
            # print('加入未出病理时错误:{}'.format(e))
            # print('bingli:{}'.format(bingli))
            true_bingli_list.append(bingli)
    return true_bingli_list ,masked_bingli_list, skip_bingli_list

# 未出的病理_转字符串
def transfer_weichu_bingli_to_str(data):
    columns = ['检查时间','临床诊断','病理类型']
    res_str = ''
    for need_key in columns:
        if need_key in data.keys() and data[need_key] != '':
            res_str = res_str + '{}:{}\n'.format(need_key,replace_space(data[need_key]))
    return res_str.strip()

def get_last_pinggu(wenshu_list):
    '''
    得到最后一个在院评估单
    '''
    res = None
    for wenshu in wenshu_list:
        if wenshu['文书名'] == '在院评估单':
            res = wenshu
    return res

def process_jianyan(data):
    '''
    因为原文本太长了，缩短一点
    '''
    maps = {
        '结果在参考范围之内':'正常',
        '超出了参考范围上限':'偏高',
        '超出了参考范围下限':'偏低'
    }
    for jianyan in data:
        for jianyan_item in jianyan['检验详情']:
            if jianyan_item['检验结果'] in maps.keys():
                jianyan_item['检验结果'] = maps[jianyan_item['检验结果']]

# 处理一下异常检验，只要指标、值和结果
def transfer_yichang_jianyan_to_str(data):
    columns = ['检验指标','检测值','单位','检验结果']
    res_str = '报告时间:{}\n检验详情:'.format(data['检验详情'][0]['报告时间'])
    for jianyan_item in data['异常检验详情']:
        res_str = res_str + '{}:{}{},{};\t'.format(*tuple([replace_space(jianyan_item[k]) for k in columns]))
    return res_str.strip()

# 处理一下诊断数据
def transfer_zhenduan_to_str(data):
    columns = ['诊断时间','诊断编号','诊断类型','诊断名称']
    res_str = ''
    for need_key in columns:
       if need_key in data.keys() and data[need_key] != '':
            res_str = res_str + '{}:{}\n'.format(need_key,replace_space(data[need_key]))
    return res_str.strip()

# 文书转str
def transfer_wenshu_to_str(data,keys):
    head_str = ''
    # 一定需要的字段
    normal_columns = ['文书名','时间']
    data['时间'] = data['时间'].split(' ')[0]
    head_str = head_str + '###{}:\n'.format(data['文书名'])
    head_str = head_str + '{}:{}\n'.format('时间',data['时间'])
    # keys为内容中的子字段
    detail = data['内容']
    content_str = ''
    for col in keys:
        if detail[col] != '':
            content_str = content_str + '{}:{}\n'.format(col,replace_space(detail[col]))
    head_str = head_str.strip()
    content_str = content_str.strip()
    if content_str == '':
        return ''
    else:
        res_str = head_str + '\n' + content_str
        return res_str.strip()


# 拿到异常检验
def get_yichang_jianyan(jianyan_list):
    '''
    拿到异常检验，保持结构不变，以“异常检验详情字段”展现
    '''
    items_dict = {}
    # 单个检验
    for jianyan in jianyan_list:
        # 检验项
        yichang_items = []
        for jianyan_item in jianyan['检验详情']:
            if jianyan_item['检验结果'] == '偏高' or jianyan_item['检验结果'] == '偏低' or '阳性' in jianyan_item['检验结果'] or '阳性' in jianyan_item['检测值'] or '未判断' in jianyan_item['检验结果']:
                yichang_items.append(jianyan_item)
        jianyan['异常检验详情'] = yichang_items

def get_fujian(wenshu_list):
    '''
    得到日常病程中的辅检
    '''
    res = []
    for wenshu in wenshu_list:
        if '记录' in wenshu['文书名']:
            keys = list(wenshu['内容'].keys())
            try:
                if len(keys) == 1 and ('辅检' in wenshu['内容'][keys[0]] or '入院后相关检查' in wenshu['内容'][keys[0]]):
                    res.append(wenshu)
            except:
                pass
    return res

import re

def check_date_format(date_str):
    """
    Check if the date string matches the format YYYY-MM-DD HH:MM:SS or YYYY-MM-DD.

    Args:
    date_str (str): The date string to check.

    Returns:
    bool: True if the date matches one of the formats, otherwise False.
    """
    format_1 = '%Y年%m月%d日 %H时%M分'
    format_2 = '%Y.%m.%d %H:%M'
    format_3 = '%Y-%m-%d %H:%M'
    format_4 = '%Y-%m-%d %H:%M:%S'
    formats = [format_1,format_2,format_3,format_4]

    for time_format in formats:
        try:
            return datetime.strptime(date_str, time_format).strftime('%Y-%m-%d %H:%M'),True
        except:
            pass
    return '',False

def build_data(ori_index,ori_data,data_maps,data_lengths,keshi):
    global keep_nums,delete_nums
    res_data = []
    xiaojie = {}
    # -----------------------Step1：拿取数据并预处理，时间分割并且删掉空值或无关字段-----------------------
    zylsh = ori_data.iat[0]
    # 病理
    # 预处理
    bingli_list = process_bingli_for_ins(ori_data.iat[1])
    ori_data.iat[1] = bingli_list
    # 医嘱
    yizhu_list = ori_data.iat[3]
    # 把删除状态的医嘱去掉
    yizhu_list = process_yizhu_for_ins(yizhu_list)
    ori_data.iat[3] = yizhu_list
    # 文书
    wenshu_list = ori_data.iat[5]
    # 删掉无用字段 如 最后修改时间......
    wenshu_list = process_wenshu_for_ins(wenshu_list)
    ori_data.iat[5] = wenshu_list
    # 护理记录
    hulijilu_list = ori_data.iat[7]
    # 检查
    jiancha_list = ori_data.iat[9]
    # 检验
    jianyan_list = ori_data.iat[11]
    process_jianyan(jianyan_list)
    # 诊断
    zhenduan_list = ori_data.iat[13]
    # 把诊断的时间裁剪到天
    zhenduan_list = process_zhenduan_for_ins(zhenduan_list)
    ori_data.iat[13] = zhenduan_list
    # 出院小结，摊平
    for data in hulijilu_list:
        if data['护理记录名'] == '出院小结(死亡小结)':
            flatten_dict(data, xiaojie, parent_key=data['护理记录名'])
            break
    # 可能拿不到出院小结，直接return None
    if xiaojie == {}:
        return None
    # -----------------------Step1 Finish-----------------------
    # -----------------------Step2 出院小结中 摊平后会出现字段重复，比如姓名、性别等，处理一下，防止出现list导致格式问题 出入院时间单独做----------------------
    # 解决一下相同字段名导致的list问题(入出院时间单独做)
    # 最后修改日期
    last_update_time = xiaojie['出院小结(死亡小结)---最后修改日期']
    last_update_time = last_update_time.split(' ')[0]

    #######
    # 用哪个数据筛选未出的检查/检验
    report_check_time = last_update_time
    #######
    flag = False
    for xiaojie_k,xiaojie_v in xiaojie.items():
        if xiaojie_k in ['出院小结(死亡小结)---入院时间','出院小结(死亡小结)---出院时间']:
            continue
        if isinstance(xiaojie_v,list):
            if len(set(xiaojie_v)) != 1:
                # print('error at index:{} key:{}'.format(ori_index,xiaojie_k))
                flag = True
            elif len(xiaojie_v) == 0:
                # print('empty at index:{} key:{}'.format(ori_index,xiaojie_k))
                flag = True
            else:
                xiaojie[xiaojie_k] = xiaojie_v[0]
    if flag:
        return None
    ######
    # 入出院时间简单处理一下
    ######
    # 入院，直接分割取到天数

    '''
    出院时间分为两个：出院小结中的(用于输出)，真实的(用于未出病理、检查、检验的mask)
    入院时间只有一个，判断病理等，直接用出院小结中的即可，虽然可能有几天的误差
    时间转为以天为单位
    ** 出院时间返回4个值**
    1: (出院小结，出院记录)
    2: 最终返回的出院时间
    3: 医嘱是否正常
    4: 数据是否正常

    ** 入院时间返回3个值 **
    1: 文书中的入院时间
    2: 小结中的入院时间
    3: 能否找到
    '''

    (time_cyxj, wenshu_time_out), chuyuan_time, res_chuyuan, data_is_normal = find_chuyuan_time(ori_index,ori_data)
    wenshu_time_in, ruyuan_time, ruyuan_find = find_ruyuan_time(ori_index,ori_data)

    # if ruyuan_find:
    #     xiaojie['出院小结(死亡小结)---入院时间'] = ruyuan_time
    # else:
    #     xiaojie['出院小结(死亡小结)---入院时间'] = "无法判断"

    # if res_chuyuan:
    #     xiaojie['出院小结(死亡小结)---出院时间'] = chuyuan_time
    #     if data_is_normal:
    #         # 检查一下 如果数据正常 出院时间不是9999
    #         if chuyuan_time.startswith('9999'):
    #             pass
    #             # print('ori_index:{} 出院时间错误 9999'.format(ori_index))
    # else:
    #     xiaojie['出院小结(死亡小结)---出院时间'] = "无法判断"
    # -----------------------Step2 Finish-----------------------
    # -----------------------Step3 处理一下24小时文书中不需要的字段-----------------------
    # 24小时中，会把出院的信息也放在里面，要删掉
    drop_keys = ['诊疗经过','出院情况','出院诊断','出院医嘱','健康宣教']
    for index,data in enumerate(wenshu_list):
        if wenshu_is_24(data):
            data_keys = data['内容'].keys()
            for drop_key in drop_keys:
                if drop_key in data_keys:
                    data['内容'].pop(drop_key)
                else:
                    pass
                    # print('index:{} 住院流水号:{} 文书为:{} 没找到需要删掉的字段:{} 所有字段:{}'.format(ori_index,zylsh,data['文书名'],drop_key,data_keys))
            # 出院时间删掉
            try:
                data['内容']['姓名'] = data['内容']['姓名'][:data['内容']['姓名'].index('出院时间')].strip()
            except:
                pass
                # print('index:{} 住院流水号:{}\t24小时中无法删除出院时间:{}'.format(ori_index,zylsh,data['内容']))
    # -----------------------Step3 Finish-----------------------
    # -----------------------Step4 构造一些常量-----------------------
    # 把出院前没出结果的检查和检验mask掉，防止影响"住院期间医疗情况"字段
    # 处理检查类型(正常，未出，随访)
    jiancha_list,weichujieguo_jiancha_list,suifang_jiancha_list = get_jiancha_list(jiancha_list,report_check_time)
    if len(weichujieguo_jiancha_list) > 0:
        pass
        # print('index:{} 住院流水号:{} 出院时间得到为:{} 删除了检查'.format(ori_index,zylsh,report_check_time))

    # # 处理检验，没出的直接删掉
    # flag = False
    # new_jianyan_list = []
    # # print('没出的检验筛选开始')
    # for index,jianyan in enumerate(jianyan_list):
    #     report_time = jianyan['报告时间'].split(' ')[0]
    #     try:
    #         report_time = datetime.strptime(report_time, "%Y-%m-%d").strftime('%Y-%m-%d')
    #         if report_time > chuyuan_time:
    #             flag = True
    #             continue
    #         else:
    #             new_jianyan_list.append(jianyan)
    #     except:
    #         print('index:{} 住院流水号:{} 检验时间转换错误:{}'.format(ori_index,zylsh,report_time))
    #         new_jianyan_list.append(jianyan)
    # # print('没出的检验筛选完毕')
    # jianyan_list = new_jianyan_list
    # if flag:
    #     print('index:{} 住院流水号:{} 出院时间得到为:{} 删除了检验'.format(ori_index,zylsh,chuyuan_time))

    # 先拿到常量
    # 常量总共有 [科室类别,全部诊断,病理报告,既往史,出院带药,出院医嘱,检查,未出检查结果报告,全部检查,检验,异常检验指标,未出结果病理报告]

    # ||科室类别||
    constants = {}
    constants['科室类别'] = cons_chinese_keshis[keshi]

    # ||全部诊断||
    zhenduan_str = ''
    for zhenduan in zhenduan_list:
        zhenduan_str = zhenduan_str + '\n\n' + transfer_zhenduan_to_str(zhenduan)
    zhenduan_str = zhenduan_str.strip()
    if zhenduan_str == '':
        zhenduan_str = '无'
    constants['全部诊断'] = zhenduan_str

    # ||既往史||
    find_jiwang = False
    for data in wenshu_list:
        if '入院记录' in data['文书名'] and not wenshu_is_24(data):
            try:
                if data['内容']['既往史'].strip() != '':
                    constants['既往史'] = replace_space(data['内容']['既往史'])
                    find_jiwang = True
            except:
                pass
                # print('入院记录查找既往史错误,wenshu:{}'.format(data))
    if not find_jiwang:
        for data in wenshu_list:
            if '新入院评估单' in data['文书名']:
                try:
                    text = data['内容']['一、基本信息']
                    constants['既往史'] = replace_space(text[text.index('特殊既往史'):])
                except:
                    pass
                    # print('入院评估但中查找既往史错误,wenshu:{}'.format(data))
    if '既往史' not in constants.keys():
        # print('当前数据index:{} 无法找到既往史'.format(ori_index))
        constants['既往史'] = '无'

    # 拿到三类型医嘱：[出院带药；常规；出院医嘱]
    chuyuandaiyao_list,no_chuyuandaiyao_list,chuyuanyizhu_list = get_chuyuandaiyao(yizhu_list)
    # ||出院带药||
    chuyuandaiyao_str = ''
    for data in chuyuandaiyao_list:
        chuyuandaiyao_str = chuyuandaiyao_str.strip() + '\n\n' + transfer_chuyuandaiyao_yizhu_to_str(data)
    chuyuandaiyao_str = chuyuandaiyao_str.strip()
    if chuyuandaiyao_str == '':
        chuyuandaiyao_str = '无'
    constants['出院带药'] = chuyuandaiyao_str

    # ||常规医嘱||
    changguiyizhu_str = ''
    for data in no_chuyuandaiyao_list:
        changguiyizhu_str = changguiyizhu_str.strip() + '\n\n' + transfer_yizhu_to_str(data)
    changguiyizhu_str = changguiyizhu_str.strip()
    if changguiyizhu_str == '':
        changguiyizhu_str = '无'
    constants['常规医嘱'] = changguiyizhu_str

    # ||出院医嘱||
    chuyuanyizhu_str = ''
    for data in chuyuanyizhu_list:
        chuyuanyizhu_str = chuyuanyizhu_str.strip() + '\n\n' + transfer_yizhu_to_str(data)
    chuyuanyizhu_str = chuyuanyizhu_str.strip()
    if chuyuanyizhu_str == '':
        chuyuanyizhu_str = '无'
    constants['出院医嘱'] = chuyuanyizhu_str.strip()

    # ||检查||
    jiancha_str = ''
    for data in jiancha_list:
        jiancha_str = jiancha_str.strip() + '\n\n' + transfer_jiancha_to_str(data)
    jiancha_str = jiancha_str.strip()
    if jiancha_str == '':
        jiancha_str = '无'
    constants['检查'] = jiancha_str

    # ||未出检查结果报告||
    weichujieguo_jiancha_str = ''
    for data in weichujieguo_jiancha_list:
        weichujieguo_jiancha_str = weichujieguo_jiancha_str.strip() + '\n\n' + transfer_masked_jiancha_to_str(data)
    if weichujieguo_jiancha_str == '':
        weichujieguo_jiancha_str = '无'
    if weichujieguo_jiancha_str != '无':
        pass
        # print('zylsh:{}\tkeshi:{}\t存在未出检查结果报告'.format(zylsh,keshi))
    constants['未出检查结果报告'] = weichujieguo_jiancha_str

    # ||全部检查|| ****因为异常的无法判断全，所以全部丢进去，最早计划找出异常的检查(存在随访/随诊)，减少输入长度****
    suifang_jiancha_str = ''
    # for data in suifang_jiancha_list:
    for data in jiancha_list:
        suifang_jiancha_str = suifang_jiancha_str.strip() + '\n\n' + transfer_jiancha_to_str(data)
    if suifang_jiancha_str == '':
        suifang_jiancha_str = '无'
    constants['全部检查'] = suifang_jiancha_str

    # ||日常病程辅检||
    fujian_list = get_fujian(wenshu_list)
    # print('辅检个数:{}'.format(len(fujian_list)))
    fujian_str = ''
    for fujian in fujian_list:
        fujian_str = fujian_str.strip() + '\n\n' + transfer_wenshu_to_str(fujian,fujian['内容'].keys()).strip()
    if fujian_str == '':
        fujian_str = '无'
    constants['日常病程辅检'] = fujian_str.strip()


    # ||检验||
    jianyan_str = ''
    for data in jianyan_list:
        jianyan_str = jianyan_str.strip() + '\n\n' + transfer_jianyan_to_str(data)
    if jianyan_str == '':
        jianyan_str = '无'
    constants['检验'] = jianyan_str.strip()

    # ||异常检验指标||
    get_yichang_jianyan(jianyan_list)
    yichang_jianyan_str = ''
    for data in jianyan_list:
        if len(data['异常检验详情']) == 0:
            # 如果没有异常检验
            continue
        yichang_jianyan_str = yichang_jianyan_str.strip() + '\n\n' + transfer_yichang_jianyan_to_str(data)
    if yichang_jianyan_str == '':
        yichang_jianyan_str = '无'
    constants['异常检验指标'] = yichang_jianyan_str
    # print('zylsh:{}'.format(zylsh))
    bingli_list, weichu_bingli_list, skip_bingli_list = get_weichu_bingli_list(bingli_list,last_update_time)
    # print('病理数量:{}\t未出病理数量:{}\t跳过的病理数量:{}'.format(len(bingli_list),len(weichu_bingli_list),len(skip_bingli_list)))
    # ||病理报告||
    bingli_str = ''
    for data in bingli_list:
        bingli_str = bingli_str.strip() + '\n\n' + transfer_bingli_to_str(data)
    if bingli_str == '':
        bingli_str = '无'
    constants['病理报告'] = bingli_str
    # ||未出结果病理报告||
    weichu_bingli_str = ''
    for data in weichu_bingli_list:
        weichu_bingli_str = weichu_bingli_str.strip() + '\n\n' + transfer_weichu_bingli_to_str(data)
    if weichu_bingli_str == '':
        weichu_bingli_str = '无'
    constants['未出结果病理报告'] = weichu_bingli_str

    # ||最后一日查房/病程记录||
    shuhou_last = None
    for wenshu_index,wenshu in enumerate(wenshu_list):
        if '术后第' in wenshu['文书名'] or '查房记录' in wenshu['文书名'] or '日常病程' in wenshu['文书名']:
            shuhou_last = wenshu_index
    
    # ||最后一个在院评估单||
    last_pinggu = get_last_pinggu(wenshu_list)
    if last_pinggu == None:
        last_pinggu_str = '无'
    else:
        last_pinggu_str = transfer_wenshu_to_str(last_pinggu,last_pinggu['内容'].keys()).strip()
    constants['最后一个在院评估单'] = last_pinggu_str
    # print('最后一个在院评估单:{}'.format(const/ants['最后一个在院评估单']))

    # -----------------------Step4 Finish-----------------------
    # -----------------------Step5 构造数据-----------------------
    # 一些文书数据单独处理下
    for wenshu in wenshu_list:
        # 特殊的情况单独处理下
        if '入院告知书' in wenshu['文书名']:
            try:
                wenshu['内容']['患者信息'] = wenshu['内容']['患者信息'][:wenshu['内容']['患者信息'].index('为了保障')]
            except:
                pass
        if '告未成年患者监护人书' in wenshu['文书名']:
            try:
                wenshu['内容']['患者信息'] = wenshu['内容']['患者信息'][:wenshu['内容']['患者信息'].index('为了保障')]
            except:
                pass
        if '入院记录' in wenshu['文书名']:
            try:
                wenshu['内容']['主治医师48小时诊断'] = wenshu['内容']['主治医师48小时诊断'][:wenshu['内容']['主治医师48小时诊断'].index('本人对于患方提供')].strip()
            except:
                pass
    # 构造数据
    for key,value in data_maps.items():
        if key == '医嘱介绍':
            continue
        # 如果数据不正确且key是"基本信息"->跳过
        if key == '患者基本信息' and data_is_normal == False:
            continue
        # 输出是一个json(基本信息字段)或者一段文本(其他字段)
        data_output = {}
        # 要输出的出院小结字段
        out_maps = value['output_keys']
        # 人工分析的来源模板
        source_keys = value['source_keys']
        # ***********************取输出***********************
        # 先设置为json
        for out_key,out_value in out_maps.items():
            if out_value.startswith('cons_'):
                out_value = out_value.replace('cons_','')
                out_value = constants[out_value]
            else:
                out_value = '出院小结(死亡小结)---'+out_value
                out_value = xiaojie[out_value]
            if '---' in out_key:
                parent_key,out_key = out_key.split('---')
                if parent_key not in data_output:
                    data_output[parent_key] = {}
                data_output[parent_key][out_key] = out_value
            else:
                data_output[out_key] = out_value
        # ***********************FINISH***********************
        # ***********************取输入***********************
        # 1. 先拿到文书
        wenshu_sources = source_keys['文书']
        processed_wenshu_sources = defaultdict(list)
        # 先处理一下文书
        # 处理后的 processed_wenshu_sources 格式为
        # {入院告知书:[患者信息、体格检查.....]......}
        for wenshu_source in wenshu_sources:
            if '---' in wenshu_source:
                wenshu_name,wenshu_key = wenshu_source.split('---')
                processed_wenshu_sources[wenshu_name].append(wenshu_key)
            else:
                wenshu_name = wenshu_source
                # assert wenshu_name not in processed_wenshu_sources.keys(),print('来源文书已存在')
                if wenshu_name in processed_wenshu_sources:
                    pass
                    # print('来源文书已存在:{}'.format(wenshu_name))
                    # print('processed_wenshu_sources:{}'.format(processed_wenshu_sources))
                processed_wenshu_sources[wenshu_name].append('ALL_KEYS')
        for tmp_key in processed_wenshu_sources.keys():
            if 'ALL_KEYS' in processed_wenshu_sources[tmp_key]:
                processed_wenshu_sources[tmp_key] = []
        # 拿取文书的字符串
        wenshu_str = ''
        # 遍历文书
        # 加入的文书下标
        exists = []
        # 需要的文书
        need_wenshus = processed_wenshu_sources.keys()
        for wenshu_index,wenshu in enumerate(wenshu_list):
            # 如果是最后一次查房/病程记录，直接单独判断
            if shuhou_last != None and wenshu_index == shuhou_last and '最后一日查房/病程记录' in need_wenshus:
                common_keys = list(wenshu['内容'].keys())
                tmp_wenshu_str = transfer_wenshu_to_str(wenshu,common_keys).strip()
                # 加入str中
                wenshu_str = wenshu_str.strip() + '\n\n' + tmp_wenshu_str
                continue

            # 如果是24，模板里写的是''
            if wenshu_is_24(wenshu):
                pipei_name = '24小时内入出院记录'
            # 如果不是24，正常按模板的匹配
            else:
                pipei_name = wenshu['文书名']

            all_common_keys = []
            # 因为不是完全匹配，遍历来源文书
            for search_wenshu in need_wenshus:
                if search_wenshu in pipei_name:
                    exists.append(wenshu_index)
                    # 加入字段
                    set_keys = set(processed_wenshu_sources[search_wenshu])
                    if len(set_keys) == 0:
                        common_keys = list(wenshu['内容'].keys())
                    else:
                        common_keys = [element for element in wenshu['内容'].keys() if element in set_keys]
                    for common_key in common_keys:
                        if common_key not in all_common_keys:
                            all_common_keys.append(common_key)
            # 当前文书的str
            if len(all_common_keys) == 0:
                continue
            tmp_wenshu_str = transfer_wenshu_to_str(wenshu,all_common_keys).strip()
            # 加入str中
            wenshu_str = wenshu_str.strip() + '\n\n' + tmp_wenshu_str
        wenshu_str = wenshu_str.strip()

        # 2. 再根据来源取值(常量+文书)
        all_sources = source_keys['字段']
        input_str = ''
        for source_key in all_sources:
            # 两种情况(文书 正常)
            if source_key == '文书':
                input_str = input_str.strip() + '\n\n' + wenshu_str
            else:
                input_str = input_str.strip() + '\n\n' + '###{}:\n{}'.format(source_key,constants[source_key])
        input_str = input_str.strip()

        # ***********************FINISH***********************
        if len(out_maps.keys()) != 1:
            # 存在子字段，需要告诉模型
            tip = random.choice(tips['detail'])
            out_maps_str = transfer_choices_to_str(out_maps)
            tip = tip.replace('{detail_keys}',out_maps_str)
            data_output = json.dumps(data_output,ensure_ascii=False,indent=2)
        else:
            # 只有一个字段，那就不需要告诉模型输出的详细字段
            tip = random.choice(tips['normal'])
            # 转为文本
            data_output = data_output[key]
            data_output = re.sub(' +',' ',data_output)
        # ***********************取指令***********************
        data_ins = random.choice(instructions)
        key_desp = random.choice(key_desps[key])
        data_ins = data_ins.replace('{key}','“{}”'.format(key))
        data_ins = data_ins.replace('{tip}',tip)
        data_ins = data_ins.replace('\\n','\n')
        data_ins = data_ins.replace('{input}',input_str)
        data_output = re.sub('(\n)+','\n',data_output)
        # 如果是内分泌科，出院时情况字段，额外判断处理下
        if keshi == 'neifenmi' and key == '出院时情况':
            data_output = filter_text_and_keep_delimiters(data_output)
        # 加入字段描述
        data_ins = data_ins.strip() + '\n字段介绍:{}'.format(key_desp)
        # 如果是 出院后用药建议 加入撰写建议
        if key == '出院后用药建议':
            data_ins = data_ins + '\n撰写建议:{}'.format(data_maps['医嘱介绍'])
            
        # ***********************FINISH***********************
        tmp_data = {
            'instruction':data_ins.strip(),
            'input':'',
            'output':data_output,
            'zylsh':zylsh,
            'key':key
        }

        res_data.append(tmp_data)

    # -----------------------Step5 Finish-----------------------
    return res_data
# 乳腺外科
ruxianwaike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','日常查房记录','日常病程记录','手术记录单','术后首次病程记录','术后第一日记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','既往史','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院告知书---患者信息','查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','入院告知书---患者信息','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请先检查患者报告是否出齐；针对患者的出院带药进行描述；随后，阐述患者应注意的伤口处理；对患者的复诊与换药提供指示；对患者在检验检查中的异常情况、以及患者的其他诊断进行随诊与随访建议；若患者有置管，应提醒拔管前后的注意事项。'
}
all_data_maps['ruxianwaike'] = ruxianwaike_data_maps
# 呼吸内科
huxineike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','呼吸日间病房护理记录---护理评估','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','首次查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','查房记录---对病情的分析','查房记录---诊疗意见','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请描述患者出院后的注意事项，介绍患者的出院带药；根据患者在检验检查中的异常情况以及异常检验指标，对患者的复诊项提出建议；此外，提醒患者查询未出齐的报告，并提醒随诊注意事项。'
}
all_data_maps['huxineike'] = huxineike_data_maps
# 胃肠外科
weichangwaike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','查房记录---补充病史与体征','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','术后首次病程记录---手术简要经过','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的注意事项；根据患者的手术过程提醒患者对伤口与拆线的注意事项，与部分手术可能造成的术后情况；针对患者的其他检查情况，提出相应的复查建议；对患者在检验检查中的异常情况、以及患者的其他诊断进行随诊与随访建议；描述患者的出院带药。'
}
all_data_maps['weichangwaike'] = weichangwaike_data_maps
# 眼科
yanke_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        ############################################################## wjc模板
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        },
        ############################################################## yc删减
        # 'source_keys':{
        #     '字段':['科室类别','文书'],
        #     '文书':['日常病程记录','手术记录单'],
        # }
        ###############################################################
        # 48眼压: '日常病程记录'
        # 主要手术：if '术后首次病程记录' 
        #          elif 上级医师查房记录---手术/治疗方案 上级医师查房记录---诊疗计划 '手术记录单' 
        #          elif  主任医师首次查房记录---诊疗意见 主治医师首次查房记录---诊疗意见
        # 术后反应/出院情况 (关键词：出院)：'主治医师日常查房记录---TM员工名称TM 主治医生查房' split(\n) 术后第X日记录---观察记录 split(\n)
        # 
        # 删除'病理报告','未出结果病理报告'，对病理报告时间做一个筛选
        ###############################################################
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','手术记录单','术后评估/治疗后病程记录','术后首次病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{ 
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','上级医师查房记录---诊断依据','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请描述患者术后注意事项；介绍患者出院带药情况；建议患者复诊时间；若患者术中送病理，提醒患者及时查询未出齐的病理报告；此外，告知患者后续复诊与就诊建议。'
}
all_data_maps['yanke'] = yanke_data_maps
# 肿瘤科
zhongliuke_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断' ,
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','查房记录---诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','主治医师查房记录---诊断','主治医师查房记录---诊断依据','主治医师查房记录---鉴别诊断','主治医师查房记录---诊疗计划','主任医师查房记录---对病情的分析','主任医师查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','主治医师查房记录---诊疗计划','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['入院记录---现病史','24小时内入出院记录---入院情况','查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的注意与禁忌事宜；介绍患者的出院带药；对患者在检验检查中的异常情况、以及患者的其他诊断进行随诊与随访建议；根据患者诊疗计划对后续诊疗安排进行说明（如定期化疗等）。'
}
all_data_maps['zhongliuke'] = zhongliuke_data_maps
# 小儿科
xiaoerke_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    


    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','PUCAI','PCDAI','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','检查','检验','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录---主治医生查房','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的日常注意事项；描述患者的出院带药；此外，核对患者相应报告是否出齐；查看患者的报告中是否有异常情况，给出随诊与就诊建议；根据患者情况给出后续就诊科室。'
}
all_data_maps['xiaoerke'] = xiaoerke_data_maps
# 耳鼻喉科
erbihouke_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请告知患者出院后的注意事项与复诊科室；检查患者的所有报告是否出齐；随后，针对患者的异常检验与检查情况，提出相应随访与随诊建议；此外，描述患者的出院带药。'
}
all_data_maps['erbihouke'] = erbihouke_data_maps
# 妇科
fuke_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','新会诊记录---会诊医师所在科别或医疗机构名称','新会诊记录---会诊意见','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','查房记录---补充病史与体征','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的注意与禁忌事项；核对患者相应报告是否出齐，未出齐可提醒其通过电话询问结果；描述患者的出院带药；此外，查看患者的检查与检验中是否有异常情况，给出随诊与就诊建议；针对患者的情况，还需给出定期复诊或复查建议。'
}
all_data_maps['fuke'] = fuke_data_maps
# 甲状腺血管外科
jiazhuangxianxueguanwaike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','手术记录单','术后评估/治疗后病程记录','术后首次病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','查房记录---补充病史与体征','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的注意与禁忌事项。随后，核对患者相应报告是否出齐，若暂未出齐，可提醒患者查询日期与查询方式。需要特意说明，石蜡病理结果可能与目前诊断不符，最终诊断以石蜡病理为准；描述患者的出院带药；此外，查看患者的检查与检验中是否有异常情况，给出随诊与就诊建议；针对患者的情况，给出定期复诊或复查建议。'
}
all_data_maps['jiazhuangxianxueguanwaike'] = jiazhuangxianxueguanwaike_data_maps
# 内分泌
neifenmi_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单','全部检查'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','检查','检验','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','入院记录---主诉','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','新会诊记录---会诊医师所在科别或医疗机构名称','新会诊记录---会诊意见','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        ############################################################### yc
        # 完善检查：首次病程记录---诊疗计划
        # 1、一般情况：
        # 化疗方案:  必备：化疗前知情同意书---诊断  有些找不到来源 在医嘱--药品里
        #           if 主治医师首次查房记录---诊疗意见 主治医师首次查房记录---诊疗计划 主治医师首次查房记录---补充 主任医师日常查房记录---诊疗意见 有创诊疗操作记录---操作名称  会诊意见处理记录---受邀科室 新会诊记录---会诊目的 新会诊记录---会诊意见 主任医师首次查房记录---诊疗意见
        # 中医药治疗方案： 首次病程记录---诊疗计划
        # 术后反应/出院情况 (关键词：出院)：主治医师首次查房记录---诊疗意见  主任医师首次查房记录---诊疗意见
        #                                ？有创诊疗操作记录---患者一般情况 有创诊疗操作记录---操作过程顺利
        # 
        # 删除'病理报告','未出结果病理报告'，对病理报告时间做一个筛选
        ###############################################################
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请告知患者的随访科室；提醒患者出院后的注意与禁忌事项；针对患者的手术以及异常的报告，提醒患者的复查科室；若患者有出院带药，描述其出院用药信息；若患者有未出的报告结果，予以提醒。'
}
all_data_maps['neifenmi'] = neifenmi_data_maps
# 神经内科
shenjingneike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单','全部检查'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','检查','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的注意与禁忌事宜；告知患者的随访科室与时间；若患者有未出的报告结果，予以提醒；查看患者的相关报告与诊断，若有异常情况，提醒随访科室；此外，描述患者的出院用药信息。'
}
all_data_maps['shenjingneike'] = shenjingneike_data_maps
# 神经外科
shenjingwaike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','查房记录---诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊疗意见','查房记录----对病情的分析','查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请提醒患者出院后的注意与禁忌事项；给出患者的定期复诊或复查建议；描述患者的出院带药；针对患者的检查与检验中的异常情况，给出随诊与就诊建议。'
}
all_data_maps['shenjingwaike'] = shenjingwaike_data_maps
# 肾脏内科
shenzangneike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单','全部检查'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','新会诊记录---会诊医师所在科别或医疗机构名称','新会诊记录---会诊意见','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','既往史','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请告知患者随诊科室与随诊时间；提醒患者复查指标；提醒患者出院后的注意事项与禁忌事宜；核对并提醒患者还未出的相关报告；描述患者的出院带药，并制定下一步治疗计划与方案。'
}
all_data_maps['shenzangneike'] = shenzangneike_data_maps
# 消化内科
xiaohuaneike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单','全部检查'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','新会诊记录---会诊医师所在科别或医疗机构名称','新会诊记录---会诊意见','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','既往史','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请告知患者出院后的注意事项与随访科室；请提醒患者需要复查的相关检查；若患者有未出的报告结果，予以提醒；描述患者的出院带药信息。'
}
all_data_maps['xiaohuaneike'] = xiaohuaneike_data_maps
# 中医科
zhongyike_data_maps = {
    # 生命体征
    ## BP低、BP高(高低血压)、P(脉搏)、R(呼吸)、T(体温)
    # 住院信息
    ## 住院号、床号、入院时间、科别、科室、出院时间手动输入
    # 个人信息
    ## 姓名、年龄(需要判断)、性别
    # 体检摘要
    # 入院时简要病史
    # 入院诊断
    '患者基本信息':{
        'output_keys':{
            '住院号':'住院号',
            '床号':'床号',
            '入院时间':'入院时间',
            '出院时间':'出院时间',
            '科别':'科别',
            '科室':'科室',
            '姓名':'姓名',
            '年龄':'年龄',
            '性别':'性别',
            '低压(BP低)':'BP低',
            '高压(BP高)':'BP高',
            '脉搏(P)':'P',
            '呼吸(R)':'R',
            '体温(T)':'T',
            '入院诊断':'入院诊断',
            '入院时简要病史':'入院时简要病史',
            '体检摘要':'体检摘要',
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','出院医嘱'],
            '文书':['入院告知书---患者信息','告未成年患者监护人书---患者信息','新入院评估单---三、生理状况评估','入院记录---体格检查','入院记录---现病史','入院记录---初步诊断','首次病程记录---病例特点','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '住院期间医疗情况':{
        'output_keys':{
            '住院期间医疗情况':'住院期间医疗情况'
        },
        'source_keys':{
            '字段':['科室类别','检查','检验','日常病程辅检','文书'],
            '文书':['日常查房记录','入院记录---辅助检查','首次病程记录---病例特点','首次病程记录---诊断依据','查房记录---补充病史与体征','查房记录---入院后辅助检查','24小时内入出院记录---入院情况','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论'],
        }
    },
    '出院诊断':{
        'output_keys':{
            '出院诊断':'出院诊断'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['入院记录---初步诊断','入院记录---现病史','入院记录---主诉','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊断','查房记录---诊断依据','查房记录---鉴别诊断','查房记录---诊疗计划','查房记录---对病情的分析','查房记录---诊疗意见','术前小结---术前诊断','术前小结---手术指征','最后一日查房/病程记录','镜','阶段小结','手术记录单','术后首次病程记录','查房记录---诊断依据与鉴别诊断的分析','术后第一日记录','24小时内入出院记录---入院情况','24小时内入出院记录---入院诊断','入院记录---辅助检查','首次病程记录---病理特点','查房记录---TM员工名称TM 主治医生查房','查房记录---TM员工名称TM 主任医生查房','转入科记录','新会诊记录---会诊意见','新会诊记录---会诊目的','日常病程记录','辅检回报','疑难病例讨论记录---讨论意见','疑难病例讨论记录---主持人总结','死亡记录','死亡病历讨论'],
        }
    },
    '病程与治疗情况':{
        'output_keys':{
            '病程与治疗情况':'病程与治疗情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','未出检查结果报告','病理报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['化疗前知情同意书---诊断','首次病程记录---初步诊断','首次病程记录---诊断依据','首次病程记录---鉴别诊断','首次病程记录---诊疗计划','查房记录---诊疗意见','查房记录---补充病史与体征','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','查房记录----对病情的分析','查房记录----诊断依据与鉴别诊断的分析','查房记录---诊疗计划','新会诊记录---会诊医师所在科别或医疗机构名称','新会诊记录---会诊意见','手术记录单','术后首次病程记录','术后第一日记录','日常查房记录','日常病程记录','最后一日查房/病程记录','镜','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况'],
        ############################################################### yc
        # 完善检查：首次病程记录---诊疗计划
        # 化疗方案:  必备：化疗前知情同意书---诊断  有些找不到来源 在医嘱--药品里
        #           if 主治医师首次查房记录---诊疗意见 主治医师首次查房记录---诊疗计划 主治医师首次查房记录---补充 主任医师日常查房记录---诊疗意见 有创诊疗操作记录---操作名称  会诊意见处理记录---受邀科室 新会诊记录---会诊目的 新会诊记录---会诊意见 主任医师首次查房记录---诊疗意见
        # 中医药治疗方案： 首次病程记录---诊疗计划
        # 术后反应/出院情况 (关键词：出院)：主治医师首次查房记录---诊疗意见  主任医师首次查房记录---诊疗意见
        #                                ？有创诊疗操作记录---患者一般情况 有创诊疗操作记录---操作过程顺利
        # 
        # 删除'病理报告','未出结果病理报告'，对病理报告时间做一个筛选
        ###############################################################
        }
    },
    '出院后用药建议':{
        'output_keys':{
            '出院后用药建议':'出院后用药建议'
        },
        'source_keys':{
            '字段':['科室类别','全部诊断','文书','既往史','出院带药','异常检验指标','全部检查','未出检查结果报告','未出结果病理报告','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后首次病程记录---术中诊断','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','死亡记录','死亡病历讨论','24小时内入出院记录---入院情况','化疗前知情同意书---诊断'],
        }
    },
    '出院时情况':{
        'output_keys':{
            '出院时情况':'出院时情况'
        },
        'source_keys':{
            '字段':['科室类别','文书','最后一个在院评估单'],
            '文书':['查房记录---诊断','入院记录---主治医师48小时诊断','新会诊记录---目前诊断','术后','查房记录---对病情的分析','日常查房记录','日常病程记录','最后一日查房/病程记录','阶段小结','转入科记录','辅检回报','首次病程记录---病例特点','入院记录---体格检查','入院记录---专科情况','死亡记录','死亡病历讨论','查房记录---TM员工名称TM 主任医生查房','查房记录---TM员工名称TM 主治医生查房','新会诊记录---病史及体检摘要','24小时内入出院记录---入院情况','新入院评估单---三、生理状况评估','化疗前知情同意书---诊断'],
        }
    },
    '医嘱介绍':'请告知患者后续随访科室；请告知患者出院后需要复查的相关检查项；请提醒患者出院后的注意与禁忌事项；描述患者的出院带药信息。'
}
all_data_maps['zhongyike'] = zhongyike_data_maps



# 指令集合
instruction_dirs = [
    './出院小结及子字段/初始instruction.txt',
    './出院小结及子字段/扩充.txt',
    './出院小结及子字段/szx_instruction.txt'
]


instructions = []
for instruction_dir in instruction_dirs:
    with open(instruction_dir,'r') as f:
        for line in f.readlines():
            instructions.append(line.strip())

def get_instructions_v2024_0324(data_dir,out_dir,keshi):
    if out_dir != '':
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    random.seed(2023)
    if isinstance(data_dir,str):
        datas = load_excel_csv(data_dir)
        datas.fillna('',inplace=True)
    else:
        datas = data_dir
    data_lengths = {}
    data_lengths[keshi] = {}
    data_maps = all_data_maps[keshi]
    for key in data_maps.keys():
        if key == '医嘱介绍':
            continue
        data_lengths[keshi][key] = defaultdict(int)

    model_dir = cons_model_dir
    # tokenizer = AutoTokenizer.from_pretrained(model_dir,trust_remote_code=True)

    partion = 0.85
    out_name = '出院小结及子字段.jsonl'
    # delete_tokens = {
    #     '患者基本信息':4000,
    #     '住院期间医疗情况':8000,
    #     '出院诊断':6000,
    #     '病程与治疗情况':6000,
    #     '出院后用药建议':6000,
    #     '出院时情况':6000,
    # }
    delete_tokens = {
        '患者基本信息':99999,
        '住院期间医疗情况':99999,
        '出院诊断':99999,
        '病程与治疗情况':99999,
        '出院后用药建议':99999,
        '出院时情况':99999,
    }
    keep_nums = 0
    delete_nums = 0

    for col in datas.columns[1:]:
        datas[col] = datas[col].apply(transfer_value)

    final_datas = []
    
    for i in tqdm(range(datas.shape[0])):
        res_data = build_data(i,datas.iloc[i,:].copy(),data_maps,data_lengths,keshi)
        # break
        if res_data == None:
            continue
        final_datas.extend(res_data)

    # print('keep_nums:{}\tdelete_nums:{}'.format(keep_nums,delete_nums))

    with jsonlines.open(os.path.join(out_dir,out_name),'w') as f:
        for final_data in final_datas:
            f.write(final_data)
    return final_datas

if __name__ == '__main__':
    print('构造指令数据')
    data_dir = sys.argv[1]
    keshi = sys.argv[2]
    zylsh = sys.argv[3]
    out_dir = sys.argv[4]
    data_dir = os.path.join(data_dir,keshi)
    data_name = 'new_最终处理并合并后数据.csv'
    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    else:
        zylshs = [zylsh]

    print('处理{}个病例'.format(len(zylshs)))
    for zylsh in zylshs:
        csv_data_path = os.path.join(data_dir,zylsh,data_name)
        now_out_dir = os.path.join(out_dir,keshi,zylsh)
        get_instructions_v2024_0324(csv_data_path,now_out_dir,keshi)

