import pymssql
import pandas as pd
import csv
import os
import shutil
# import pyodbc
import time
import chardet
import re
import yaml
import logging
from datetime import timedelta,datetime
import json
import random
from LAC import LAC

def filter_text_and_keep_delimiters(text):
    '''
    内分泌科“出院时情况”删掉 血压/心率/毛糖
    '''
    # 使用正则表达式按逗号或句号分割文本，同时保留分隔符
    segments = re.split(r'([。，,、])', text)
    
    # 初始化一个空列表来存储最终保留的文本段
    filtered_segments = []
    print(segments)    
    # 遍历所有分割后的段落，包括分隔符
    for i in range(0, len(segments), 2):
        segment = segments[i] + (segments[i + 1] if i + 1 < len(segments) else '')
        # 检查当前段落是否包含"血压"或"mmhg"
        if '血压' in segment and 'mmhg' in segment.lower():
            continue
        if '心率' in segment and '次/分' in segment.lower():
            continue
        if ('血糖' in segment or '毛糖' in segment) and 'mmol' in segment.lower():
            continue

        filtered_segments.append(segment)
    
    # 将过滤后的文本段合并为一个字符串
    filtered_text = ''.join(filtered_segments)
    if len(filtered_text) == 0:
        filtered_text = '神清，精神可。'
    else:
        if filtered_text[-1] == '，':
            filtered_text = filtered_text[:-1] + '。'
    return filtered_text

def get_data_lengths(tokenizer,data):
    '''
    拿到指令长度(tokens)
    '''
    model_type = str(type(tokenizer))
    if 'ChatGLM' in model_type:
        input_ids = tokenizer.build_chat_input(data['instruction'])['input_ids'][0].tolist()
        answer = tokenizer.encode(data['output'],add_special_tokens=False)
        input_ids.extend(answer)
        input_ids.append(tokenizer.eos_token_id)
        length = len(input_ids)
    else:
        messages = [
        {"role": "user", "content": data['instruction']}
        ]
        enc = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True
        )
        length = len(enc)
    return length

def get_lac_model():
    '''
    拿到lac模型
    '''
    lac = LAC(mode='lac')
    return lac

def wenshu_is_24(wenshu):
    '''
    判断是不是24小时入出院
    '''
    if '24小时内' in wenshu['文书名'] or '出入院记录' in wenshu['文书名'] or '入出院记录' in wenshu['文书名']:
        return True
    return False

def standardize_date_day(date_str):
    """
    Standardize different date formats to time_cyxj common format 'YYYY-MM-DD HH:MM'.

    Args:
    date_str (str): The date string in varied formats.

    Returns:
    str: The standardized date string.
    """
    # Define the formats to be standardized
    format_1 = '%Y年%m月%d日'
    format_2 = '%Y.%m.%d'
    format_3 = '%Y-%m-%d'
    date_str = str(date_str)
    # Try to parse and standardize the date string
    try:
        if '年' in date_str:
            return datetime.strptime(date_str, format_1).strftime('%Y-%m-%d')
        elif '.' in date_str:
            return datetime.strptime(date_str, format_2).strftime('%Y-%m-%d')
        elif '-' in date_str:
            return datetime.strptime(date_str, format_3).strftime('%Y-%m-%d')
        else:
            return f"Error format of {date_str}"
    except ValueError as e:
        return f"Error: {str(e)}"

def get_date_to_day_from_regrex(text):
    '''
    用正则获取时间，允许时间中间出现空格，规则是 4个数字x 1-2个数字x(带0和不带0) 1-2个数字(带0和不带0) 日或空(中文时间会有日，符号时间就是空)
    '''
    date_pattern = r"(\d{4}) *[^0-9] *(\d{1,2}) *[^0-9] *(\d{1,2}) *(?:日)?"
    dates = re.findall(date_pattern, text)
    try:
        trips = dates[0]
        return_str = '{}-{}-{}'.format(trips[0],trips[1],trips[2])
        return return_str
    except:
        return 'regrex find date error'
