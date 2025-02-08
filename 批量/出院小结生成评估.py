import sys
sys.path.append('../')
import jsonlines
import json
import os
import shutil
import json
import jsonlines
import os
from collections import defaultdict
from tqdm import tqdm
import re
import json
from rouge_chinese import Rouge
import jieba
import os
from tqdm import tqdm
import numpy as np


rouge = Rouge()
def get_scores(pred,gold):
    if pred.strip() == '' or gold.strip() == '':
        print('get score error! pred:{}\tgold:{}'.format(pred,gold))
        return 0
    hypothesis = ' '.join(jieba.cut(pred)) 
    reference = ' '.join(jieba.cut(gold))
    scores = rouge.get_scores(hypothesis, reference)
    return scores[-1]['rouge-l']['f']

# # 出院小结计算
# def cyxj_metrics_calc(pred_datas):
#     keys = [
#         '患者基本信息',
#         '入院时简要病史',
#         '体检摘要',
#         '住院期间医疗情况',
#         '出院诊断',
#         '病程与治疗情况', 
#         '出院时情况',
#         '出院后用药建议' 
#     ]
#     pred_datas_with_keys = {key:[] for key in keys}
#     for pred_data in pred_datas:
#         key = pred_data['key']
#         pred_datas_with_keys[key].append(pred_data)
#     all_metrics = {}
    
#     # 一个一个算
#     key = '患者基本信息'
#     now_pred_datas = pred_datas_with_keys[key]
#     # 格式正确
#     dict_corr = 0
#     all_nums = 0
#     # key,value正确
#     all_keys = 0
#     corr_keys = 0
#     errors = []
#     format_errors = []
#     # 患者基本信息字段，采用 acc
#     for index,pred_data in enumerate(now_pred_datas):
#         # try:
#         pred = pred_data['pred'].strip()
        
#         gold = pred_data['output'].strip()
#         # 
#         gold_dict = json.loads(gold)
#         # for key in gold_dict.keys():
#         #     if key == '入院时间':
#         #         gold_dict[key] = gold_dict[key][0][:10]
#         #     elif key == '出院时间':
#         #         gold_dict[key] = gold_dict[key][0][:10]
#         gold_dict = {k:v.replace(' ','') for k,v in gold_dict.items()}
#         pred_dict = json.loads(pred)
#         # for key in pred_dict.keys():
#         #     if key == '入院时间':
#         #         pred_dict[key] = pred_dict[key][0][:10]
#         #     elif key == '出院时间':
#         #         pred_dict[key] = pred_dict[key][0][:10]
#         pred_dict = {k:v.replace(' ','') for k,v in pred_dict.items()}
#         dict_corr += 1
#         preds = set(tuple(pred_dict.items()))
#         golds = set(tuple(gold_dict.items()))
#         all_keys += len(golds)
#         commons = preds & golds
#         corr_keys += len(commons)
#         error_keys = list(preds - golds)
#         for error_key in error_keys:
#             errors.append(pred_data)
#         # except:
#         #     format_errors.append(pred_data)
#         all_nums += 1
#     # 存储的指标是，格式正确的（样本）即能转换为json的样本，key_value正确的字段（以字段为单位）
#     all_metrics['患者基本信息'] = (dict_corr,all_nums,corr_keys,all_keys,errors,format_errors)
#     print('{} finish'.format(key))
#     # 其他字段，都采用rougel
#     keys = ['住院期间医疗情况', '出院诊断', '病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']
#     infos_dict = {}
#     for key in keys:
#         all_scores = []
#         need_datas = pred_datas_with_keys[key]
#         for index,data in tqdm(enumerate(need_datas)):
#             # 每一条，计算 预测 和 黄金 之间的rouge
#             score = get_scores(data['pred'].strip(),data['output'].strip())
            
#             all_scores.append(score)
#         mean_score = np.mean(all_scores)
#         errors = []
#         for index,score in enumerate(all_scores):
#             if score < mean_score:
#                 errors.append(need_datas[index])


#         # 最终返回的: 每条句子的rouge，平均rouge, 低于平均分的样本
#         all_metrics[key] = (all_scores,mean_score,errors)
#         print('{} finish'.format(key))
#     return all_metrics


