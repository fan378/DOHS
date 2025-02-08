# 全部由模型生成
import os
import sys
import shutil
import numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM, AutoModel
import jsonlines
from tqdm import tqdm
import json
# os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
# os.environ['CUDA_VISIBLE_DEVICES'] = '2'

def process_jsonlines(model,tokenizer,data_dir,out_dir,start_num = 0,end_num = -1):
    datas = []
    with open(data_dir,'r',encoding='utf8') as f:
        lines = f.readlines()
        if start_num != 0 :
            start_num = start_num *6
        if end_num != -1 :
            end_num = end_num *6
        for line in tqdm(lines[start_num:end_num]):
            # print(line)
            line = json.loads(line)
            now_input = line['instruction']
            inputs = tokenizer.build_chat_input(now_input, history=[], role='user')['input_ids'].size()
            if inputs[1] > 8192:
                line['ground-truth'] = line['output'] 
                line['output'] = 'over_length'
                datas.append(line)
                continue
            # print(line['zylsh'],inputs)
            line['ground-truth'] = line['output'] 
            line['output'] = ''
            res,his = model.chat(tokenizer, now_input, history=[], max_length=8192)
            # 判断患者信息能否json化
            if line['key'] == '患者基本信息':
                # 检查是否是json
                now_key = line['key']
                now_output =  res
                try:
                    now_output_json = {now_key:json.loads(now_output)}
                except:
                    # 多次尝试
                    for i in range(3):
                        print('患者基本信息生成：第{}次尝试'.format(i+1))
                        res,his = model.chat(tokenizer, now_input, history=[])
                        now_output =  res
                        try:
                            now_output_json = {now_key:json.loads(now_output)}
                            # 成功转json后，break
                            break
                        except:
                            # 否则继续尝试生成
                            pass
                    # 多次后仍然无法生成
                    try:
                        now_output_json = {now_key:json.loads(now_output)}
                    except:
                        # print('无法转json:{}'.format(now_output))
                        # 否则尝试转成json
                        now_output = now_output.strip()
                        if now_output[-1] == '}':
                            # print('去掉最后的}，加上"}')
                            now_output = now_output[:-1]+'"}'
                        elif now_output[-1] == '\'' or now_output[-1] == '"':
                            # print('最后是引号，直接加上大括号')
                            now_output = now_output + '}'
                        else:
                            # print('直接加上引号与大括号')
                            now_output = now_output + '"}'
                    # 最后尝试转json
                    try:
                        now_output_json = {now_key:json.loads(now_output)}
                    except:
                        # print('患者基本信息字段 输出错误')
                        now_output_json = {
                            "患者基本信息": {
                                "住院号": "error",
                                "床号": "error",
                                "入院时间": "error",
                                "出院时间": "error",
                                "科别": "error",
                                "科室": "error",
                                "姓名": "error",
                                "年龄": "error",
                                "性别": "error",
                                "低压(BP低)": "error",
                                "高压(BP高)": "error",
                                "脉搏(P)": "error",
                                "呼吸(R)": "error",
                                "体温(T)": "error",
                                "入院诊断": "error",
                                "入院时简要病史": "error",
                                "体检摘要": "error"
                            }
                        }
            line['output'] = res
            datas.append(line)
    with jsonlines.open(out_dir,'w') as f:
        for line in datas:
            f.write(line)

# 后处理
from copy import deepcopy
from commons.constants import *

def read_josnlines(pred_path):
    with jsonlines.open(pred_path,'r') as f:
        datas = [data for data in f]
    return datas

def save_jsonlines(save_path,datas):
    with jsonlines.open(save_path,'w') as f:
        for line in datas:
            f.write(line)

def save_json(save_path,data,indent=2):
    with open(save_path,'w') as f:
        json.dump(data,f,indent =indent, ensure_ascii=False)

def read_json(read_path):
    with open(read_path,'r') as f:
        content = json.load(f)
    return content

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
    # "入院时简要病史": "入院时简要病史",
    # "体检摘要": "体检摘要",
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

def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

def update_formats_with_ori_data(formats, ori_datas):
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
            "入院时简要病史": "over_length",
            "体检摘要": "over_length"
        }
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

def postprocess(key_id,keshi):
    data_dir=f'./model_generated/{keshi}'
    input_file = os.path.join(data_dir,key_id,'{}.json'.format(key_id))

    with open(input_file, 'r',encoding='utf8') as f:
        datas = json.load(f)

    # output取output字段，溯源取source字段
    zylshs = list(datas.keys())
    # os.remove(os.path.join(data_dir,'{}.json'.format(key_id)))
    for zylsh in zylshs:
        data_save_dir = os.path.join(data_dir,zylsh)
        if not os.path.exists(data_save_dir):
            os.makedirs(data_save_dir)
        save_json(os.path.join(data_save_dir,'{}.json'.format(zylsh)),{zylsh:datas[zylsh]})
        data = datas[zylsh]

        data_output = data['output']
        data_source = {
            zylsh:data['find_source']
        }

        # 处理成医院格式
        processed_data = deepcopy(formats)
        update_formats_with_ori_data(processed_data,data_output)
            
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
    out_dir = sys.argv[2]
    keshi = sys.argv[3]
    model_path = sys.argv[4]
    gpu = sys.argv[5]
    start_num = int(sys.argv[6])
    end_num = int(sys.argv[7])

    # show_dir = '/HL_user01/2024_03_24_生成出院小结_演示/演示/全部由模型生成'
    # 加载模型
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True, device=gpu)
    
    data_name = '出院小结及子字段.jsonl'

    ins_data_path = os.path.join(data_dir,keshi,data_name)
    now_out_dir = os.path.join(out_dir,keshi,data_name)
    process_jsonlines(model,tokenizer,ins_data_path,out_dir,start_num = start_num,end_num = start_num)
        # source = os.path.join(now_out_dir,'{}.json'.format(zylsh))
        # target = os.path.join(show_dir,'{}.json'.format(zylsh))
        # shutil.copy(source,target)