# ------------------------转换指令数据的处理代码---------------------
def process_wenshu_for_ins(wenshu_list):
    ''' 处理文书
    1.删掉无用字段 如 最后修改时间......
    2.时间裁剪到天
    '''
    drop_keys = []
    for wenshu in wenshu_list:
        for drop_key in drop_keys:
            wenshu.pop(drop_key)
        wenshu['时间'] = wenshu['时间'].split(' ')[0]
        # 部分出院记录中，入院与出院时间解析错误，额外处理一下
        if '出院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu) and '出院日期' not in wenshu['内容'].keys():
            print('ori_wenshu:{}'.format(json.dumps(wenshu,ensure_ascii=False,indent=4)))
            try:
                ori_text = wenshu['内容']['入院日期']
                if '出院日期' not in ori_text:
                    print('没有变化,没找到出院日期')
                    continue
                start_index = None
                print('存在入院日期字段！！！')
                wenshu['内容']['入院日期'] = ori_text[:ori_text.index('出院日期')].strip()
                wenshu['内容']['出院日期'] = ori_text[ori_text.index('出院日期')+len('出院日期:'):].strip()
                print('成功处理后文书:\n{}'.format(json.dumps(wenshu,ensure_ascii=False,indent=4)))
            except:
                print('查找并分析错误:\n{}'.format(json.dumps(wenshu,ensure_ascii=False,indent=4)))
                

        # 处理一下包含人名的情况
        # flag = False
        # key_maps = {}
        # for now_key in wenshu['内容'].keys():
        #     lac_res = lac.run(u'{}'.format(now_key))
        #     per_indexes = [index for index, element in enumerate(lac_res[1]) if element == 'PER']
        #     new_key = now_key
        #     # 找到人名
        #     if len(per_indexes) != 0:
        #         per_names = [lac_res[0][per_index] for per_index in per_indexes]
        #         print('在原字段"{}"中找到人名:{}'.format(now_key,per_names))
        #         for per_name in per_names:
        #             new_key = new_key.replace(per_name,'')
        #     # 去掉TM等内容
        #     new_key = new_key.replace('TM员工名称TM','').strip()
        #     if new_key != now_key:
        #         flag = True
        #     # 获得字段映射
        #     key_maps[now_key] = new_key
        # if flag:
        #     # 更新
        #     wenshu_content = wenshu['内容']
        #     new_dict = {key_maps[key]:wenshu_content[key] for key in wenshu_content.keys()}
        #     wenshu['内容'] = new_dict

    return wenshu_list

def process_yizhu_for_ins(yizhu_list):
    ''' 处理医嘱
    1.把删除状态的医嘱去掉
    2.医嘱时间裁剪到天
    3.医嘱详情里，删掉医嘱时间，把空的value删掉
    '''
    processed_data = []
    for yizhu in yizhu_list:
        # 删掉id
        del yizhu['医嘱id']
        # 时间裁剪
        yizhu['医嘱时间'] = yizhu['医嘱时间'].split(' ')[0]
        # 创建一个新的医嘱详情列表，用于存放筛选后的元素
        filtered_details = []
        for detail in yizhu['医嘱详情']:
            # 检查 '状态' 字段是否为 '删除'，如果不是，则加入新的列表
            if '状态' in detail.keys() and detail['状态'] == '删除' or '作废' in detail['医嘱项名称']:
                continue
            
            # 删掉住院流水号和医嘱时间
            del detail['住院流水号']
            del detail['医嘱时间']

            # 检测需要删除的key
            delete_keys = []
            for k,v in detail.items():
                if v == '':
                    delete_keys.append(k)
            for delete_key in delete_keys:
                del detail[delete_key]
            filtered_details.append(detail)

        # 将筛选后的医嘱详情列表替换原来的 '医嘱详情' 字段
        yizhu['医嘱详情'] = filtered_details
        processed_data.append(yizhu)

    # 删除 '医嘱详情' 字段为空的字典元素
    return [item for item in processed_data if item['医嘱详情']]

def process_zhenduan_for_ins(zhenduan_list):
    ''' 处理诊断
    1. 时间分割
    2. 如果类型为空，把类型字段删掉
    3. 如果名称为空，这条数据跳过
    '''
    columns = ['诊断时间','诊断名称','诊断类型']
    processed_zhenduans = []
    for zhenduan in zhenduan_list:
        # 名称为空，跳过
        if zhenduan['诊断名称'].strip() == '':
            continue
        # 时间裁剪到天
        zhenduan['诊断时间'] = zhenduan['诊断时间'].split(' ')[0]
        zhenduan = {k:zhenduan[k] for k in columns}
        processed_zhenduans.append(zhenduan)
    return processed_zhenduans

def process_bingli_for_ins(bingli_list):
    ''' 处理病理
    1. 时间分割
    2. 把空的字段删掉
    '''
    columns = ['临床诊断','病理类型','病理诊断结果','镜下所见','肉眼所见','免疫组化','报告内容']
    processed_binglis = []
    for bingli in bingli_list:
        new_bingli = {}
        new_bingli['检查时间'] = bingli['检查时间'].split(' ')[0]
        new_bingli['报告时间'] = bingli['报告时间'].split(' ')[0]
        for k in columns:
            if bingli[k].strip() != '':
                new_bingli[k] = bingli[k]
        processed_binglis.append(new_bingli)
    return processed_binglis

