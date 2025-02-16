import sys
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
cons_keshis = ['yanke', 'zhongyike', 'neifenmi', 'xiaohuaneike', 'huxineike', 'shenjingneike', 'shenzangneike', 'ruxianwaike', 'fuke', 'jiazhuangxianxueguanwaike', 'zhongliuke', 'erbihouke', 'shenjingwaike', 'xiaoerke', 'weichangwaike']
cons_chinese_keshis = {
    'yanke':'眼科',
    'zhongyike':'中医科',
    'neifenmi':'内分泌',
    'xiaohuaneike':'消化内科',
    'huxineike':'呼吸内科',
    'shenjingneike':'神经内科',
    'shenzangneike':'肾脏内科',
    'ruxianwaike':'乳腺外科',
    'fuke':'妇科',
    'jiazhuangxianxueguanwaike':'甲状腺血管外科',
    'zhongliuke':'肿瘤科',
    'erbihouke':'耳鼻喉科',
    'shenjingwaike':'神经外科',
    'xiaoerke':'小儿科',
    'weichangwaike':'胃肠外科',
}
rouge = Rouge()

def get_scores(pred,gold):
    if pred.strip() == '' or gold.strip() == '':
        print('get score error! pred:{}\tgold:{}'.format(pred,gold))
        return 0
    hypothesis = ' '.join(jieba.cut(pred)) 
    reference = ' '.join(jieba.cut(gold))
    scores = rouge.get_scores(hypothesis, reference)
    return scores[-1]['rouge-l']['f']
punctuation_map = {
    "，": ",", 
    "。": ".", 
    "！": "!", 
    "？": "?",
    "：": ":", 
    "；": ";", 
    "“": "\"", 
    "”": "\"",
    "‘": "'", 
    "’": "'", 
    "（": "(", 
    "）": ")",
    "【": "[", 
    "】": "]", 
    "《": "<", 
    "》": ">",
    ' ':''
}

# 转换函数
def translate_punctuation(text):
    translator = str.maketrans(punctuation_map)
    return text.translate(translator)

re_comp = re.compile(r'【.*?】([^【]*)')
re_date = re.compile(r'\d{4}-\d{1,2}-\d{1,2}')
re_chinese = re.compile(r'[\u4e00-\u9fff]')
re_cankaozhi = re.compile(r'\(.*?\)')
def contains_chinese(text):
    return re_chinese.search(text) is not None
def is_val(text):
    '''
    函数判断是不是指标的数值
    '''
    # 不包含中文，肯定是val
    nums = ['0','1','2','3','4','5','6','7','8','9']
    # if not contains_chinese(text[0]):
    #     return True
    if text[0] in nums:
        return True
    if '阴性' in text or '阳性' in text:
        return True
    return False
def extract_tuples(raw_text):
    raw_text = re_cankaozhi.sub('',raw_text)
    date_clear = re_date.sub('',raw_text)
    texts = re_comp.findall(date_clear)
    if len(texts) == 0:
        texts = [raw_text]
    texts = [text.replace('：','').replace('。','').replace('，',' ').replace('↑','').replace('↓','').replace('；','').replace('','').strip() for text in texts]
    res = []
    for text in texts:
        if ' ' in text:
            text_splits = text.split()
            index = 0
            while index< len(text_splits):
                # 最后一个
                if index + 1 == len(text_splits):
                    merge_text = text_splits[index].replace(' ','')
                    if merge_text != '':
                        res.append(merge_text)
                    index += 1
                    break
                now_text = text_splits[index].strip()
                next_text = text_splits[index+1].strip()
                if is_val(next_text):
                    res.append(str(now_text)+str(next_text))
                    index += 2
                else:
                    if '常规' in now_text or '生化' in now_text:
                        pass
                    else:
                        if now_text != '':
                            res.append(now_text)
                    index += 1

        else:
            if text != '':
                res.append(text)

    return res


