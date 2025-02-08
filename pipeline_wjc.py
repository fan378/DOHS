# 全部由模型生成
import os
import sys
import shutil
import numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM, AutoModel
import torch
import jsonlines
import global_variable
import json
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
# os.environ['CUDA_VISIBLE_DEVICES'] = '2'

def main(model,tokenizer,ins_datas,key_id,out_dir='全部由模型生成'):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    preds = {}
    print(key_id,'全部的指令数据条数:{}'.format(len(ins_datas)))


    ################################yc修改############################################
    # if os.path.exists(os.path.join(out_dir,'{}.json'.format(key_id))):
    #     with open(os.path.join(out_dir,'{}.json'.format(key_id)),'r',encoding='utf8') as f:
    #         preds = json.load(f)
    # else:
    #     preds = {
    #         key_id:{
    #             'output':{},
    #             'find_source':{}
    #         }
    #     }
    ###################################################################################

    for now_index,data in enumerate(ins_datas):
        zylsh = data['zylsh']

        if zylsh not in preds.keys():
            preds[zylsh] = {
                'output':{},
                'find_source':{}
            }

        #############################################################   yc添加   ###############################################
        # if data['key'] in preds[zylsh]['find_source'].keys():
        #     continue
        ########################################################################################################################

        data_key = data['key']
        print('***********************{}/{}模型正在生成字段:{}***********************'.format(now_index+1,len(ins_datas),data['key']))
        now_key = data['key']
        now_input = data['instruction']
        gold = data['output']
        if data_key == '住院期间医疗情况':
            res_json = {now_key:''}
            preds[zylsh]['output'].update(res_json)
            preds[zylsh]['find_source'][data_key] = now_input 
            continue
        if len(tokenizer.build_chat_input(data['instruction'])['input_ids'][0].tolist()) > 8000:
            print(len(tokenizer.build_chat_input(data['instruction'])['input_ids'][0].tolist()))
            res_json = {now_key:'输入数据过长，模型无法输出！'}
            print('当前数据{}字段生成过程中，输入过长，该字段无法正常输出'.format(data['key']))
        else:
            res,his = model.chat(tokenizer, now_input, history=[])
            if now_key == '患者基本信息':
                # 检查是否是json
                try:
                    res_json = {now_key:json.loads(res)}
                except:
                    # 多次尝试
                    for i in range(3):
                        print('患者基本信息生成：第{}次尝试'.format(i+1))
                        res,his = model.chat(tokenizer, now_input, history=[])
                        try:
                            res_json = {now_key:json.loads(res)}
                            # 成功转json后，break
                            break
                        except:
                            # 否则继续尝试生成
                            pass
                    # 多次后仍然无法生成
                    try:
                        res_json = {now_key:json.loads(res)}
                    except:
                        print('无法转json:{}'.format(res))
                        # 否则尝试转成json
                        res = res.strip()
                        if res[-1] == '}':
                            print('去掉最后的}，加上"}')
                            res = res[:-1]+'"}'
                        elif res[-1] == '\'' or res[-1] == '"':
                            print('最后是引号，直接加上大括号')
                            res = res + '}'
                        else:
                            print('直接加上引号与大括号')
                            res = res + '"}'
                    # 最后尝试转json
                    try:
                        res_json = {now_key:json.loads(res)}
                    except:
                        print('患者基本信息字段 输出错误')
                        res_json = {
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
            else:
                res_json = {now_key:res}
            # print(res)
            print('***********************{}/{}字段:{} 生成结束***********************'.format(now_index+1,len(ins_datas),data['key']))

        preds[zylsh]['output'].update(res_json)
        preds[zylsh]['find_source'][data_key] = now_input 
    
    with open(os.path.join(out_dir,'{}.json'.format(key_id)),'w',encoding='utf8') as f:
        json.dump(preds,f,indent=4,ensure_ascii=False)


if __name__ == '__main__':
    print('构造指令数据')
    data_dir = sys.argv[1]
    keshi = sys.argv[2]
    zylsh = sys.argv[3]
    out_dir = sys.argv[4]
    model_path = sys.argv[5]
    gpu = sys.argv[6]

    # show_dir = '/HL_user01/2024_03_24_生成出院小结_演示/演示/全部由模型生成'
    # 加载模型
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True, device=gpu)
    
    data_name = '出院小结及子字段.jsonl'
    data_dir = os.path.join(data_dir,keshi)
    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    elif zylsh == '-2':
        zylshs = np.loadtxt(f'./流水号/{keshi}_新增源文件流水号.csv', delimiter=',',dtype=str)
        zylshs = list(zylshs)
        # zylshs = zylshs[344:]
    else:
        zylshs = [zylsh]

    print('处理{}个病例'.format(len(zylshs)))
    for zylsh in zylshs:
        ins_data_path = os.path.join(data_dir,zylsh,data_name)
        with jsonlines.open(ins_data_path,'r') as f:
            datas = [line for line in f]
        now_out_dir = os.path.join(out_dir,keshi,zylsh)
        main(model,tokenizer,datas,zylsh,now_out_dir)
        # source = os.path.join(now_out_dir,'{}.json'.format(zylsh))
        # target = os.path.join(show_dir,'{}.json'.format(zylsh))
        # shutil.copy(source,target)