def find_ruyuan_time(i,data):
    '''
    **args**
    i:数据的index
    data:DataFrame的一行

    **功能**
    1. 通过得到的规则，遍历文书并拿到入院时间
    2. 如果入院时间和出院小结中的不一样，直接修改

    **处理逻辑**
    1. 先拿到出院小结中的入院时间
    2. 拿到出院记录中的入院时间
    3. 查找文书中的入院时间
    4. 比较文书中的和出院小结中的，如果匹配则直接结束
    5. 因为有时候出院小结中的存在错误，如果不匹配，再拿出院记录中的时间再匹配一次
    6. 如果全都是error，就找不到。如果是存在符合规则的，但是时间不同，修改一下出院小结中的时间，防止错误数据导致幻觉(耳鼻喉科---index225,文书中查找到的是2020-12-11，但是出院记录和出院小结中的都是2020-12-10)
    7. 最终返回 ||文书中的入院时间|| ||小结中的入院时间|| ||能否找到||
    '''
    ori_index = i
    zylsh = data.iat[0]
    # ----------------------------从出院小结中查找----------------------------
    hulijilu_list = data.iat[7]
    for hulijilu in hulijilu_list:
        if hulijilu['护理记录名'] == '出院小结(死亡小结)':
            break
    if hulijilu['护理记录名'] != '出院小结(死亡小结)':
        print('当前例子找不到出院小结:{}\n'.format(i))
        return [],'-1',False
    else:
        # 拿"基本信息"中的入院时间，"病人信息"中的会有错误
        time_cyxj = hulijilu['内容']['基本信息']['入院时间']
    # ----------------------------从入院文书中查找----------------------------
    wenshu_list = data.iat[5]
    # 文书中的"入院时间"，比如"入院评估单"、"入院记录"等，用一个list保存
    wenshu_time_in = []
    # 出院记录的"入院时间"，可能存在多个来源，比如"出院记录"、"乳腺外科出院记录"，用一个list保存
    now_times_in_record = []
    for wenshu in wenshu_list:
        # ----------------------------出院记录中查找----------------------------
        if '出院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu):
            try:
                time_in_record = wenshu['内容']['入院日期'].strip()
                time_in_record = get_date_to_day_from_regrex(time_in_record)
            except:
                # print('出院记录中查找入院日期字段错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                time_in_record = '-1'
            now_times_in_record.append((time_in_record,wenshu['文书名']))
        # 24小时入出院中找 入院时间
        if wenshu_is_24(wenshu):
            try:
                ori_text = wenshu['内容']['姓名']
                text = ori_text
                # 其中还会存在出院时间，所以要单独判断一下
                if '出院时间' in text:
                    text = text[:text.index('出院时间:')]
                text = text[text.index('入院时间'):].strip()
                time_in = get_date_to_day_from_regrex(text)
                now_times_in_record.append((time_in,wenshu['文书名']))
            except:
                try:
                    ori_text = ori_text
                    # print('24小时入出院 在姓名中抽取入院时间错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],ori_text))
                    del ori_text,text
                except:
                    # print('24小时入出院 查找[内容][姓名]字段错误at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass
        # ----------------------------其他文书中查找----------------------------
        # 新入院评估单(入科室时间)、入院告知书、入院记录、入院录、告未成年患者监护人书
        
        # 入院告知书中找 入院时间
        if '新入院评估单' in wenshu['文书名']:
            try:
                text = wenshu['内容']['一、基本信息']
                # 根据字符串先定位，并去除所有的空格，防止因为空格导致识别与标准化错误
                time_in = text[text.index('入科室时间'):].strip()
                # 后根据正则识别入院时间
                time_in = get_date_to_day_from_regrex(time_in)
                wenshu_time_in.append((time_in,wenshu['文书名']))
                del text
            except:
                try:
                    tmp_val = text
                    # print('新入院评估单抽取错误 at index:{} 文书名:{} \n内容---一、基本信息:{}\n\n'.format(i,wenshu['文书名'],tmp_val))
                    del text
                except:
                    # print('新入院评估单抽取错误抽取错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass

        if '入院告知书' in wenshu['文书名']:
            try:
                text = wenshu['内容']['患者信息']
                time_in = text[text.index('入院日期'):].strip()
                time_in = get_date_to_day_from_regrex(time_in)
                wenshu_time_in.append((time_in,wenshu['文书名']))
                del text
            except:
                try:
                    tmp_val = text
                    # print('入院告知书抽取错误 at index:{} 文书名:{} \n内容---患者信息:{}\n\n'.format(i,wenshu['文书名'],tmp_val))
                    del text
                except:
                    # print('入院告知书抽取错误抽取错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass

        if '告未成年患者监护人书' in wenshu['文书名']:
            try:
                text = wenshu['内容']['患者信息']
                time_in = text[text.index('入院日期'):].strip()
                time_in = get_date_to_day_from_regrex(time_in)
                wenshu_time_in.append((time_in,wenshu['文书名']))
                del text
            except:
                try:
                    tmp_val = text
                    # print('告未成年患者监护人书抽取错误 at index:{} 文书名:{} \n内容---患者信息:{}\n\n'.format(i,wenshu['文书名'],tmp_val))
                    del text
                except:
                    # print('告未成年患者监护人书抽取错误抽取错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass

        # 正常入院记录中找 入院时间
        if '入院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu):
            try:
                if '患者一般情况' in wenshu['内容'].keys():
                    text = wenshu['内容']['患者一般情况']
                    time_in = text[text.index('入院日期'):].strip()
                    time_in = get_date_to_day_from_regrex(time_in)
                    wenshu_time_in.append((time_in,wenshu['文书名']))
                    del text
                elif '病人信息' in wenshu['内容'].keys():
                    text = wenshu['内容']['病人信息']
                    time_in = text[text.index('入院日期'):].strip()
                    time_in = get_date_to_day_from_regrex(time_in)
                    wenshu_time_in.append((time_in,wenshu['文书名']))
                    del text
            except:
                try:
                    tmp_val = text
                    # print('入院记录中抽取入院日期错误at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],text_gaozhi))
                    del text
                except:
                    # print('入院记录查找[内容][患者一般情况]或[病人信息]字段错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass

        # 入院录---病人信息 正则查找入院时间(眼科中存在的异常情况添加)
        if '入院录' in wenshu['文书名']:
            try:
                text = wenshu['内容']['病人信息']
                time_in = text[text.index('入院时间'):].strip()
                time_in = get_date_to_day_from_regrex(time_in)
                wenshu_time_in.append((time_in,wenshu['文书名']))
                del text
            except:
                try:
                    tmp_val = text
                    # print('入院录中抽取入院日期错误at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],text_gaozhi))
                    del text
                except:
                    # print('入院录查找[内容][病人信息]字段错误 at index:{} 文书名:{} \n内容:{}\n\n'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass
    # 此处得到了三类入院数据
    # time_cyxj             出院小结中的入院时间
    # wenshu_time_in        病历文书中的入院时间
    # now_times_in_record   出院记录中的入院时间
    # ----------------------------分析是否匹配----------------------------
    # 出院小结时间分割到天
    time_cyxj = str(time_cyxj).split(' ')[0]
    # 格式统一一下 YYYY-MM-DD
    times = [standardize_date_day(tmp[0]) for tmp in wenshu_time_in]
    # print('出院小结:{}\t病历文书:{}\t病历文书_时间:{}\t出院记录:{}\t{}'.format(time_cyxj,wenshu_time_in,times,now_times_in_record,len(set(times))))
    # 出院记录中的先处理一下
    check_time_record = None
    for c_item in now_times_in_record:
        try:
            # 出院记录中的时间分析一下
            check_time_record = standardize_date_day(c_item[0])
            break
        except:
            # print('处理出院记录中的时间错误:{}'.format(c_item))
            pass
    if check_time_record == None:
        pass
        # print('出院记录时间找不到')
    else:
        pass
        # print('处理的出院记录中的时间:{}'.format(check_time_record))
    # 先使用出院小结的时间check一下
    check_time = standardize_date_day(time_cyxj)
    return_time = check_time
    # 文书中的入院时间只有一个
    if len(set(times)) == 1:
        if check_time == times[0]:
            res = '通过'
            # print('index:{}\t只有一个，检测一下:{}'.format(ori_index,res))
        else:
            res = '不通过,index:{}\t出院小结:{}\t文书:{}'.format(ori_index,check_time,times[0])
    # 不同病历文书中有多个入院时间
    if len(set(times))!=1:
        finds = []
        not_finds = []
        for item in wenshu_time_in:
            if standardize_date_day(item[0]) == check_time:
                finds.append(item[1])
            else:
                not_finds.append(item[1])
        # print('自动检测 at index:{}'.format(ori_index))
        # print('找到的:{}'.format(finds))
        # print('没找到的:{}'.format(not_finds))
        if len(finds)>0:
            res = '通过'
            # print('index:{}\t存在多个，检测一下:{}'.format(ori_index,res))
        else:
            res = '不通过'
            # print('index:{}\t存在多个，检测一下:{}'.format(ori_index,res))
    # 检查一下，如果结果是不通过，那么就用出院记录的再判断一下
    if res.startswith('不通过') and check_time_record != None:
        # print('******此处再使用出院记录的时间分析一下******')
        check_time = check_time_record
        return_time = check_time
        if len(set(times)) == 1:
            if check_time == times[0]:
                res = '通过'
                # print('index:{}\t只有一个，检测一下:{}'.format(ori_index,res))
            else:
                res = '不通过,index:{}\t出院小结:{}\t文书:{}'.format(ori_index,check_time,times[0])
        # 不同病历文书中有多个入院时间
        if len(set(times))!=1:
            finds = []
            not_finds = []
            for item in wenshu_time_in:
                if standardize_date_day(item[0]) == check_time:
                    finds.append(item[1])
                else:
                    not_finds.append(item[1])
            # print('自动检测 at index:{}'.format(ori_index))
            # print('找到的:{}'.format(finds))
            # print('没找到的:{}'.format(not_finds))
            if len(finds)>0:
                res = '通过'
                # print('index:{}\t存在多个，检测一下:{}'.format(ori_index,res))
            else:
                res = '不通过'
                # print('index:{}\t存在多个，检测一下:{}'.format(ori_index,res))
    if res.startswith('不通过'):
        # print('最终判断结果:{}'.format('不通过'))
        final_find = False
    else:
        # print('最终判断结果:{}'.format('通过'))
        final_find = True
    # print('入院时间获取返回值: 文书中:{}\t返回时间:{}\t是否找得到:{}'.format(wenshu_time_in, return_time, final_find))
    return wenshu_time_in, return_time, final_find