# 出院小结计算
def cyxj_metrics_calc(pred_datas):
    keys = [
        '患者基本信息',
        '入院时简要病史',
        '体检摘要',
        '住院期间医疗情况',
        '出院诊断',
        '病程与治疗情况', 
        '出院时情况',
        '出院后用药建议' 
    ]
    pred_datas_with_keys = {key:[] for key in keys}
    for pred_data in pred_datas:
        key = pred_data['key']
        pred_datas_with_keys[key].append(pred_data)
    all_metrics = {}

    # 一个一个算
    key = '患者基本信息'
    now_pred_datas = pred_datas_with_keys[key]
    # 格式正确
    dict_corr = 0
    all_nums = 0
    # key,value正确
    all_keys = 0
    corr_keys = 0
    errors = []
    format_errors = []
    # 患者基本信息字段，采用 acc
    for index,pred_data in enumerate(now_pred_datas):
        try:
            pred = pred_data['pred'].strip()
            gold = pred_data['output'].strip()
            gold_dict = json.loads(gold)
            # for key in gold_dict.keys():
            #     if key == '入院时间':
            #         gold_dict[key] = gold_dict[key][0][:10]
            #     elif key == '出院时间':
            #         gold_dict[key] = gold_dict[key][0][:10]
            gold_dict = {k:v.replace(' ','') for k,v in gold_dict.items()}
            pred_dict = json.loads(pred)
            # for key in pred_dict.keys():
            #     if key == '入院时间':
            #         pred_dict[key] = pred_dict[key][0][:10]
            #     elif key == '出院时间':
            #         pred_dict[key] = pred_dict[key][0][:10]
            pred_dict = {k:v.replace(' ','') for k,v in pred_dict.items()}
            dict_corr += 1
            preds = set(tuple(pred_dict.items()))
            golds = set(tuple(gold_dict.items()))
            all_keys += len(golds)
            commons = preds & golds
            corr_keys += len(commons)
            error_keys = list(preds - golds)
            for error_key in error_keys:
                errors.append(pred_data)
        except:
            format_errors.append(pred_data)
        all_nums += 1
    # 存储的指标是，格式正确的（样本）即能转换为json的样本，key_value正确的字段（以字段为单位）
    all_metrics['患者基本信息'] = (dict_corr,all_nums,corr_keys,all_keys,errors,format_errors)
    print('{} finish'.format(key))
    # 其他字段，都采用rougel
    keys = ['住院期间医疗情况', '出院诊断', '病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']
    infos_dict = {}
    for key in keys:
        all_scores = []
        need_datas = pred_datas_with_keys[key]
        for index,data in tqdm(enumerate(need_datas)):
            # 每一条，计算 预测 和 黄金 之间的rouge
            if data['output'].strip()=="over_length":
                continue
            score = get_scores(data['output'].strip(),data['ground-truth'].strip())
            
            all_scores.append(score)
        mean_score = np.mean(all_scores)
        errors = []
        for index,score in enumerate(all_scores):
            if score < mean_score:
                errors.append(need_datas[index])


        # 最终返回的: 每条句子的rouge，平均rouge, 低于平均分的样本
        all_metrics[key] = (all_scores,mean_score,errors)
        print('{} finish'.format(key))
    return all_metrics

metrics_func = {
    '出院小结及子字段':cyxj_metrics_calc,
    # '猜测字段':cczd_metrics_calc,
    # '格式化': gsh_metrics_calc,
    # '科室导诊': ksdz_metrics_calc,
    # '指标检测': zbjc_metrics_calc,
    # '指标提取': zbtq_metrics_calc
}

# tasks = ['出院小结及子字段','猜测字段','格式化','科室导诊','指标检测','指标提取']
# pred_dir = '/HL_user01/lyh/评估/模型预测结果/xiaoerke_chatglm3_0706/medical/emr|-1|0|07-08-00-47-21/'
tasks = ['出院小结及子字段']
pred_dir = '/HL_user01/yc_ruxianwaike_test/2024.5.31出院小结完整演示/批量数据_instructions_202407_全科室模型'
# tasks = ['出院小结及子字段']
# pred_dir = '/HL_user01/lyh/评估/模型预测结果/xiaoerke_chatglm3_0707_wjc/medical/emr|-1|0|07-09-04-20-35'

pred_keshis = os.listdir(pred_dir)

keshis = sorted(list(pred_keshis))
print('数据包含的科室:{}'.format(keshis))

final_metrics = {t:{} for t in tasks}
for task in tasks:
    print('现在处理的任务是:{}'.format(task))
    for keshi in keshis:
        print('科室:{}'.format(keshi))

        pred_path = os.path.join(pred_dir,keshi,'{}_test_ours.jsonl'.format(task))
        if not os.path.exists(pred_path):
            print('不存在文件:{}'.format(pred_path))
        else:
            with jsonlines.open(pred_path,'r') as f:
                pred_datas = [data for data in f]
            # print('输出时长:{}秒'.format(round(float(pred_datas[-1]['cost_time']))))
            pred_datas = pred_datas[:-1]
            final_metrics[task][keshi] = metrics_func[task](pred_datas)

# print(final_metrics['出院小结及子字段']['xiaoerke']['患者基本信息'])

task = '出院小结及子字段'

keys = ['住院期间医疗情况', '出院诊断', '病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']

jbxx_met_list = []
cyxj_met_list = [[] for key in keys]

for keshi in final_metrics[task].keys():
    keshi_metrics = final_metrics[task][keshi]

    jbxx_met = keshi_metrics['患者基本信息']
    # with open("./error.txt","w", encoding="utf-8") as f:
    #     f.write(str(jbxx_met))
    jbxx_met_list.append((jbxx_met[2], jbxx_met[3]))
    
    for index, key in enumerate(keys):
        cyxj_met_list[index].extend(keshi_metrics[key][0])
print('\n')
print('患者基本信息')
corr_num = 0
all_num = 0
for c_num, a_num in jbxx_met_list:
    corr_num += c_num
    all_num += a_num

if all_num > 0:
    print(round(corr_num / all_num * 100, 2))
else:
    print("No data available for '患者基本信息'")

all_score_list = []
for index, key in enumerate(keys):
    print(key)
    score_list = cyxj_met_list[index]
    if len(score_list) > 0:
        now_score = sum(score_list) / len(score_list)
        print(round(now_score * 100, 2))
        all_score_list.append(now_score)
    else:
        print("No data available for '{}'".format(key))
        all_score_list.append(0)

if len(all_score_list) > 0:
    avg_score = sum(all_score_list) / len(all_score_list)
    print('avg:{}'.format(round(avg_score * 100, 2)))
else:
    print("No data available to calculate average score")