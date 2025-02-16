# -*- coding: utf-8 -*-
import sys
import imp

import numpy as np
imp.reload(sys)
import sys
import shutil
import string
from commons.utils import *
from commons.preprocess import *
from commons.constants import *
import pandas as pd
from tqdm import tqdm
import re
from bs4 import BeautifulSoup,Tag
import bs4
import json
from copy import deepcopy
from collections import defaultdict
import os
from datetime import timedelta,datetime
from faker import Faker
import random


def transfer_value(val):
    if val == '':
        return {}
    else:
        return json.loads(val)

def df_to_json(df):
    res_js = {}
    res_js_text = {}
    for i in range(df.shape[0]):
        zylsh = df.iat[i,0]
        res_js[zylsh] = df.iat[i,1]
        res_js_text[zylsh] = df.iat[i,2]
    with open('./输出/processed.json', 'w', encoding='utf-8') as json_file:
        json.dump(res_js, json_file, ensure_ascii=False, indent=4)
    with open('./输出/text_processed.json', 'w', encoding='utf-8') as json_file:
        json.dump(res_js_text, json_file, ensure_ascii=False, indent=4)
    return res_js,res_js_text
def transfer_value_to_str(val):
    if val == {}:
        return ''
    else:
        return json.dumps(val,ensure_ascii=False)

def generate_random_zhuyuanhao():
    random_val = random.random()

    if random_val <= 0.5:
        # “z”加上4-6位数字
        content = 'z' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))
    elif random_val <= 0.7:
        # “zyh”加上4-6位数字
        content = 'zyh' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))
    elif random_val <= 0.9:
        # 第三种情况：随机生成一个大写字母加上“-”和4-6位数字
        content = random.choice(string.ascii_uppercase) + '-' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))
    else:
        # 第四种情况：使用“hosp”作为前缀，后面加上4-6位数字
        content = 'hosp' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))

    return content

def generate_random_chuanghao():

    choice = random.randint(1, 4)
    
    if choice == 1:
        # 生成2-5位数字，可以以0开头
        content = ''.join(random.choices('0123456789', k=random.randint(2, 5)))
    elif choice == 2:
        # 返回"RICU"
        content = 'RICU'
    elif choice == 3:
        # 生成1-2个大写字母+1-2个数字，可以以0开头
        letters = ''.join(random.choices(string.ascii_uppercase, k=random.randint(1, 2)))
        numbers = ''.join(random.choices('0123456789', k=random.randint(1, 2)))
        content = letters + numbers
    else:
        # 生成“+”加上2-4个数字
        content = '+' + ''.join(random.choices('0123456789', k=random.randint(2, 4)))

    # 随机决定是否添加“床”作为后缀
    if random.random() < 0.1:
        content += "床"

    return content


def generate_random_name(fake):
    # 正确格式
    if random.random() < 0.8:
        return fake.name()
    else:
        number = random.randint(0, 9999)
        # 正确格式
        # return f"{number:04}"
        # 构造格式
        return f"测试病人{number:04}"


def end_with_underline(key):
    for i in range(1,5):
        if key.endswith('_{}'.format(i)):
            return True
    return False

tuomin_fixes = []
with open('./脱敏修复.txt','r') as f:
    for line in f.readlines():
        line = line.strip()
        tuomin_fixes.append(line.split('-->'))

transfer_keys = []
with open('./transfer_keys.txt','r') as f:
    for line in f.readlines():
        line = line.strip()
        transfer_keys.append(line)