def find_chuyuan_time(i,data):
    '''
    **args**
    i:数据的index
    data:DataFrame的一行

    **功能**
    1. 通过判断医嘱是否能推理出出院时间，若不能，返回"无法判断"
    2. 拿到 出院记录/出院小结 中的出院时间，这是真实出院时间，以对检查、检验、病理进行mask
    '''
    zylsh = data.iat[0]
    yizhu_list = data.iat[3]
    wenshu_list =  data.iat[5]
    hulijilu_list = data.iat[7]
    # ----------------------------从出院小结中查找----------------------------
    for hulijilu in hulijilu_list:
        if hulijilu['护理记录名'] == '出院小结(死亡小结)':
            break
    if hulijilu['护理记录名'] != '出院小结(死亡小结)':
        print('当前例子找不到出院小结:{}'.format(i))
        return ('-1',[]), '-1', False
    else:
        time_cyxj = hulijilu['内容']['基本信息']['出院时间']
    # 从出院记录中查找
    # 出院记录的"出院时间"，可能存在多个来源，比如"出院记录"、"乳腺外科出院记录"，用一个list保存
    wenshu_time_out = []
    # ----------------------------从出院记录中查找----------------------------
    for wenshu in wenshu_list:
        if '出院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu):
            try:
                time_out = wenshu['内容']['出院日期']
                wenshu_time_out.append((time_out,wenshu['文书名']))
            except:
                # print('出院记录中查找出院日期字段错误 at index:{} 文书名:{} 内容:{}'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                pass
        if wenshu_is_24(wenshu):
            try:
                text = wenshu['内容']['姓名']
                time_out = text[text.index('出院时间'):].strip()
                time_out = get_date_to_day_from_regrex(time_out)
                wenshu_time_out.append((time_out,wenshu['文书名']))
                del text
            except:
                try:
                    text = text
                    # print('24小时入出院 在姓名中抽取出院时间错误 at index:{} 文书名:{} 内容:{}'.format(i,wenshu['文书名'],text))
                    del text
                except:
                    # print('24小时入出院 查找[内容][姓名]字段错误at index:{} 文书名:{} 内容:{}'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass
        if '呼吸日间病房护理记录' in wenshu['文书名']:
            try:
                text = wenshu['内容']['姓名']
                time_out = text[text.index('出院时间'):].strip()
                time_out = get_date_to_day_from_regrex(time_out)
                wenshu_time_out.append((time_out,wenshu['文书名']))
                del text
            except:
                try:
                    text = text
                    # print('呼吸日间病房护理记录 在姓名中抽取出院时间错误 at index:{} 文书名:{} 内容:{}'.format(i,wenshu['文书名'],text))
                    del text
                except:
                    # print('呼吸日间病房护理记录 查找[内容][姓名]字段错误at index:{} 文书名:{} 内容:{}'.format(i,wenshu['文书名'],json.dumps(wenshu,ensure_ascii=False,indent=2)))
                    pass

    # ----------------------------从医嘱中查找----------------------------
    res_chuyuan = True
    # 是否找到出院医嘱， 或者医嘱是否只有"出院"两个字
    yizhu_finds = False
    yizhus = []
    for yizhu in yizhu_list:
        if '出院' in yizhu['医嘱详情'][0]['医嘱项名称']:
            yizhu_finds = True
            yizhus.append(yizhu)
            if yizhu['医嘱详情'][0]['医嘱项名称'] == '出院':
                # 如果医嘱只是 "出院"，那么就无法判断出院时间
                res_chuyuan = False   
    if not yizhu_finds:
        # print('index:{} 没找到出院医嘱'.format(i))
        res_chuyuan = False
    # print('出院医嘱:{}'.format(yizhus))
    # ----------------------------分析是否匹配----------------------------
    # 出院时间统计规则
    # 出院小结中的出院日期，用作匹配
    # 文书中，查找出院记录的出院日期
    # 查找医嘱中和出院相关的信息(可能有多个，有的作废，有的已结束等等)

    # 出院小结中的时间提取到天为单位
    a_date = get_date_to_day_from_regrex(str(time_cyxj))
    a_date_check = standardize_date_day(a_date)
    # 先用出院小结的时间判断一下，因为有的出院小结可能是"    -  -"
    res_chuyuan_time = None
    if a_date_check.startswith('Error'):
        a_check_flag = False
    else:
        res_chuyuan_time = a_date_check
        a_check_flag = True
    # print("index:{}\tzylsh:{}".format(i,zylsh))
    # print('出院小结中的时间:{}'.format(time_cyxj))
    # print('出院小结中的时间_提取到天:{}'.format(a_date))
    # print("初始的时间:{}".format(wenshu_time_out))
    # 是否全部符合标准
    flag = True
    # 是否有一个符合标准
    one_flag = False
    standards = []
    for item in wenshu_time_out:
        b_item,b_source = item
        # 处理到天
        b_item = get_date_to_day_from_regrex(b_item)
        # 处理成同一表示格式
        check_time = standardize_date_day(b_item)
        if check_time.startswith('Error'):
            flag = False
        else:
            # 如果没拿到出院时间，赋值
            if res_chuyuan_time == None:
                res_chuyuan_time = check_time
            # 统计标准的时间
            standards.append(check_time)
            one_flag = True
    # print('标准化后:{}'.format(standards))
    # print('出院小结中是否全部符合规范:{}'.format(a_check_flag))
    # print('出院记录中是否全部符合规范:{}'.format(flag))
    # print('出院记录中是否存在符合规范的:{}'.format(one_flag))
    merge_flag = one_flag | a_check_flag
    # print('出院小结+出院记录中是否存在符合规范的:{}'.format(merge_flag))
    # 如果都是不符合标准的，使用出院小结的时间|文书的时间
    if not merge_flag:
        # print('没有一个符合规范')
        # wenshu_final_time = wenshu_list[-1]['时间']
        # wenshu_final_time = get_date_to_day_from_regrex(wenshu_final_time)
        # wenshu_final_time = standardize_date_day(wenshu_final_time)
        # hulijilu_time = hulijilu['时间']
        # hulijilu_time = get_date_to_day_from_regrex(hulijilu_time)
        # hulijilu_time = standardize_date_day(hulijilu_time)
        # if wenshu_final_time > hulijilu_time:
        #     res_chuyuan_time = wenshu_final_time
        # else:
        #     res_chuyuan_time = hulijilu_time
        # print('wenshu_final_time:{}'.format(wenshu_final_time))
        # print('hulijilu_time:{}'.format(hulijilu_time))
        res_chuyuan_time = '9999-99-99'
    # 如果 没有一个符合规范，并且医嘱不是("出院"或找不到出院医嘱)，那这条就不要了
    if merge_flag == False and res_chuyuan == True:
        data_is_normal = False
    else:
        data_is_normal = True
    # 返回4个值
    # 1: (出院小结，出院记录)
    # 2: 最终返回的出院时间
    # 3: 医嘱是否正常
    # 4: 数据是否正常
    # print('出院时间获取返回值:出院小结:{}\t文书:{}\t返回的出院时间:{}\t医嘱是否正常:{}\t数据是否正常:{}'.format(time_cyxj, wenshu_time_out, res_chuyuan_time, res_chuyuan, data_is_normal))
    return (time_cyxj, wenshu_time_out), res_chuyuan_time, res_chuyuan, data_is_normal


