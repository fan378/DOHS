import os
import sys
from transformers import AutoTokenizer,AutoModelForCausalLM
import torch
import global_variable
import json

def main(model,tokenizer,ins_datas_v1201,key_id):
    preds = {key_id:{}}
    for data in ins_datas_v1201:
        now_input = data['instruction']
        gold = data['output']
        res,his = model.chat(tokenizer, now_input, history=[], max_new_tokens=8192)
        # print(now_input,res)
        preds[key_id].update(json.loads(res))
    with open('演示示例/简单字段'+key_id+'.json','w',encoding='utf8') as f:
        json.dump(preds,f,indent=4,ensure_ascii=False)