keshi_list = cons_keshis
def process_and_merge(data_dir,out_dir):
    # ------------------------------------1.处理并合并---------------------------------------
    random.seed(2023)
    # 0:部分 1:全量
    data_type = 1
    data_nums = 5000
    patient_nums = 20
    # data_dir = '/HL_user01/emr_datas/ruxianwaike'
    if out_dir != '':
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    # 文书
    print('处理文书')
    data_dir_wenshu = os.path.join(data_dir,'wenshu.csv')
    res_wenshu,html_text_data,patient_zylsh = get_wenshu(data_dir_wenshu,data_type,data_nums,patient_nums)
    zylsh = res_wenshu.iat[0,0]
    # 病理
    print('处理病理')
    data_dir_binli = os.path.join(data_dir,'bingli.csv')
    res_bingli = get_bingli(data_dir_binli,data_type,data_nums,patient_zylsh)
    # print(res_bingli)
    # 医嘱
    print('处理医嘱')
    data_dir_yizhu = os.path.join(data_dir,'yizhu.csv')
    res_yizhu = get_yizhu(data_dir_yizhu,data_type,data_nums,patient_zylsh)
    # 护理记录
    print('处理护理记录')
    data_dir_hulijilu = os.path.join(data_dir,'hulijilu.csv')
    res_hulijilu,xml_text_data = get_hulijilu(data_dir_hulijilu,data_type,data_nums,patient_zylsh)
    # 检验
    print('处理检验')
    data_dir_jianyan = os.path.join(data_dir,'jianyan.csv')
    res_jianyan = get_jianyan(data_dir_jianyan,data_type,data_nums,patient_zylsh)
    # 检查
    print('处理检查')
    data_dir_jiancha = os.path.join(data_dir,'jiancha.csv')
    res_jiancha = get_jiancha(data_dir_jiancha,data_type,data_nums,patient_zylsh)
    # 诊断
    print('处理诊断')
    data_dir_zhenduan = os.path.join(data_dir,'zhenduan.csv')
    res_zhenduan = get_zhenduan(data_dir_zhenduan,data_type,data_nums,patient_zylsh)
    print('处理体征')
    data_dir_tizheng = os.path.join(data_dir,'tizheng.csv')
    res_tizheng = get_tizheng(data_dir_tizheng,data_type,data_nums,patient_zylsh)
    print('合并成最终')
    # 合并成最终
    dfs = [res_bingli, res_yizhu , res_wenshu, res_hulijilu, res_jiancha, res_jianyan, res_zhenduan, res_tizheng]  
    # dfs = [res_bingli, res_yizhu , res_wenshu, res_hulijilu, res_jiancha, res_jianyan]  # ..., df3, df4, df5, df6
    merged_df = dfs[0]

    for i, df in enumerate(dfs[:],1):
        # 更新列名，为非流水号列加上后缀
        columns = df.columns.to_list()
        columns = ["zylsh"] + [col + f"_df{i}" for col in columns if col != "zylsh"]
        df.columns = columns

    for df in dfs[1:]:
        merged_df = merged_df.merge(df, on="zylsh", how="outer")
    # merged_df = merged_df[merged_df['结构化数据_df3'] != '[]']
        
    #########################################yc添加####################################################
    merged_df.iat[0,0] = zylsh
    # print(merged_df.iat[0,0],merged_df.iat[0,2])
    if merged_df.iat[0,2] == zylsh:
        merged_df.iat[0,2] = ''
    # print(merged_df.iat[0,0],merged_df.iat[0,2])
    #################################################################################################

    merged_df.shape
    merged_df.fillna('',inplace=True)


    for col in merged_df.columns[1:]:
        # print(merged_df)
        merged_df[col] = merged_df[col].apply(transfer_value)
    # 处理数据
    for i in range(merged_df.shape[0]):
        wenshu_list = merged_df.iat[i,5]
        for wenshu in wenshu_list:
            for key,content in wenshu['内容'].items():
                new_content = re.sub(r'(床号[:： ]{1,2})([\+0-9A-Za-z床]+) ',r'\1TM床号IDTM ',content)
                wenshu['内容'][key] = new_content

    for col in merged_df.columns[1:]:
        merged_df[col] = merged_df[col].apply(transfer_value_to_str)
    fake = Faker('zh')

    num_columns = merged_df.shape[1]
    for i in range(merged_df.shape[0]):
        zhuyuanhao = generate_random_zhuyuanhao()
        chuanghao = generate_random_chuanghao()
        p_name = generate_random_name(fake)
        for j in range(1,num_columns):
            ori_text = merged_df.iat[i,j]
            ori_text = ori_text.replace('TM住院号IDTM',zhuyuanhao)
            ori_text = ori_text.replace('TM床号IDTM',chuanghao)
            ori_text = ori_text.replace('TM患者名称TM',p_name)
            merged_df.iat[i,j] = ori_text
    merged_df.shape
    if out_dir != '':
        merged_df.to_csv(os.path.join(out_dir,'最终处理并合并后数据.csv'),header=None,index=None)
    # 复制一下 处理成json的时候会修改数据
    merged_df_copy = merged_df.copy()
    # ------------------------------------2.合并成大json---------------------------------------
    
    for col in merged_df.columns[1:]:
        merged_df[col] = merged_df[col].apply(transfer_value)
    json_datas = {}
    for i in range(merged_df.shape[0]):
        zylsh = merged_df.iat[i,0]
        # zylsh = new_zylsh

        # 病理：1，医嘱：3，文书：5，护理：7，检查：9，检验：11
        json_data = {}
        wenshu_list = merged_df.iat[i,5]
        for wenshu in wenshu_list:
            name = wenshu['文书名']
            # del wenshu['文书名']
            json_data[name] = wenshu
        for hulijilu in merged_df.iat[i,7]:
            if '出院小结' in hulijilu['护理记录名']:
                json_data['出院小结'] = hulijilu

        yizhu_list = merged_df.iat[i,3]
        for yizhu in yizhu_list:
            yizhu_items = yizhu['医嘱详情']
            for index,yizhu_item in enumerate(yizhu_items):
                yizhu_items[index] = list(yizhu_items[index].values())
        json_data['医嘱'] = yizhu_list

        bingli_list = merged_df.iat[i,1]
        for index,bingli in enumerate(bingli_list):
            bingli_list[index] = list(bingli_list[index].values())
        json_data['病理'] = bingli_list

        jiancha_list = merged_df.iat[i,9]
        for index,jiancha in enumerate(jiancha_list):
            jiancha_list[index] = list(jiancha_list[index].values())
        json_data['检查'] = jiancha_list

        jianyan_list = merged_df.iat[i,11]
        for jianyan in jianyan_list:
            jianyan_items = jianyan['检验详情']
            for index,jianyan_item in enumerate(jianyan_items):
                jianyan_items[index] = list(jianyan_items[index].values())
        json_data['检验'] = jianyan_list

        zhenduan_list = merged_df.iat[i,13]
        for index,zhenduan in enumerate(zhenduan_list):
            zhenduan_list[index] = list(zhenduan_list[index].values())
        json_data['诊断'] = zhenduan_list

        tizheng_list = merged_df.iat[i,15]
        for index,tizheng in enumerate(tizheng_list):
            tizheng.pop('住院流水号')
            tizheng_list[index] = list(tizheng.values())
        json_data['体征'] = tizheng_list

        json_datas[zylsh] = json_data
        if out_dir != '':
            with open(os.path.join(out_dir,'合并.json'),'w',encoding='utf8') as f:
                json.dump(json_datas,f,ensure_ascii=False,indent=4)

    # ------------------------------------3.额外处理一下一些key的问题---------------------------------------
    # 赋值还原回去
    merged_df = merged_df_copy
    for col in merged_df.columns[1:]:
        merged_df[col] = merged_df[col].apply(transfer_value)


    for i in range(merged_df.shape[0]):
        wenshu_list = merged_df.iat[i,5]
        for wenshu in wenshu_list:
            # 处理文本
            if wenshu['文书名'] in transfer_keys:
                final_json = wenshu['内容']
                processed_str = ''
                for key,value in final_json.items():
                    if key == '文本':
                        processed_str = processed_str + value
                    else:
                        processed_str = processed_str + key + ' ' + value
                processed_str = processed_str.strip()
                processed_str = re.sub(' +',' ',processed_str)
                wenshu['内容'] = {'文本':processed_str}
            text_json = wenshu['内容']
            update_keys = []
            update_keys_2 = []

            for key in text_json.keys():
                # 处理_1 _2的情况
                if end_with_underline(key):
    
                    update_keys.append((key,key[:-2]))
                # 第一个为句号。 的，就不统计了
                elif '。' in key.strip()[1:] or len(key)>50:
                    update_keys_2.append(key)

            if len(update_keys) != 0:
                for (ori_key,new_key) in update_keys:
                    text_json[new_key] = text_json[ori_key]
                    del text_json[ori_key]
            if len(update_keys_2) != 0:
                for ori_key in update_keys_2:
                    text_json['文本'] = ori_key.strip() + ' ' + text_json[ori_key].strip()
                    del text_json[ori_key]
    # 处理一下额外脱敏
    for i in range(merged_df.shape[0]):
        wenshu_list = merged_df.iat[i,5]
        for wenshu in wenshu_list:
            for key,text in wenshu['内容'].items():
                new_text = text
                for ori_content,new_content in tuomin_fixes:
                    new_text = new_text.replace(ori_content,new_content)
                wenshu['内容'][key] = new_text
        
        hulijilu_list = merged_df.iat[i,7]
        for hulijilu in hulijilu_list:
            if '出院小结' in hulijilu['护理记录名']:
                for key,text in hulijilu['内容'].items():
                    if isinstance(text,dict):
                        continue
                    new_text = text
                    for ori_content,new_content in tuomin_fixes:
                        new_text = new_text.replace(ori_content,new_content)
                    hulijilu['内容'][key] = new_text
                for key,text in hulijilu['内容']['基本信息'].items():
                    new_text = text
                    for ori_content,new_content in tuomin_fixes:
                        new_text = new_text.replace(ori_content,new_content)
                    hulijilu['内容']['基本信息'][key] = new_text
                for key,text in hulijilu['内容']['病人信息'].items():
                    new_text = text
                    for ori_content,new_content in tuomin_fixes:
                        new_text = new_text.replace(ori_content,new_content)
                    hulijilu['内容']['病人信息'][key] = new_text

    cyxjs = []
    for i in range(merged_df.shape[0]):
        zylsh = merged_df.iat[i,0]
        # zylsh = new_zylsh
        hulijilu_list = merged_df.iat[i,7]
        for hulijilu in hulijilu_list:
            if '出院小结' in hulijilu['护理记录名']:
                break
        ################################################################ yc添加
        if len(hulijilu_list) == 0 :
            cyxj = {}
        ################################################################
        elif '出院小结' not in hulijilu['护理记录名']:
            cyxj = {}
        else:
            cyxj = hulijilu['内容']
        cyxj = {
            zylsh:cyxj
        }
        cyxjs.append((zylsh,cyxj))
        
    for col in merged_df.columns[1:]:
        merged_df[col] = merged_df[col].apply(transfer_value_to_str)


    if out_dir != '':
        merged_df.to_csv(os.path.join(out_dir,'new_最终处理并合并后数据.csv'),header=None,index=None)


    return merged_df,json_datas,cyxjs