# ----------------------------------------------------------
# 把候选项加上双引号，拼接成字符串
def transfer_choices_to_str(out_keys,use_Chinese = True):
    out_keys = ['“{}”'.format(time_cyxj) for time_cyxj in out_keys]
    join_str = random.choice(['，','、'])
    if use_Chinese:
        out_keys_str = join_str.join(out_keys[:-1]) + random.choice(['和','以及','与',join_str]) + out_keys[-1]
    else:
        out_keys_str = join_str.join(out_keys)
    return out_keys_str
# 把检验为空的行都删掉(构造检验相关任务时需要预先处理一下)
def drop_empty_jianyan_rows(row):
    if len(row.iat[11]) != 0:
        return True
    return False

def group_by_thousand(input_dict):
    '''
    把dict中的key变成以1000为一个范围
    '''
    grouped_dict = {}
    for key, value in input_dict.items():
        # 计算键属于哪个区间（例如，1500的键属于1区间，2500的键属于2区间）
        group = f"{(key // 1000) * 1000}-{(key // 1000 + 1) * 1000 -1}"
        # 将值累加到相应区间
        if group in grouped_dict:
            grouped_dict[group] += value
        else:
            grouped_dict[group] = value
    grouped_dict = {k:grouped_dict[k] for k in sorted(grouped_dict.keys(), key = lambda x:int(x.split('-')[0]))}
    return grouped_dict
    