# 出院小结计算
def cyxj_metrics_calc(pred_datas):
    keys = [
        '患者基本信息',
        '住院期间医疗情况',
        '出院诊断',
        '病程与治疗情况', 
        '出院后用药建议', 
        '出院时情况'
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
            gold_dict = {k:translate_punctuation(v) for k,v in gold_dict.items()}
            pred_dict = json.loads(pred)
            pred_dict = {k:translate_punctuation(v) for k,v in pred_dict.items()}
            for key in gold_dict.keys():
                if key == '入院时间':
                    gold_dict[key] = gold_dict[key][0][:10]
                elif key == '出院时间':
                    gold_dict[key] = gold_dict[key][0][:10]
            gold_dict = {k:v.replace(' ','') for k,v in gold_dict.items()}
            for key in pred_dict.keys():
                if key == '入院时间':
                    pred_dict[key] = pred_dict[key][0][:10]
                elif key == '出院时间':
                    pred_dict[key] = pred_dict[key][0][:10]
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

    # # 一个一个算
    # key = '出院诊断'
    # now_pred_datas = pred_datas_with_keys[key]
    # # 格式正确
    # dict_corr = 0
    # all_nums = 0
    # # key,value正确
    # all_keys = 0
    # corr_keys = 0
    # errors = []
    # format_errors = []
    # # 患者基本信息字段，采用 acc
    # for index,pred_data in enumerate(now_pred_datas):
    #     try:
    #         pred = pred_data['pred'].strip()
    #         gold = pred_data['output'].strip()
    #         pred = translate_punctuation(pred)
    #         gold = translate_punctuation(gold)
    #         dict_corr += 1
    #         preds = set(pred)
    #         golds = set(gold)
    #         all_keys += len(golds)
    #         commons = preds & golds
    #         corr_keys += len(commons)
    #         error_keys = list(preds - golds)
    #         for error_key in error_keys:
    #             errors.append(pred_data)
    #     except:
    #         format_errors.append(pred_data)
    #     all_nums += 1
    # # 存储的指标是，格式正确的（样本）即能转换为json的样本，key_value正确的字段（以字段为单位）
    # all_metrics['出院诊断'] = (dict_corr,all_nums,corr_keys,all_keys,errors,format_errors)
    # print('{} finish'.format(key))

    # 其他字段，都采用rougel
    keys = ['住院期间医疗情况', '出院诊断', '病程与治疗情况', '出院后用药建议', '出院时情况']
    # keys = ['住院期间医疗情况','病程与治疗情况', '出院后用药建议', '出院时情况']
    infos_dict = {}
    for key in keys:
        all_scores = []
        need_datas = pred_datas_with_keys[key]
        for index,data in tqdm(enumerate(need_datas)):
            # 每一条，计算 预测 和 黄金 之间的rouge
            score = get_scores(data['pred'].strip(),data['output'].strip())
            
            all_scores.append(score)
        mean_score = np.mean(all_scores)
        errors = []
        for index,score in enumerate(all_scores):
            if score < mean_score:
                errors.append(need_datas[index])


        # 最终返回的: 每条句子的rouge，平均rouge, 低于平均分的样本
        all_metrics[key] = (all_scores,mean_score,errors)
        print('{} finish'.format(key))


    key = '住院期间医疗情况'
    all_num = 0
    correct_num = 0
    pred_num = 0
    need_datas = pred_datas_with_keys[key]
    for index,data in tqdm(enumerate(need_datas)):
        # 每一条，计算 预测 和 黄金 之间的rouge
        pred = data['pred']
        gold = data['output']
        pred_tuples = set(extract_tuples(pred))
        gold_tuples = set(extract_tuples(gold))
        print(pred_tuples,gold_tuples)
        all_num += len(gold_tuples)
        pred_num += len(pred_tuples)
        correct_num += len(pred_tuples & gold_tuples)

    all_metrics['住院期间医疗情况_2'] = (correct_num,pred_num,all_num)

    return all_metrics

# 猜测字段计算
def cczd_metrics_calc(pred_datas):
    samples = 0
    # 总体情况
    overall_nums = 0
    overall_corr_nums = 0
    # 针对否定
    negative_nums = 0
    negative_corr_nums = 0
    negative_errors = []
    # 正常情况
    normal_nums = 0
    normal_corr_nums = 0
    normal_errors = []
    # 正则提取答案
    answer_re = re.compile(r"“(.*?)”")
    for pred_data in pred_datas:
        pred_data.pop('prompt')
        
        # 提取答案
        pred_answers = answer_re.findall(pred_data['pred'])
        # 答案是否为否定（如果正则识别到的为空，则认为是否定）
        pred_is_neg = len(pred_answers) == 0
        if pred_data['答案'][0] == "否定":
            # 否定判断
            negative_nums += 1
            if pred_is_neg:
                negative_corr_nums += 1
                overall_corr_nums += 1
            else:
                negative_errors.append(pred_data)


        else:
            # 正常判断
            normal_nums += len(pred_data['答案'])
            corr_keys = set(pred_data['答案']) & set(pred_answers)
            overall_corr_nums += len(corr_keys)
            normal_corr_nums += len(corr_keys)
            if len(pred_data['答案']) != len(corr_keys):
                normal_errors.append(pred_data)

        overall_nums += len(pred_data['答案'])
        samples += 1
    return (
        samples,
        overall_nums,overall_corr_nums,
        negative_nums,negative_corr_nums,negative_errors,
        normal_nums,normal_corr_nums,normal_errors,
        )
# 格式化 计算
def process_json(data):
    '''
    因为 value是list的话，无法直接比较，转为str
    '''
    for key in data.keys():
        if isinstance(data[key],list):
            details = []
            for detail in data[key]:
                details.append('_'.join(['{}:{}'.format(k,str(detail[k]).replace(' ','')) for k in sorted(detail.keys())]))
            data[key] = '||'.join(sorted(details))
        else:
            data[key] = str(data[key]).replace(' ','')
    return data
            

def gsh_metrics_calc(pred_datas):
    # 参考 出院小结---患者基本信息 计算方法
    # 格式正确
    dict_corr = 0
    all_nums = 0
    # key,value正确
    all_keys = 0
    corr_keys = 0
    errors = []
    format_errors = []
    # 患者基本信息字段，采用 acc
    for index,pred_data in enumerate(pred_datas):
        try:
            pred_data.pop('prompt')
            pred = pred_data['pred'].strip()
            gold = pred_data['output'].strip()
            gold_dict = json.loads(gold)
            gold_dict = process_json(gold_dict)
            pred_dict = json.loads(pred)
            pred_dict = process_json(pred_dict)
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
    return (dict_corr,all_nums,corr_keys,all_keys,format_errors,errors)
# 科室导诊 计算
def ksdz_metrics_calc(pred_datas):
    chinese_keshis = [cons_chinese_keshis[keshi] for keshi in cons_keshis]
    samples = 0
    # 总体情况
    overall_nums = 0
    overall_corr_nums = 0
    # 针对否定
    negative_nums = 0
    negative_corr_nums = 0
    negative_errors = []
    # 正常情况
    normal_nums = 0
    normal_corr_nums = 0
    normal_errors = []
    for pred_data in pred_datas:
        pred_data.pop('prompt')
        pred_txt = pred_data['pred']
        gold_txt = pred_data['output']

        gold_answers = []
        pred_answers = []

        for chinese_keshi in chinese_keshis:
            if chinese_keshi in pred_txt:
                pred_answers.append(chinese_keshi)
            if chinese_keshi in gold_txt:
                gold_answers.append(chinese_keshi)

        # 答案是否为否定（如果正则识别到的为空，则认为是否定）
        pred_is_neg = len(pred_answers) == 0
        if len(gold_answers) == 0:
            # 否定判断
            negative_nums += 1
            if pred_is_neg:
                negative_corr_nums += 1
                overall_corr_nums += 1
            else:
                negative_errors.append(pred_data)

            overall_nums += 1


        else:
            # 正常判断
            normal_nums += len(gold_answers)
            corr_keys = set(gold_answers) & set(pred_answers)
            overall_corr_nums += len(corr_keys)
            normal_corr_nums += len(corr_keys)
            if len(gold_answers) != len(corr_keys):
                normal_errors.append(pred_data)

            overall_nums += len(gold_answers)
        samples += 1
    return (
        samples,
        overall_nums,overall_corr_nums,
        negative_nums,negative_corr_nums,negative_errors,
        normal_nums,normal_corr_nums,normal_errors,
        )
# 指标检测 计算
def zbjc_metrics_calc(pred_datas):
    samples = 0
    # 总体情况
    overall_nums = 0
    overall_corr_nums = 0
    # 针对否定
    negative_nums = 0
    negative_corr_nums = 0
    negative_errors = []
    # 正常情况
    normal_nums = 0
    normal_corr_nums = 0
    normal_errors = []
    # 正则提取答案
    answer_re = re.compile(r"在(.*?)进行的(.*?)检验存在数据不一致，医疗文本中记录的结果为(.*?)，而实际检验结果为(.*?)。")
    for pred_data in pred_datas:
        pred_data.pop('prompt')
        
        # 提取答案
        pred_answers = answer_re.findall(pred_data['pred'])
        gold_answers = answer_re.findall(pred_data['output'])
        # 答案是否为否定（如果正则识别到的为空，则认为是否定）
        pred_is_neg = len(pred_answers) == 0
        if len(gold_answers) == 0:
            # 否定判断
            negative_nums += 1
            overall_nums += 1
            if pred_is_neg:
                negative_corr_nums += 1
                overall_corr_nums += 1
            else:
                negative_errors.append(pred_data)


        else:
            # 正常判断
            normal_nums += len(gold_answers)
            corr_keys = set(gold_answers) & set(pred_answers)
            overall_corr_nums += len(corr_keys)
            normal_corr_nums += len(corr_keys)
            assert len(gold_answers) >= len(corr_keys),print('preds:{}\tgolds:{}'.format(pred_answers,gold_answers))
            if len(gold_answers) != len(corr_keys):
                normal_errors.append(pred_data)
            overall_nums += len(gold_answers)
        samples += 1
    return (
        samples,
        overall_nums,overall_corr_nums,
        negative_nums,negative_corr_nums,negative_errors,
        normal_nums,normal_corr_nums,normal_errors,
        )
# 指标提取 计算
def transfer_data(data):
    '''
    把检验数据转换
    '''
    if '详情' in data.keys():
        details = []
        for detail in data['详情']:
            details.append('_'.join(['{}:{}'.format(k,detail[k]) for k in sorted(detail.keys())]))
        data['详情'] = '||'.join(sorted(details))
    return '**'.join('{}:{}'.format(k,data[k]) for k in sorted(data.keys()))
    
def zbtq_metrics_calc(pred_datas):
    # 参考 出院小结---患者基本信息 计算方法
    # 格式正确
    dict_corr = 0
    all_nums = 0
    # key,value正确
    all_keys = 0
    corr_keys = 0 
    # 患者基本信息字段，采用 acc
    format_errors = []
    errors = []
    for index,pred_data in enumerate(pred_datas):
        try:
            pred_data.pop('prompt')
            pred = pred_data['pred'].strip()
            gold = pred_data['output'].strip()
  
            if '{' in pred_data['output']:
                gold_not_find = False
                gold_dict = json.loads(gold)
            else:
                gold_not_find = True
                gold_dict = [{'答案':'没找到'}]
            if '{' in pred_data['pred']:
                pred_not_find = False
                pred_dict = json.loads(pred)                
            else:
                pred_not_find = True
                pred_dict = [{'答案':'没找到'}]

            dict_corr += 1
            preds = set([transfer_data(a) for a in pred_dict])
            golds = set([transfer_data(a) for a in gold_dict])

            all_keys += len(golds)
            commons = preds & golds
            corr_keys += len(commons)
            assert len(golds) >= len(commons),print('preds:{}\tgolds:{}'.format(preds,golds))
            error_keys = list(preds - golds)
            for error_key in error_keys:
                errors.append(pred_data)
        except:
            format_errors.append(pred_data)
        all_nums += 1
    assert all_keys >= corr_keys
    return (dict_corr,all_nums,corr_keys,all_keys,format_errors,errors)

metrics_func = {
    '出院小结及子字段':cyxj_metrics_calc,
    '猜测字段':cczd_metrics_calc,
    '格式化': gsh_metrics_calc,
    '科室导诊': ksdz_metrics_calc,
    '指标检测': zbjc_metrics_calc,
    '指标提取': zbtq_metrics_calc
}
# tasks = ['出院小结及子字段','猜测字段','格式化','科室导诊','指标检测','指标提取']
# pred_dirs = [
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_1',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_2',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_3',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_4',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_5',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_6',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_7',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_8',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_9',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_10',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_11',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_12',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_13',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_14',
#     '/HL_user01/0726_wjc_upload/每个科室单独的指标/2_emr_15',
# ]

tasks = ['出院小结及子字段']
pred_dirs = [
    '/HL_user01/yc_ruxianwaike_test/2024_5_31出院小结完整演示_wjc版/评估/2_emr_6'
]


from datetime import datetime, timedelta
from tqdm import tqdm
import time
def get_time(fmt='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时间，并增加8小时
    """
    # 获取当前时间
    ts = time.time()
    current_time = datetime.fromtimestamp(ts)

    # 增加8小时
    adjusted_time = current_time + timedelta(hours=12)

    # 格式化时间
    return adjusted_time.strftime(fmt)
out_time = get_time('%m-%d-%H-%M-%S')
print('out_time:{}'.format(out_time))
with open('emr评估_{}.txt'.format(out_time),'w') as fw:
    for pred_dir in tqdm(pred_dirs):
        pred_keshis = os.listdir(pred_dir)
        keshis = sorted(list(pred_keshis))
        fw.write('文件路径:{}\n'.format(pred_dir))
        fw.write('数据包含的科室:{}\n'.format(keshis))
        # print('数据包含的科室:{}'.format(keshis))
        final_metrics = {t:{} for t in tasks}
        for task in tasks:
            # print('现在处理的任务是:{}'.format(task))
            for keshi in keshis:
                # print('科室:{}'.format(keshi))

                pred_path = os.path.join(pred_dir,keshi,'{}_test'.format(task),'preds.json')
                if not os.path.exists(pred_path):
                    print('不存在文件:{}'.format(pred_path))
                else:
                    pred_datas = []
                    with jsonlines.open(pred_path,'r') as f:
                        for data in f:
                            if 'output' in data.keys() and len(data['output']) < 10:
                                continue
                            pred_datas.append(data)
                    # print('输出时长:{}秒'.format(round(float(pred_datas[-1]['cost_time']))))
                    pred_datas = pred_datas[:-1]
                    final_metrics[task][keshi] = metrics_func[task](pred_datas)
        # print(pred_dir)
        task = '出院小结及子字段'

        keys = ['住院期间医疗情况', '出院诊断', '病程与治疗情况', '出院后用药建议', '出院时情况']
        # keys = ['住院期间医疗情况', '病程与治疗情况', '出院后用药建议', '出院时情况']


        jbxx_met_list = []
        cyxj_met_list = [[] for key in keys]
        for keshi in final_metrics[task].keys():
            keshi_metrics = final_metrics[task][keshi]

            jbxx_met = keshi_metrics['患者基本信息']
            with open(f"./error/{keshi}_error.txt","w", encoding="utf-8") as f:
                f.write(str(jbxx_met))    
            jbxx_met_list.append((jbxx_met[2],jbxx_met[3]))

            for index,key in enumerate(keys):
                cyxj_met_list[index].extend(keshi_metrics[key][0])

        # print('患者基本信息')
        corr_num = 0
        all_num = 0
        for c_num,a_num in jbxx_met_list:
            corr_num += c_num
            all_num += a_num
        try:
            met = round(corr_num/all_num*100,2)
        except:
            met = 0
        fw.write('患者基本信息\n')
        fw.write('{}\n'.format(met))

        jbxx_met_list = []
        cyxj_met_list = [[] for key in keys]
        for keshi in final_metrics[task].keys():
            keshi_metrics = final_metrics[task][keshi]

            jbxx_met = keshi_metrics['出院诊断']
            with open(f"./error/{keshi}_error.txt","w", encoding="utf-8") as f:
                f.write(str(jbxx_met))    
            jbxx_met_list.append((jbxx_met[2],jbxx_met[3]))

            for index,key in enumerate(keys):
                cyxj_met_list[index].extend(keshi_metrics[key][0])

        # # print('出院诊断')
        # corr_num = 0
        # all_num = 0
        # for c_num,a_num in jbxx_met_list:
        #     corr_num += c_num
        #     all_num += a_num
        # try:
        #     met = round(corr_num/all_num*100,2)
        # except:
        #     met = 0
        # fw.write('出院诊断\n')
        # fw.write('{}\n'.format(met))

        all_score_list = []
        for index,key in enumerate(keys):
            fw.write('{}\n'.format(key))
            score_list = cyxj_met_list[index]
            now_score = sum(score_list)/len(score_list)
            fw.write('{}\n'.format(round(now_score*100,2)))
            # print(round(now_score*100,2))
            all_score_list.append(now_score)
        # print('avg:{}'.format(round(sum(all_score_list)/len(all_score_list)*100,2)))
        all_nums = 0
        pred_nums = 0
        corr_nums = 0
        for keshi in keshis:
            correct_num,pred_num,all_num = final_metrics['出院小结及子字段'][keshi]['住院期间医疗情况_2']
            all_nums += all_num
            corr_nums += correct_num
            pred_nums += pred_num
        try:
            p = round(corr_nums / pred_nums * 100 ,2)
            r = round(corr_nums / all_nums * 100 ,2)
            f1 = round((2*p*r)/(p+r),2)
        except:
            p = 0
            r = 0
            f1 = 0
        # print('住院期间医疗情况_2')
        # print('P:{}\tR:{}\tF:{}'.format(p,r,f1))
        fw.write('{}\n'.format('住院期间医疗情况_2'))
        fw.write('P:{}\tR:{}\tF:{}\n'.format(p,r,f1))

        # task = '猜测字段'
        # corr_num = 0
        # all_num = 0
        # for keshi in final_metrics[task].keys():
        #     keshi_metrics = final_metrics[task][keshi]
        #     corr_num += keshi_metrics[2]
        #     all_num += keshi_metrics[1]
        # if all_num == 0:
        #     all_num = 1
        # print(task)
        # print(round(corr_num/all_num*100,2))
        # fw.write('{}\n'.format(task))
        # fw.write('{}\n'.format(round(corr_num/all_num*100,2)))
        # task = '格式化'
        # corr_num = 0
        # all_num = 0
        # for keshi in final_metrics[task].keys():
        #     keshi_metrics = final_metrics[task][keshi]
        #     corr_num += keshi_metrics[2]
        #     all_num += keshi_metrics[3]
        # # print(task)
        # # print(round(corr_num/all_num*100,2))
        # if all_num == 0:
        #     all_num = 1
        # fw.write('{}\n'.format(task))
        # fw.write('{}\n'.format(round(corr_num/all_num*100,2)))
        # task = '科室导诊'
        # corr_num = 0
        # all_num = 0
        # for keshi in final_metrics[task].keys():
        #     keshi_metrics = final_metrics[task][keshi]
        #     corr_num += keshi_metrics[2]
        #     all_num += keshi_metrics[1]
        # # print(task)
        # # print(round(corr_num/all_num*100,2))
        # if all_num == 0:
        #     all_num = 1
        # fw.write('{}\n'.format(task))
        # fw.write('{}\n'.format(round(corr_num/all_num*100,2)))
        # task = '指标提取'
        # corr_num = 0
        # all_num = 0
        # for keshi in final_metrics[task].keys():
        #     keshi_metrics = final_metrics[task][keshi]
        #     corr_num += keshi_metrics[2]
        #     all_num += keshi_metrics[3]
        # # print(task)
        # # print(round(corr_num/all_num*100,2))
        # fw.write('{}\n'.format(task))
        # if all_num == 0:
        #     all_num = 1
        # fw.write('{}\n'.format(round(corr_num/all_num*100,2)))
        # task = '指标检测'
        # corr_num = 0
        # all_num = 0
        # for keshi in final_metrics[task].keys():
        #     keshi_metrics = final_metrics[task][keshi]
        #     corr_num += keshi_metrics[2]
        #     all_num += keshi_metrics[1]
        # # print(task)
        # # print(round(corr_num/all_num*100,2))
        # if all_num == 0:
        #     all_num = 1
        # fw.write('{}\n'.format(task))
        # fw.write('{}\n'.format(round(corr_num/all_num*100,2)))
        fw.write('\n')
print('finish')