if __name__ == '__main__':
    print('处理源文件')
    data_dir = sys.argv[1]
    keshi = sys.argv[2]
    zylsh = sys.argv[3]
    out_dir = sys.argv[4]
    data_dir = os.path.join(data_dir,keshi)
    out_dir = os.path.join(out_dir,keshi)
    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    elif zylsh == '-2':
        # zylshs = np.loadtxt('新增源文件流水号.csv', delimiter=',',dtype=str)
        zylshs = np.loadtxt(f'./流水号/{keshi}_新增源文件流水号.csv', delimiter=',',dtype=str)
        zylshs = list(zylshs)
        # print(zylshs)
    else:
        zylshs = [zylsh]
    if len(zylshs) == 0:
        print('文件夹{}下没有文件，请检查！'.format(data_dir))


    print('处理{}个病例'.format(len(zylshs)))
    for zylsh in zylshs:
        now_data_dir = os.path.join(data_dir,zylsh)
        now_out_dir = os.path.join(out_dir,zylsh)
        merged_df,json_datas,cyxjs = process_and_merge(now_data_dir,now_out_dir)
        # for tmp_zylsh,cyxj in cyxjs:
        #     with open(os.path.join('/HL_user01/2024_03_24_生成出院小结_演示/演示/医生示例','{}.json'.format(tmp_zylsh)),'w') as f:
        #         json.dump(cyxj,f,indent=2,ensure_ascii=False)