def transfer_value(val):
    '''
    load dataframe后，字符串转json
    '''
    if val == '':
        return []
    else:
        return json.loads(val)

def json_to_text(value:dict,tab_num = 0, empty_skip = True):
    '''
    json转text
    '''
    text_str = ''
    for key in value.keys():
        # 如果是嵌套
        if type(value[key]) == dict:
            text_str = text_str + tab_num * '\t' + str(key) + '\n' + json_to_text(value[key], tab_num + 1, empty_skip)
        elif type(value[key]) == list:
            text_str = text_str + tab_num * '\t' + str(key) + '\n'
            for v_item in value[key]:
                text_str = text_str + json_to_text(v_item, tab_num + 1, empty_skip) + '\n'
        # 不是嵌套
        elif value[key] != None:
            if empty_skip and value[key] == '':
                continue
            text_str = text_str + tab_num * '\t' + '{}:{}\n'.format(str(key),str(value[key]))
    return text_str

def has_empty_key(value:dict):
    '''
    是否有空值的key
    '''
    find_flag = False
    for key in value.keys():
        # 如果是嵌套
        if type(value[key]) == dict:
            find_flag = find_flag | has_empty_key(value[key])
        elif type(value[key]) == list:
            for v_item in value[key]:
                find_flag = find_flag | has_empty_key(v_item)
        # 不是嵌套
        elif value[key] != None:
            if value[key] == '':
                return True
    return find_flag

def get_every_nums(total,num_people):
    base = total // num_people
    
    # 使用取模运算来计算多余的分数
    remainder = total % num_people
    
    # 创建一个列表，包含每个人的分数
    distribution = [base for _ in range(num_people)]
    
    # 分配多余的分数
    for i in range(remainder):
        distribution[i] += 1
    return distribution

def get_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file,encoding='utf-8')        
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

def get_pattern_and_replace_datas(path):
    """
    加载护理额外脱敏的分析结果
    """
    re_compiles = []
    replace_datas = []
    with open(path,'r',encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            original,replace = line.split('-->')
            replace = 'TM'+replace+'TM'
            original_splits = original.split(',')
            if len(original_splits) == 1:
                re_pattern = re.compile(r'(<{}(?: [^>/]*?)?>).*?<'.format(original_splits[0]))
            else:
                mates = '(?:'+'|'.join(original_splits)+')'
                re_pattern = re.compile(r'(<{}(?: [^>/]*?)?>).*?<'.format(mates))
            re_compiles.append(re_pattern)
            replace_datas.append(replace)
    return re_compiles,replace_datas

def get_pattern_admission_and_bed():
    """
    文书脱敏住院号和床号
    """
    re_compiles = []
    replace_datas = []
    re_compiles.append(re.compile(r'(住院号(?::|：|&nbsp;| ){1,2}<[^>]*?>)[A-Za-z0-9]+<'))
    replace_datas.append('TM住院号IDTM')
    re_compiles.append(re.compile(r'(床[号位](?::|：|&nbsp;| ){1,2}<[^>]*?>)[\+0-9A-Za-z床]+<'))
    replace_datas.append('TM床号IDTM')
    return re_compiles,replace_datas
    

def get_pattern_and_replace_datas_2():
    """
    自定义护理额外脱敏
    """
    re_compiles = []
    replace_datas = []
    re_compiles.append(re.compile(r'住院号(?::|：|&nbsp;| ){1,2}[A-Za-z0-9]+ '))
    replace_datas.append('住院号：TM住院号IDTM ')
    re_compiles.append(re.compile(r'床 *[号位](?::|：|&nbsp;| ){1,2}[\+0-9A-Za-z床]+ '))
    replace_datas.append('床号：TM床号IDTM ')
    return re_compiles,replace_datas

def get_pattern_and_replace_datas_3():
    """
    自定义护理额外脱敏
    """
    re_compiles = []
    replace_datas = []
    re_compiles.append(re.compile(r'(住院号(?::|：|&nbsp;| ){1,2}<.*?<Text>)[A-Za-z0-9]+(</Text>.*?<InnerValue>)[A-Za-z0-9]+(</InnerValue>)'))
    replace_datas.append('TM住院号IDTM')
    re_compiles.append(re.compile(r'(床 *[号位](?::|：|&nbsp;| ){1,2}<.*?<Text>)[\+0-9A-Za-z床]+(</Text>.*?<InnerValue>)[\+0-9A-Za-z床]+(</InnerValue>)'))
    replace_datas.append('TM床号IDTM')
    return re_compiles,replace_datas

def get_time(fmt='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时间
    """
    ts = time.time()
    ta = time.localtime(ts)
    t = time.strftime(fmt, ta)
    return t

# 加载yaml
def load_config(config_file):
    encoding = detect_encoding(config_file)
    with open(config_file, "r", encoding=encoding['encoding']) as f:
        return yaml.safe_load(f)
    
# 链接数据库
def connect_db(config_file,driver="{SQL Server}"):
    db_configs = load_config(config_file)
    # ip
    sql_host = db_configs['sql_host']
    # 端口(默认1433)
    sql_port = db_configs['sql_port']
    # 用户
    sql_user = db_configs['sql_user']
    # 密码
    sql_passwd = db_configs['sql_passwd']
    # 数据库名
    sql_database = db_configs['sql_database']
    connect_sentence = 'DRIVER={};SERVER={},{};DATABASE={};ENCRYPT=no;UID={};PWD={};'.format(driver,sql_host,sql_port,sql_database,sql_user,sql_passwd)
    return pyodbc.connect(connect_sentence)

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

# 加载excel或者csv
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

# 字典树相关
#########################################################
# 字典树替换函数
def build_dictonarys(lists):
    dicts = {}
    for name in lists:
        now_dict = dicts
        for word in name:
            if word not in now_dict:
                now_dict[word] = {}
            now_dict = now_dict[word]
        now_dict['end'] = 'end'
    return dicts

def trie_search(text,dicts,idx):
    res = -1
    for index in range(idx,len(text)):
        word = text[index]
        # 出现end，说明当前是一个需要查找的名字的结尾，先存起来，因为要找到最长
        if 'end' in dicts.keys():
            res = index-idx
        # 当前字符不在现在的树中，返回
        if word not in dicts.keys():
            return res
        # 在树中，继续查找
        else:
            dicts = dicts[word]
    if 'end' in dicts.keys():
        return len(text) - idx
    else:
        return res
def find_idx_and_trie_replace(text,dicts,replace_name):
    idx_list = []
    idx = 0
    while idx < len(text):
        # 字典树search
        idx_length = trie_search(text,dicts,idx)
        if(idx_length != -1):
            idx_list.append((idx,idx+idx_length))
            idx = idx + idx_length -1
        idx += 1
    new_text = ''
    idx = 0
    for id_tuple in idx_list:
        new_text += text[idx:id_tuple[0]] + replace_name
        idx = id_tuple[1]
    new_text += text[idx:]
    return new_text

def find_idx(text,dicts):
    idx = 0
    while idx < len(text):
        # 字典树search
        idx_length = trie_search(text,dicts,idx)
        if(idx_length != -1):
            return True
        idx += 1
    return False

#########################################################
def execute_sql_file(sql_file,cursor,mode='multi',depart_id=None,log=None):
    encoding = detect_encoding(sql_file)
    if mode == 'line':
        # 一行一行读取
        with open(sql_file,'r',encoding=encoding['encoding']) as f:
            for line in f.readlines():
                if line.strip() == '':
                    continue
                if '{}' in line:
                    line = line.format(depart_id)
                if log == None:
                    print('execute:{}'.format(line.strip()))
                else:
                    log.info('execute:{}'.format(line.strip()))

                try:
                    cursor.execute(line)
                    if log == None:
                        print('success')
                    else:
                        log.info('success')
                except Exception as e:
                    if log == None:
                        print('error:{}'.format(e))
                    else:
                        log.info('error:{}'.format(e))
    elif mode == 'multi':
        # 读取到分号就执行
        sql_sentence = ''
        with open(sql_file,'r',encoding=encoding['encoding']) as f:
            for line in f.readlines():
                line = line.strip()
                if '{}' in line:
                    line = line.format(depart_id)
                sql_sentence = sql_sentence.strip() + ' ' + line
                if sql_sentence.endswith(';'):
                    if log == None:
                        print('execute:{}'.format(sql_sentence))
                    else:
                        log.info('execute:{}'.format(sql_sentence))
                    try:
                        cursor.execute(sql_sentence)
                        if log == None:
                            print('success')
                        else:
                            log.info('success')
                    except Exception as e:
                        if log == None:
                            print('error:{}'.format(e))
                        else:
                            log.info('error:{}'.format(e))
                    sql_sentence = ''
    else:
        raise ValueError('读取sql的模式错误')

# 向新服务器中插入表
def share_datas(from_conn,to_cursor,table_name,sql_file):
    datas = pd.read_sql('SELECT * FROM {}'.format(table_name), from_conn)
    with open(sql_file,'r') as f:
        for line in f:
            line = line.strip() 
            if not '?' in line:
                to_cursor.execute(line)
            else:
                for i in range(datas.shape[0]):
                    to_cursor.execute(line,tuple(datas.iloc[i]))

def insert_datas_from_files(cursor,sql_file,ids,log):
    with open(sql_file,'r') as f:
        for line in f:
            line = line.strip() 
            log.info('execute:{}'.format(line))
            if not '?' in line:
                cursor.execute(line)
            else:
                for id in ids:
                    cursor.execute(line,(id))
