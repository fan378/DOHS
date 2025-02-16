import json
import sys
from typing import Dict, Any
import random
import os
from transformers import AutoTokenizer, AutoModel
import global_variable

# import torch
# with torch.cuda.device(1):
#     tokenizer = AutoTokenizer.from_pretrained("/data/yuguangya/ALLYOUNEED/7B/chatglm/chat/chatglm3-6b", trust_remote_code=True)
#     model = AutoModel.from_pretrained("/data/yuguangya/ALLYOUNEED/7B/chatglm/chat/chatglm3-6b", trust_remote_code=True, device='cuda')
#     model = model.eval()
# device = 'cuda'

if len(sys.argv)>1:
    key_id = sys.argv[1]
    file_path_zhen = sys.argv[2]
else:
    key_id = "19032000000142"
# print(key_id)

def read_json(file_path)-> dict:
    with open(file_path, 'r',encoding='utf8') as f:
        data = json.load(f)
    return data
def save_json(save_path, data):
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4,ensure_ascii=False)
def save_json(path,data):
    with open(path, 'w',encoding='utf8') as f:
        json.dump(data, f,ensure_ascii=False)

def chinese_to_number(chinese):
    # 定义中文数字和对应的阿拉伯数字
    number_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
                  '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

    if chinese in number_map:
        return number_map[chinese]
    
    # 对于两位数的中文数字如“十一”，“二十”等的处理
    if chinese.startswith('十'):
        if len(chinese) == 1:
            return 10
        else:
            return 10 + number_map[chinese[1]]
    if '十' in chinese:
        tens, unit = chinese.split('十')
        return number_map[tens] * 10 + (number_map[unit] if unit else 0)
    
def get_last_day_value(d,source,patient_id):
    max_day = 0
    ff=-1
    max_key = None
    for key in d.keys():
        # 提取中文数字部分，例如从“第一日”中提取“一”
        if '术后第' in key:
            index0=key.find('第')
            index=key.find('日')
            day_chinese = key[index0+1:index]
#             print(day_chinese)
#             print(key)
            day_number = chinese_to_number(day_chinese)
            if day_number > max_day:
                max_day = day_number
                max_key = key
                ff=0
        elif '日常病程记录' in key:
            a='TM员工名称TM主治医师查房：'
            if 'TM员工名称TM主治医师查房：' not in d[key]["内容"]:
                a="TM员工名称TM主治医生查房"
            list1=[]
            for item in d[key]["内容"].keys():
                list1.append(item)
            if len(list1)<1:
                continue
            if '术后第' in d[key]["内容"][list1[0]]:
                aaaaaa=d[key]["内容"][list1[0]].strip().replace('第 ','第')
#                 print(aaaaaa)
                day_chinese =aaaaaa[aaaaaa.find('术后第')+3:aaaaaa.find('术后第')+4]               
#                 print(day_chinese)
                if day_chinese=='？' or '第日' in aaaaaa or '…' in aaaaaa:
                    temptemp=d[key]["内容"][list1[0]]
                    max_key = key
                    ff=1
                    break
                
                day_number = chinese_to_number(day_chinese)
                # print(day_chinese)
                # print(max_day)
                if day_number > max_day:
                    max_day = day_number
                    max_key = key
                    ff=1
                    temptemp=d[key]["内容"][list1[0]]
    str0=''
    if ff==0:
        a='观察记录:'
        if '观察记录:' not in d[max_key]["内容"]:
            a='TM员工名称TM 主任医生查房'
        list1=[]
        for item in d[max_key]["内容"].keys():
            list1.append(item)
        if len(list1)>1:
            if '处理：' in d[max_key]["内容"][list1[0]]:
                index=d[max_key]["内容"][list1[0]].find('处理：')
                text=d[max_key]["内容"][list1[0]][index:]
                split=text.split('\n')
                for aa in split:
                    split2=aa.split('。')
                    for bb in split2:
                        if '引流管' in bb or '出院' in bb:
                            str0=str0+bb
            elif '处理:' in d[max_key]["内容"][list1[0]]:
                index=d[max_key]["内容"][list1[0]].find('处理:')
                text=d[max_key]["内容"][list1[0]][index:]
                split=text.split('\n')
                for aa in split:
                    split2=aa.split('。')
                    for bb in split2:
                        if '引流管' in bb or '出院' in bb:
                            str0=str0+bb
        if str0!="":
            if "术后反应" not in source[patient_id]:
                source[patient_id]["病程与治疗经过"].setdefault("术后反应",[])
            temp={"book_name":max_key,"content":str0}
            source[patient_id]["病程与治疗经过"]["术后反应"].append(temp)
    elif ff==1:
        if '处理：' in temptemp:
            index=temptemp.find('处理：')
            text=temptemp[index:]
            split=text.split('\n')
            for aa in split:
                split2=aa.split('。')
                for bb in split2:
                    if '引流管' in bb or '出院' in bb:
                        str0=str0+bb
        elif '处理:' in temptemp:
            index=temptemp.find('处理:')
            text=temptemp[index:]
            split=text.split('\n')
            for aa in split:
                split2=aa.split('。')
                for bb in split2:
                    if '引流管' in bb or '出院' in bb:
                        str0=str0+bb
        if str0!="":
            if "术后反应" not in source[patient_id]:
                source[patient_id]["病程与治疗经过"].setdefault("术后反应",[])
            temp={"book_name":"日常病程记录","content":str0}
            source[patient_id]["病程与治疗经过"]["术后反应"].append(temp)
    return str0

#在文书 术后第n日记录，日常病程记录中找到石蜡相关内容
def get_last_day_value2(d,source,patient_id):
    str0=''
    for key,value in d.items():
         if '术后第' in key or '日常病程记录' in key:
                list1=[]
                for item in value["内容"].keys():
                    list1.append(item)
                if len(list1)<1:
                    continue
                temptemp=value["内容"][list1[0]]
                split=temptemp.split('\n')
                for aa in split:
                    if '术后石蜡' in aa:
                        str0=str0+aa
                        if "术后石蜡" not in source[patient_id]:
                            source[patient_id]["病程与治疗经过"].setdefault("术后石蜡",[])
                        temp={"book_name":key,"content":aa}
                        source[patient_id]["病程与治疗经过"]["术后石蜡"].append(temp)
    return str0

#在文书 术后第n日记录，日常病程记录中找到化疗相关内容
def get_last_day_value3(d,source,patient_id):
    str0=''
    for key,value in d.items():
         if '术后第' in key or '日常病程记录' in key or "主治医师日常查房记录" in key:
                list1=[]
                for item in value["内容"].keys():
                    list1.append(item)
                if len(list1)<1:
                    continue
                temptemp=value["内容"][list1[0]]
                if '处理：' in temptemp:
                    index=temptemp.find('处理：')
                    text=temptemp[index:]
                    split=text.split('\n')
                    for aa in split:
                        if '化疗' in aa:
                            # print(aa)
                            str0=str0+aa
                            if "化疗" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("化疗",[])
                            temp={"book_name":key,"content":aa}
                            source[patient_id]["病程与治疗经过"]["化疗"].append(temp)
                elif '处理:' in temptemp:
                    index=temptemp.find('处理:')
                    text=temptemp[index:]
                    split=text.split('\n')
                    for aa in split:
                        if '化疗' in aa:
                            # print(aa)
                            str0=str0+aa
                            if "化疗" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("化疗",[])
                            temp={"book_name":key,"content":aa}
                            source[patient_id]["病程与治疗经过"]["化疗"].append(temp)
                if "诊疗意见: " in temptemp:
                    index=temptemp.find('诊疗意见: ')
                    text=temptemp[index:]
                    split=text.split('\n')
                    for aa in split:
                        if '化疗' in aa or '靶向治疗' in aa:
                            # print(aa)
                            str0=str0+value["时间"]+aa
                            if "化疗" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("化疗",[])
                            temp={"book_name":key,"content":aa}
                            source[patient_id]["病程与治疗经过"]["化疗"].append(temp)
    return str0

#在文书 术后第n日记录，日常病程记录中找到穿刺病理相关内容
def get_last_day_value4(d,source,patient_id):
    str0=''
    temp11=""
    for key,value in d.items():
         if '术后第' in key or '日常病程记录' in key:
                list1=[]
                for item in value["内容"].keys():
                    list1.append(item)
                if len(list1)<1:
                    continue
                temptemp=value["内容"][list1[0]]
                split=temptemp.split('\n')
                for aa in split:
                    if '穿刺病理' in aa:
                        # print(aa)
                        str0=str0+aa
                        temp11=key
    if len(str0)>0:
        if "穿刺病理" not in source[patient_id]:
            source[patient_id]["病程与治疗经过"].setdefault("穿刺病理",[])
        temp={"book_name":temp11,"content":str0}
        source[patient_id]["病程与治疗经过"]["穿刺病理"].append(temp)
    return str0

def extract_sentence_with_keyword(text, keyword)->str:
    # 检查关键词是否在文本中
    if len(text)>600:
        keyword_index = text.find(keyword)
        jiequ=0
        if keyword_index == -1:
            return ''  # 如果关键词不在文本中，返回 ''
        # 向后搜索最近的句号
        end_index = text.find('。', keyword_index)
        if end_index == -1:
            end_index = len(text)  # 如果没有找到句号，直到文本末尾
        # 提取句子并返回
        return jiequ,text[keyword_index:end_index].strip()
    else:
        keyword_index = text.find(keyword)
        jiequ=0
        flag=0
        if keyword_index == -1:
            return ''  # 如果关键词不在文本中，返回 ''
        # 向后搜索最近的句号
        end_index=-1
        if '严密止血' in text[keyword_index:]:
            end_index = text.find('严密止血', keyword_index)
            jiequ=1
        else:
            end_index = text.find('。', keyword_index)
            flag=1
        if '再行' in text[keyword_index:]:
            end_index2 = text.find('再行', keyword_index)
            if flag==0:
                if end_index2<end_index:
                    end_index=end_index2
            else:
                end_index=end_index2
            jiequ=2
        if end_index == -1:
            end_index = len(text)  # 如果没有找到句号，直到文本末尾
    # 提取句子并返回
    return jiequ,text[keyword_index:end_index].strip()

def read_json(file_path):
    with open(file_path, 'r',encoding='utf8') as f:
        data = json.load(f)
    return data

def query(input_text,flag1,query_list,temp_dict,data,total,key_list):
    aaa=[]
    icl=[]
    k=0
    # print(flag1)
    if flag1==0:
        for item in query_list:
            if item in input_text:
                aaa.append(item)               
        for key,value in temp_dict.items():
            if key==input_text:
                continue
            flag=0
            if k==2:
                break
            
            if len(aaa)==0:
                for item in query_list:
                    if item in key:
                        flag=0
                        break
                    else:
                        flag=1                
            else:
                for item in aaa:
                    if item not in key:
                        flag=0
                        break
                    else:
                        flag=1
                if flag==1:
                    for item in query_list:
                        if item in aaa:
                            continue
                        else:
                            if item in key:
                                flag=0
                                break
                            else:
                                flag=1
            if flag==1:
                    icl.append([key,value])
                    k=k+1
    elif flag1==1:
        for key,value in data.items():
            if key in key_list:
                continue
            elif '24小时内入出院记录' in total[key]:
                if '手术记录单(试用)' in total[key] or '手术记录单' in total[key]:
                    icl.append([data[key]["input"],data[key]["output"]])
                    k=k+1
    elif flag1==2:
        for key,value in data.items():
            if key in key_list:
                continue
            if '手术记录单(试用)' not in total[key]:
                icl.append([data[key]["input"],data[key]["output"]])
                k=k+1
    return icl

def compose_zs_prompt_zhenliao(question,context):
    return "例子输入:\n  {}\n\n例子诊疗经过：\n{}\n".format(question, context)

def my_split(s, ds):
    #  s1:待分隔字符串，ds:包含所有分隔符的字符串
    """
     需要注意有种情形是连续两个分隔符，如'i,,j'
     列表中会出现空字符串，此时就需要对结果进行过滤。
    """
    res = [s]
    for d in ds:
        t = []
        list(map(lambda x: t.extend(x.split(d)), res))
        res = t
    # 使用列表解析过滤空字符串
    return [x for x in res if x]


def get_last_day_value_kenei(d):
    str0 = ''
    temp=[]
    book_name_kenei=''
    for key, value in d.items():
        if '术后第' in key or '日常病程记录' in key or '术后当日' in key:
            list1 = []
            for item in value["内容"].keys():
                list1.append(item)
            if len(list1)<1:
                continue
            temptemp = value["内容"][list1[0]]
            if '处理:' in temptemp:
                index = temptemp.find('处理:')
                text = temptemp[index:]
                split = text.split('\n')
                for aa in split:
                    if '引流' in aa or '病理' in aa:
                        temp.append(aa)
                        book_name_kenei=key
    return temp,book_name_kenei
def input_all_zhenliao(ICL,question):
    return "{}\n输入:\n  {}\n\n诊疗经过：".format(ICL, question)

def compose_zs_prompt_bingshi(question,context):
    return "例子输入:\n{}\n\n病史总结：\n{}\n".format(question, context)
def input_all_bingshi(ICL, promote1,promote2,question):
    return "{}\n{}\n{}\n\n患者情况:\n{}\n\n病史总结:".format(ICL,promote1,promote2,question)

def input_all_jiancha(ICL, promote, question):
    return "{}\n{}\n\n检查结果:\n{}\n\n随访科室:".format(ICL,promote, question)

def compose_zs_prompt_jiancha(question,context):
    return "检查结果:\n{}\n\n随访科室：\n{}\n".format(question, context)
def get_last_day_value_chuyuan(d):
    str0 = ''
    temp=[]
    book_name_chuyuan=""
    for key, value in d.items():
        if '术后第' in key or '日常病程记录' in key or '术后当日' in key:
            list1 = []
            for item in value["内容"].keys():
                list1.append(item)
            if len(list1)<1:
                continue
            temptemp = value["内容"][list1[0]]
            if '处理:' in temptemp:
                index = temptemp.find('处理:')
                text = temptemp[index:]
                split = text.split('\n')
                for aa in split:
                    if '引流' in aa or '病理' in aa:
                        temp.append(aa)
                        book_name_chuyuan=key
    # 在有序号1处进行分割
    #str0 = str0.replace('\n1.','\n\n1.')
    return temp,book_name_chuyuan
class HandleData:
    elc: Dict[str, Dict[str, Any]]
    def __init__(self,file_path):
        self.elc = read_json(file_path)
        self.bing_keyword=['术中冰冻病理，','送冰冻提示','送术中冰冻','冰冻病理']
    #按模板抽取相关内容
    def spe_query_zong(self):
        count_1and2=0
        result={}
        source={}
        for patient_id,patient_book in self.elc.items():
            source.setdefault(patient_id,{})
            source[patient_id]={"病程与治疗经过":{}}
            # print(patient_id)
            if '24小时内入出院记录' in self.elc.keys():
                if '手术记录单(试用)' in patient_book.keys() or '手术记录单' in patient_book.keys():
                    print("判断情况：该病历24小时内入出院记录和并且未进行手术")
                    count_1and2 += 1
                    str_zhen=""
                    main_operation=""   # 主要手术信息
                    bingdong_result=""
                    flag_bingdong=0
                    first_record_key='乳腺中心术后首次病程记录'
                    if first_record_key not in patient_book:
                        first_record_key='术后首次病程记录'
                    if first_record_key not in patient_book:     # 两种key都不在，跳过
                        continue

                    first_record_content = patient_book[first_record_key]['内容']   # 术后首次记录内容

                    # 主要手术信息，除手术简要经过、术后应当……、诊断以外的内容
                    for record_key,record_info in first_record_content.items():
                        if "手术简要经过" not in record_key and '术后应当' not in record_key and '诊断' not in record_key:
                            main_operation=main_operation+record_key+record_info
                    if main_operation!="":
                        if "主要手术" not in source[patient_id]:
                            source[patient_id]["病程与治疗经过"].setdefault("主要手术",[])
                        temp={"book_name":first_record_key,"content":main_operation}
                        source[patient_id]["病程与治疗经过"]["主要手术"].append(temp)
                    str_zhen=str_zhen+main_operation
                    # 冰冻
                    operation_process_key='手术简要经过'
                    # 中文冒号或者英文冒号
                    if '手术简要经过：' in first_record_content:
                        operation_process_key='手术简要经过：'
                    elif '手术简要经过:' in first_record_content:
                        operation_process_key='手术简要经过:'
                    # 两个都不是就是手术方式
                    if operation_process_key not in first_record_content:
                        operation_process_key='手术方式'
                    bingdong_text = ''  # 包含冰冻关键词的文本
                    bingdong_str_list=[]   # 冰冻关键词
                    surgey='手术记录单(试用)'
                    if '手术记录单(试用)' not in patient_book:
                        surgey='手术记录单'
                    bingdong_index=0
                    for item in self.bing_keyword:
#                         print(type(first_record_content[operation_process_key]))
                        if item in first_record_content[operation_process_key]:
                            if bingdong_index==0:
                                bingdong_text=first_record_content[operation_process_key].strip()
                                bingdong_index+=1
#                                 for str_bing in bingdong_str_list:
#                                     bingdong_text=first_record_content[operation_process_key].replace(str_bing,'')
                            while(bingdong_text.count(item)>0):
                                if patient_id=='19012900000350':
                                    print(extract_sentence_with_keyword(bingdong_text,item))
                                jiequ,temp_text=extract_sentence_with_keyword(bingdong_text,item)
                                bingdong_str_list.append(temp_text)
                                bingdong_text=bingdong_text.replace(bingdong_str_list[-1],'')
                                if jiequ==1:
                                    bingdong_text=bingdong_text.replace('严密止血','')
                                elif jiequ==2:
                                    bingdong_text=bingdong_text.replace('再行','')
                    if len(bingdong_str_list)>0:
                        for item in bingdong_str_list:
                            bingdong_result=bingdong_result+"  "+item
                            flag_bingdong=1
                        if "冰冻" not in source[patient_id]:
                            source[patient_id]["病程与治疗经过"].setdefault("冰冻",[])
                        temp={"book_name":first_record_key,"content":bingdong_result}
                        source[patient_id]["病程与治疗经过"]["冰冻"].append(temp)
                    if flag_bingdong==0:
                        for item in self.bing_keyword:
                            if item in patient_book[surgey]["内容"]['手术日期']:
                                if bingdong_index==0:
                                    lines=patient_book[surgey]["内容"]['手术日期'].split('\n')
                                    for line in lines:
                                        if '冰冻' in line:
                                            bingdong_text=line.strip()
                                    bingdong_index+=1
    #                                 for str_bing in bingdong_str_list:
    #                                     bingdong_text=first_record_content[operation_process_key].replace(str_bing,'')
                                while(bingdong_text.count(item))>0:
                                    if patient_id=='19012900000350':
                                        print(extract_sentence_with_keyword(bingdong_text,item))
                                    jiequ,temp_text=extract_sentence_with_keyword(bingdong_text,item)
                                    bingdong_str_list.append(temp_text)
                                    bingdong_text=bingdong_text.replace(bingdong_str_list[-1],'')
                                    if jiequ==1:
                                        bingdong_text=bingdong_text.replace('严密止血','').replace('再行','')
                                    elif jiequ==2:
                                        bingdong_text=bingdong_text
                        for item in bingdong_str_list:
                            bingdong_result=bingdong_result+"  "+item
                        if "冰冻" not in source[patient_id]:
                            source[patient_id]["病程与治疗经过"].setdefault("冰冻",[])
                        temp={"book_name":surgey,"content":bingdong_result}
                        source[patient_id]["病程与治疗经过"]["冰冻"].append(temp)
#                     if patient_id =='19031900000172':
#                         print(str_zhen)
                    str_zhen=str_zhen+' '+bingdong_result
                    result[patient_id]={'input':str_zhen,'output':patient_book['出院小结']['内容']["病程与治疗情况"]}
            # 无手术单
            elif '手术记录单(试用)' not in patient_book.keys() and '手术记录单' not in patient_book.keys():
                print("判断情况：患者未进行手术")
                count_1and2=count_1and2+1   # 记录前两种if的次数
                str_zhen=""
                hualiao=""
                t1=0
                for key2,value2 in patient_book.items():
                # 会诊信息
                    if "乳腺中心主任医师查房记录" in key2:    # 存在乳腺中心主任医师查房记录
                        lines=value2['内容']['诊疗意见'].split('\n')  # 拆分成行
                        for line in lines:
                            if '会诊' in line:  # 找出存在会诊的行
                                str_zhen=str_zhen+' '+line
                                if "会诊" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("会诊",[])
                                temp={"book_name":key2,"content":line}
                                source[patient_id]["病程与治疗经过"]["会诊"].append(temp)
                    # 穿刺信息
                    if "乳腺中心主任医师首次查房记录" in key2:    # 存在乳腺中心主任医师首次查房记录
                        lines=value2['内容']['诊疗意见'].split('\n')  # 拆分成行
                        for line in lines:
                            if '穿刺' in line:  # 找出存在穿刺的行
                                str_zhen=str_zhen+' '+line
                                if "穿刺" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("穿刺",[])
                                temp={"book_name":key2,"content":line}
                                source[patient_id]["病程与治疗经过"]["穿刺"].append(temp)
                    if '主治医师日常查房记录' in key2:
                        list1=[]
                        for item in value2["内容"].keys():
                            list1.append(item)
                        if len(list1)<1:
                            continue
                        lines=value2['内容'][list1[0]].split('\n')  # 拆分成行
                        for line in lines:
                            if '穿刺' in line:  # 找出存在穿刺的行
                                str_zhen=str_zhen+' '+line
                                if "穿刺" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("穿刺",[])
                                temp={"book_name":key2,"content":line}
                                source[patient_id]["病程与治疗经过"]["穿刺"].append(temp)
                    # 医生决定
                    if "主任医师日常查房记录" in key2:
                        for key in value2['内容']:
                            if "诊疗意见" in key:
                                diagnosis_opinion=key
                        lines=value2['内容'][diagnosis_opinion].split('\n')
                        for line in lines:
                            if '风险' in line or '会诊' in line or  '出院' in line:
                                str_zhen=str_zhen+' '+line
                                if "医生决定" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("医生决定",[])
                                temp={"book_name":key2,"content":line}
                                source[patient_id]["病程与治疗经过"]["医生决定"].append(temp)
                    if '主治医师日常查房记录' in key2:
                        list1=[]
                        for item in value2["内容"].keys():
                            list1.append(item)
                        if len(list1)<1:
                            continue
                        lines=value2['内容'][list1[0]].split('\n')
                        for line in lines:
                            if '诊疗意见' in line:  # 找出存在穿刺的行
                                str_zhen=str_zhen+' '+line
                                if "诊疗意见" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("医生决定",[])
                                temp={"book_name":key2,"content":line}
                                source[patient_id]["病程与治疗经过"]["医生决定"].append(temp)
                    if '术后第' in key2 or '日常病程记录' in key2:
                        
                        list1=[]
                        for item in value2["内容"].keys():
                            list1.append(item)
                        if len(list1)<1:
                            continue
                        temptemp=value2["内容"][list1[0]]
                        if '处理：' in temptemp:
                            index=temptemp.find('处理：')
                            text=temptemp[index:]
                            lines=text.split('\n')
                            for line in lines:
                                if '出院' in line:
                                    # print(aa)
                                    str_zhen=str_zhen+line
                                    if "医生决定" not in source[patient_id]:
                                        source[patient_id]["病程与治疗经过"].setdefault("医生决定",[])
                                    temp={"book_name":key2,"content":line}
                                    source[patient_id]["病程与治疗经过"]["医生决定"].append(temp)
                        elif '处理:' in temptemp:                          
                            index=temptemp.find('处理:')
                            text=temptemp[index:]
                            lines=text.split('\n')
                            for line in lines:
                                if '出院' in line:
                                    # print(aa)
                                    str_zhen=str_zhen+line
                                    if "医生决定" not in source[patient_id]:
                                        source[patient_id]["病程与治疗经过"].setdefault("医生决定",[])
                                    temp={"book_name":key2,"content":line}
                                    source[patient_id]["病程与治疗经过"]["医生决定"].append(temp)
                    if t1==0:   # 没找过
                        str_zhen=str_zhen+" "+get_last_day_value3(patient_book,source,patient_id)
                        t1=1
                    if '主任医师首次查房' in key2:
                        # print('aaaaaa')
                        a="诊疗意见"
                        if a not in value2["内容"]:
                            a="诊疗意见："
                        if a not in value2["内容"]:
                            a="诊疗意见:" 
                            # print(key)
                            # print(value2["内容"])
                        if a not in value2["内容"]:
                            continue
                        lines=value2["内容"][a].split('\n')
                        for line in lines:  # 每行内容
                            if '化疗' in line:
                                # print(bbb)
                                hualiao=hualiao+line
                        str_zhen=str_zhen+hualiao
                        if hualiao!="":
                            if "化疗" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("化疗",[])
                            temp={"book_name":key2,"content":hualiao}
                            source[patient_id]["病程与治疗经过"]["化疗"].append(temp)        
                if '出院小结' in patient_book:
                    result[patient_id]={'input':str_zhen,'output':patient_book['出院小结']['内容']["病程与治疗情况"]}
                else:
                    result[patient_id]={'input':str_zhen,'output':""}
            else:
                print("判断情况：患者住院超过24小时")
                str_zhen=hualiao=huizhen=shila=bingdong_result=chuanci=str1=''
                flag_bingdong2=flag_bingdong=t1=t2=t3=t4=t5=0
                first_record_key='乳腺中心术后首次病程记录'
                if first_record_key not in patient_book:
                    first_record_key='术后首次病程记录'
                # 主要手术
                print("===========================")
                print("开始寻找主要手术来源")
                if first_record_key not in patient_book:
                    for item in patient_book['手术记录单']['内容']["手术日期"].split('\n'):
                        if '手术者' not in item and '麻醉方式' not in item:
                            str1=str1+item
                        elif '麻醉方式' in item:
                            str1=str1+item
                            break
                    if "主要手术" not in source[patient_id]:
                        source[patient_id]["病程与治疗经过"].setdefault("主要手术",[])
                    temp={"book_name":'手术记录单',"content":str1}
                    source[patient_id]["病程与治疗经过"]["主要手术"].append(temp)
                else:
                    for key2,value2 in patient_book[first_record_key]['内容'].items():
                        if "手术简要经过" not in key2 and '术后应当' not in key2 and '诊断' not in key2:
                            str1=str1+key2+value2
                    if "主要手术" not in source[patient_id]:
                        source[patient_id]["病程与治疗经过"].setdefault("主要手术",[])
                    temp={"book_name":first_record_key,"content":str1}
                    source[patient_id]["病程与治疗经过"]["主要手术"].append(temp)
                #术后用药
                print("===========================")
                print("开始寻找术后用药来源")
                diagnosis_opinion=''
                if '主任医师日常查房记录' in patient_book:
                    if '诊疗意见' in patient_book['主任医师日常查房记录']['内容']:
                        lines=patient_book['主任医师日常查房记录']['内容']["诊疗意见"].split('\n')
                        for line in lines:
                            yongyao=""
                            if line.strip() in str_zhen.strip():
                                diagnosis_opinion=""
                            elif '术前检查' not in line and '术前告知' not in line:
                                diagnosis_opinion=diagnosis_opinion+' '+line
                    if diagnosis_opinion!="":
                        if "术后用药" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("术后用药",[])
                        temp={"book_name":'主任医师日常查房记录',"content":diagnosis_opinion}
                        source[patient_id]["病程与治疗经过"]["术后用药"].append(temp)
                elif "乳腺中心主任医师查房记录" in patient_book:
                    if '诊疗意见' in patient_book['乳腺中心主任医师查房记录']['内容']:
                        lines=patient_book['乳腺中心主任医师查房记录']['内容']["诊疗意见"].split('\n')
                        for line in lines:
                            yongyao=""
                            if line.strip() in str_zhen.strip():
                                diagnosis_opinion=""
                            elif '术前检查' not in line and '术前告知' not in line:
                                diagnosis_opinion=diagnosis_opinion+' '+line
                    if diagnosis_opinion!="":
                        if "术后用药" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("术后用药",[])
                        temp={"book_name":'乳腺中心主任医师查房记录',"content":diagnosis_opinion}
                        source[patient_id]["病程与治疗经过"]["术后用药"].append(temp)
                elif "乳腺中心主任医师首次查房记录" in patient_book:
                    diagnosis_opinion=patient_book['乳腺中心主任医师首次查房记录']['内容']["诊疗意见"]
                    if diagnosis_opinion!="":
                        if "术后用药" not in source[patient_id]:
                            source[patient_id]["病程与治疗经过"].setdefault("术后用药",[])
                        temp={"book_name":'乳腺中心主任医师首次查房记录',"content":diagnosis_opinion}
                        source[patient_id]["病程与治疗经过"]["术后用药"].append(temp)
                tt=get_last_day_value(patient_book,source,patient_id).replace(':：',':')                
                for key2,value2 in patient_book.items():
                    # print(key2)
                    # 化疗
                    if t1==0:   # 没找过
                        print("===========================")
                        print("开始寻找是否存在化疗相关内容")
                        str_zhen=str_zhen+" "+get_last_day_value3(patient_book,source,patient_id)
                        t1=1
                    if '主任医师首次查房' in key2:
                        # print('aaaaaa')
                        a="诊疗意见"
                        if a not in value2["内容"]:
                            a="诊疗意见："
                        if a not in value2["内容"]:
                            a="诊疗意见:" 
                            # print(key)
                            # print(value2["内容"])
                        if a not in value2["内容"]:
                            continue
                        lines=value2["内容"][a].split('\n')
                        for line in lines:  # 每行内容
                            if '化疗' in line:
                                # print(bbb)
                                hualiao=hualiao+line
                                if "化疗" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("化疗",[])
                                temp={"book_name":key2,"content":line}
                                source[patient_id]["病程与治疗经过"]["化疗"].append(temp)
                        str_zhen=str_zhen+hualiao
                    
                    # 穿刺
                    if '主任医师查房记录' in key2:
                        lines=value2["内容"]['诊疗意见'].split('\n')
                        for line in lines:
                            if line.strip() in str_zhen.strip():
                                chuanci=""
                            elif '穿刺' in line:
                                chuanci=chuanci+' '+line
                        if chuanci!="":
                            str_zhen=value2["时间"]+" "+chuanci+' '+str_zhen
                            if "穿刺" not in source[patient_id]:
                                    source[patient_id]["病程与治疗经过"].setdefault("穿刺",[])
                            temp={"book_name":key2,"content":value2["时间"]+" "+chuanci}
                            source[patient_id]["病程与治疗经过"]["穿刺"].append(temp)

                    #穿刺病理
                    if t5==0:
                        print("===========================")
                        print("开始寻找是否存在穿刺病理相关内容")
                        str_zhen=str_zhen+" "+get_last_day_value4(patient_book,source,patient_id)
                        t5=1
                    # 主要手术
                    if t2==0:
                        if '【医学元素\自定义控件' in str1:
                            continue
                        else:
                            str_zhen=str_zhen+str1     
                            t2=1
                    
                    #术后用药
                    if t3==0:
                        str_zhen=str_zhen+diagnosis_opinion
                        t3=1
                    # 冰冻
                    
                    if '术后首次' in key2 and flag_bingdong==0:
                        print("=========================")
                        print("开始寻找冰冻病理相关部分")
                        first_record_content = patient_book[first_record_key]['内容']   # 术后首次记录内容
                        operation_process_key='手术简要经过'
                        if '手术简要经过：' in patient_book[first_record_key]["内容"]:
                            operation_process_key='手术简要经过：'
                        elif '手术简要经过:' in patient_book[first_record_key]["内容"]:
                            operation_process_key='手术简要经过:'
                        if operation_process_key not in patient_book[first_record_key]["内容"]:
                            # print(key)
                            # print(value[aat]["内容"].keys())
                            operation_process_key='手术方式'

                        bingdong_text = ''  # 包含冰冻关键词的文本
                        bingdong_str_list=[]
                        surgey='手术记录单(试用)'
                        if '手术记录单(试用)' not in patient_book:
                            surgey='手术记录单'
                        bingdong_index=0
                        for item in self.bing_keyword:
                            if item in first_record_content[operation_process_key]:
                                if bingdong_index==0:
                                    bingdong_text=first_record_content[operation_process_key].strip()
                                    bingdong_index+=1
#                                 for str_bing in bingdong_str_list:
#                                     bingdong_text=first_record_content[operation_process_key].replace(str_bing,'')
#                                 bingdong_str_list.append(extract_sentence_with_keyword(bingdong_text,item))
#                                 bingdong_text=bingdong_text.replace(bingdong_str_list[-1],'')
                                while(bingdong_text.count(item)>0):
                                    if patient_id=='19012900000350':
                                        print(extract_sentence_with_keyword(bingdong_text,item))
                                    jiequ,temp_text=extract_sentence_with_keyword(bingdong_text,item)
                                    bingdong_str_list.append(temp_text)
                                    bingdong_text=bingdong_text.replace(bingdong_str_list[-1],'')
                                    if jiequ==1:
                                        bingdong_text=bingdong_text.replace('严密止血','')
                                    elif jiequ==2:
                                        bingdong_text=bingdong_text.replace('再行','')
                                flag_bingdong2=1
                        if flag_bingdong2==0: 
                            for item in self.bing_keyword:
                                if item in patient_book[surgey]["内容"]['手术日期']:
                                    if bingdong_index==0:
                                        lines=patient_book[surgey]["内容"]['手术日期'].split('\n')
                                        for line in lines:
                                            if '冰冻' in line:
                                                bingdong_text=line.strip()
                                        bingdong_index+=1
        #                                 for str_bing in bingdong_str_list:
        #                                     bingdong_text=first_record_content[operation_process_key].replace(str_bing,'')
#                                     bingdong_str_list.append(extract_sentence_with_keyword(bingdong_text,item))
#                                     bingdong_text=bingdong_text.replace(bingdong_str_list[-1],'')
                                    while(bingdong_text.count(item))>0:
                                        if patient_id=='19012900000350':
                                            print(extract_sentence_with_keyword(bingdong_text,item))
                                        jiequ,temp_text=extract_sentence_with_keyword(bingdong_text,item)
                                        bingdong_str_list.append(temp_text)
                                        bingdong_text=bingdong_text.replace(bingdong_str_list[-1],'')
                                    if jiequ==1:
                                        bingdong_text=bingdong_text.replace('严密止血','')
                                    elif jiequ==2:
                                        bingdong_text=bingdong_text.replace('再行','')
                        for item in bingdong_str_list:
                            
                            bingdong_result=bingdong_result+"  "+item
                        if flag_bingdong2==0:
                            if "冰冻" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("冰冻",[])
                            temp={"book_name":surgey,"content":bingdong_result}
                            source[patient_id]["病程与治疗经过"]["冰冻"].append(temp)
                        elif flag_bingdong2==1:
                            if "冰冻" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("冰冻",[])
                            temp={"book_name":first_record_key,"content":bingdong_result}
                            source[patient_id]["病程与治疗经过"]["冰冻"].append(temp)
                        # if patient_id=='19031500000363':
                        #     print(bingdong_result)
                        flag_bingdong=1
                        str_zhen=str_zhen+' '+bingdong_result
#                         if patient_id=='19031500000363':
#                             print(key2)
#                             print(str_zhen)
#                         if '术中冰冻病理' in first_record_content[operation_process_key]:
#                             bingdong_text= first_record_content[operation_process_key]
#                             bingdong_keyword.append('术中冰冻病理')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword(bingdong_text,'术中冰冻病理')
#                         elif '术中冰冻病理' in patient_book[surgey]["内容"]['手术日期']:
#                             bingdong_text=patient_book[surgey]["内容"]['手术日期']
#                             bingdong_keyword.append('术中冰冻病理')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword2(bingdong_text,'术中冰冻病理')
#                         if '送冰冻提示' in first_record_content[operation_process_key]:
#                             bingdong_text=first_record_content[operation_process_key]
#                             bingdong_keyword.append('送冰冻提示')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword(bingdong_text,'送冰冻提示')
#                         elif '送冰冻提示' in patient_book[surgey]["内容"]['手术日期']:
#                             bingdong_text=patient_book[surgey]["内容"]['手术日期']
#                             bingdong_keyword.append('送冰冻提示')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword(bingdong_text,'送冰冻提示')
#                         if '送术中冰冻' in patient_book[first_record_key]["内容"][operation_process_key]:
#                             bingdong_text=patient_book[first_record_key]["内容"][operation_process_key]
#                             bingdong_keyword.append('送术中冰冻')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword2(bingdong_text,'送术中冰冻')
#                         elif '送术中冰冻' in patient_book[surgey]["内容"]['手术日期']:
#                             bingdong_text=patient_book[surgey]["内容"]['手术日期']
#                             bingdong_keyword.append('送术中冰冻')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword2(bingdong_text,'送术中冰冻')
#                         if '冰冻病理' in patient_book[first_record_key]["内容"][operation_process_key]:
#                             bingdong_text=patient_book[first_record_key]["内容"][operation_process_key]
#                             bingdong_keyword.append('冰冻病理')
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword2(bingdong_text,'冰冻病理')
#                         elif '冰冻病理' in patient_book[surgey]["内容"]['手术日期']:
#                             bingdong_text=patient_book[surgey]["内容"]['手术日期']
#                             bingdong_result=bingdong_result+extract_sentence_with_keyword2(bingdong_text,'冰冻病理')                              
                        
                    # 石蜡
                    if t4==0:
                        print("====================")
                        print("开始寻找石蜡来源")
                        shila=shila+' '+get_last_day_value2(patient_book,source,patient_id)
                        str_zhen=str_zhen+' '+shila
                        t4=1
                    # 会诊
                    if '新会诊记录' in key2:
                        # print('ddddddddd')
                        a="会诊医师所在科别或医疗机构名称"
                        if a not in value2["内容"]:
                            a="会诊医师所在科别或医疗机构名称:"
                        if "会诊" not in str_zhen:
                            print("====================")
                            print("开始寻找会诊来源")
                            huizhen=huizhen+" "+value2["内容"][a].replace('\n','').strip()+"会诊，"
                            if "会诊" not in source[patient_id]:
                                source[patient_id]["病程与治疗经过"].setdefault("会诊",[])
                            temp={"book_name":key2,"content":line}
                            source[patient_id]["病程与治疗经过"]["会诊"].append(temp)
                            str_zhen=str_zhen+' '+huizhen
                        else:
                            break
                # 术后反应
                print("====================")
                print("开始寻找术后反应来源")
                str_zhen=str_zhen+tt
                print("+++++++++++++++病程与诊疗经过溯源结束+++++++++++++++++++++")
                result[patient_id]={'input':str_zhen}

        return source,result

#===========================读取模型与数据+处理数据=========================================#
def remove_greeting(string):
    greeting = "否认"
    goodbye = "慢性疾病史"
    start_index = string.find(greeting)
    end_index = string.find(goodbye)
    
    if start_index != -1 and end_index != -1:
        # 包含要删除的子字符串
        return string[:start_index] + string[end_index + len(goodbye):]
    else:
        # 没有找到要删除的子字符串
        return string

def main(model,tokenizer,key_id,file_path_zhen=""):
    # print('正在读取模型与数据+处理数据') 
    import csv
    index_keshi={}
    # 打开CSV文件

    # 从CSV文件中读取数据
    with open('病史随访科室对应.csv', 'r',encoding='utf-8') as file:
        # 创建CSV读取器
        reader = csv.reader(file)
        next(reader)
        # 遍历每一行
        for row in reader:
            index_keshi[row[0]]=row[1]
#     model,tokenizer = global_variable.load_model(device)
    handle_data = HandleData(file_path_zhen)

    source,dict_zhen=handle_data.spe_query_zong()

    elc3=read_json('/data/zhongboyang/瑞金/ruxian/乳腺外科_zhen_test.json')
    key_list=[]
    for key in elc3.keys():
        key_list.append(key)
    total=read_json('/data/zhongboyang/瑞金/ruxian/乳腺外科_zhen.json')
    self_elc=read_json(file_path_zhen)
    data=read_json('/data/zhongboyang/瑞金/更新后示例.json')


    temp_dict={}
    for key,value in data.items():
        if key not in key_list:
            if len(value['output'])<1:
    #             print("aaaa")
                continue
    #         if 'text' not in value['output'][0]:
    #             print("bbbb")
    #             continue
            temp_dict.setdefault(value['input'],value['output'])
    #=======================构建ICL=========================================
    query_list=['冰冻','穿刺','石蜡','会诊','化疗']
    promote = '''"手册"：
    诊疗经过:为此次住院期间诊疗情况的总结，包括:
    (1)住院期间的病情变化;
    (2) 检查治疗经过:主要用药的名称、疗程、用量；实施手术、操作的日期、名称、病理检查结果；有意义的辅助检查结果；治疗过程中出现的并发症或不良反应；诊治中还存在的问题等。

    请参照"手册"和下方例子，根据输入总结诊疗经过''' 

    icl_dict={}
    for key,value in dict_zhen.items():
        # if key in key_list:
        if '24小时内入出院记录' in self_elc[key].keys() and '手术记录单(试用)' not in self_elc[key].keys():
            continue
        if '24小时内入出院记录' in self_elc[key].keys():
            if '手术记录单(试用)' in self_elc[key].keys() or '手术记录单' in self_elc[key].keys():
                flag=1
        elif '手术记录单(试用)' not in self_elc[key].keys() and '手术记录单' not in self_elc[key].keys():
            flag=2
        else:
            flag=0
        text_input=dict_zhen[key]['input']
#         print(text_input)
#         print(output)
        text_input=text_input.replace('<BR> 查房医师: TM员工名称TM 签名: ______ 日期:______','').replace('医师: TM员工名称TM 签名: ______ 日期:______','').replace('<BR>','')
        icl=query(dict_zhen[key]['input'],flag,query_list,temp_dict,data,total,key_list)
    #     print(icl)
        if len(icl)==0:
            random_keys = random.choices(list(temp_dict.keys()), k=1)
            icl.append([random_keys[0],temp_dict[random_keys[0]]])
            print(icl)
        if len(icl)>0:
            text1 = icl[0][0]
            answer1 =icl[0][1]
            text1=text1.replace('<BR> 查房医师: TM员工名称TM 签名: ______ 日期:______','').replace('医师: TM员工名称TM 签名: ______ 日期:______','').replace('<BR>','')

        if len(icl)>1:
            text2 = icl[1][0]
            answer2 = icl[1][1]
            text2=text2.replace('<BR> 查房医师: TM员工名称TM 签名: ______ 日期:______','').replace('医师: TM员工名称TM 签名: ______ 日期:______','').replace('<BR>','')
        else:
            text2=""
            answer2=""
        ICL = compose_zs_prompt_zhenliao(text1.replace("\n",""),answer1.replace("\n","")) + '\n' + compose_zs_prompt_zhenliao(text2.replace("\n",""),answer2.replace("\n",""))

        if len(ICL)>2000:
            ICL=compose_zs_prompt_zhenliao(text1.replace("\n",""),answer1.replace("\n",""))
        icl_dict[key]=ICL

    total_dict={}
    i=0
    # print('读取模型与数据+处理数据成功')
    # print('正在推理，请稍等...')
    #=============================推理-病程与治疗情况=======================================
    print('#=============================开始推理-病程与治疗情况=======================================')
    for key,value in dict_zhen.items():
        # if key in key_list:
            # print(key)
    #         print(input_all(ICL+"\n请参照上方例子，根据输入总结诊疗经过,禁止抄写例子\n",text_input))
        text_input=dict_zhen[key]['input'].replace('\n','')
        # output=dict_zhen[key]['output']
#         print(output)

        text_input=text_input.replace('<BR> 查房医师: TM员工名称TM 签名: ______ 日期:______','').replace('医师: TM员工名称TM 签名: ______ 日期:______','').replace('<BR>','')
        response, history = model.chat(tokenizer, input_all_zhenliao(icl_dict[key]+"\n请参照上方例子，根据输入总结诊疗经过,禁止抄写例子\n",text_input.replace("\n","")),temperature=0.1)
        print(input_all_zhenliao(icl_dict[key]+"\n请参照上方例子，根据输入总结诊疗经过,禁止抄写例子\n",text_input.replace("\n","")),response)
        if '补充' in response:
            response=response[:response.find('补充')]
        total_dict.setdefault(key,{"病程与治疗情况":response.replace('\n','')})
    print('#=============================推理成功=======================================')
    print("病程与诊疗经过:\n",total_dict)
    #=============================推理-出院带药医嘱=======================================
    print('#=============================开始推理-出院带药医嘱=======================================')
    print('开始判断患者是否存在慢性病、科外疾病并匹配随访科室')
    source[key_id].setdefault("出院带药医嘱",{})       
    i=0
    temp_zong={}
    elc=read_json(file_path_zhen)
    for key,value in elc.items():
        str1=""
        for key2,value2 in value.items():
            
            if '入院记录' in key2:
                if '既往史' in value2['内容']:
                    item=value2['内容']['既往史']
                else:
                    continue
                if '疾病史:' in item and '预防接种史' in item:
                    str1=item[item.find('疾病史:'):item.find("预防接种史")]
        if "慢性病史" not in source[key]:
            source[key]["出院带药医嘱"].setdefault("慢性病史",[])
        temp={"book_name":"入院记录","content":str1.replace('\n','')}
        source[key]["出院带药医嘱"]["慢性病史"].append(temp)
        temp_zong.setdefault(key,str1.replace('\n',''))
        i=i+1



    #例子
    # text1 = '''疾病史: 高血压史20余年，现服厄贝沙坦氢氯噻嗪片 1# qd+血脂康 2# bid；房性早博病史2年，目前控制尚可。否认糖尿病、冠心病、COPD等慢性疾病史 传染病史: 否认 传染性疾病史。'''

    # answer1 = '''高血压,早搏'''

    # text2 = '''疾病史: 否认高血压、糖尿病、冠心病、COPD等慢性疾病史。 传染病史: 承认 传染性疾病史，乙肝大三阳20余年，目前服用恩替卡韦1'''

    # answer2 = '''乙肝'''

    # # text3 = '''腹部超声提示：胆囊隆起样病变（考虑胆囊息肉）'''

    # # answer3 = '''肝胆外科'''
    # # promote 是相关医疗知识，视输入长度决定是否添加
    # promote1 = '''疾病列表:["乙肝","心肌炎","桥本甲状腺炎","高血压","甲状腺结节","心绞痛","早搏","糖尿病","过敏性支气管炎"]''' # ,并且通过自己的语言精简的描述小事件
    # #promote_2 = "请将下面的文本精简描述为多个小事件,描述小事件时，请忽略不重要信息。并且结合上面的格式进行输出\n"  # ,并且通过自己的语言精简的描述小事件
    # promote2='''你是一位专业医生，根据患者情况，判断患者是否存在疾病列表中的疾病,没有则输出“无”'''
    # #ICL = compose_zs_prompt_1(text1, answer1)
    # ICL = compose_zs_prompt_bingshi(text1, answer1) + '\n' + compose_zs_prompt_bingshi(text2, answer2)


    #输入样本


    yizhu={}
    for key,value in temp_zong.items():
        temp_sys=[]
        temp_list=[]
        # response,history= model.chat(tokenizer,input_all_bingshi(ICL,promote1,promote2,value), history=[],temperature=0.2)
        # if '病史总结' in response:
        #     response=response[response.find("病史总结"):]
        for ill,keshi in index_keshi.items():
            if ill in remove_greeting(value) and ill not in temp_sys:
                temp_sys.append(ill)
        if len(temp_sys)>3:
            yizhu.setdefault("慢性病医嘱",[])
        else:
            for item in temp_sys:
                temp_list.append("患者{}病史，建议{}随访".format(item,index_keshi[item]))
            yizhu.setdefault("慢性病医嘱",temp_list)
    print("慢性病医嘱:\n",temp_list)



    i=0
    temp_zong={}
    for key,value in elc.items():
        if "检查" in value:

            temp={}
            for item in value['检查']:
                if item[2]!='心电图':
                    if '随访' in item[6] or '随诊' in item[6] or '建议' in item[6]:
                        sysptom_list=[]
                        jiancha_name=""
                        for ii in range(2,5):
                            if item[ii] not in jiancha_name:
                                jiancha_name=jiancha_name+item[ii]
                        if "超声乳腺中心三维超声" in jiancha_name or "放射增强住院MRI" in jiancha_name or "乳腺" in jiancha_name:
                            continue
                        temp_list=my_split(item[6],'\n。；')
                        for vv in temp_list:
                            if '未见明显异常' in vv: 
                                continue
                            elif '乳' in vv and '，' not in vv:
                                continue
                            elif '请结合临床' in vv:
                                vv=vv[:vv.find('请结合临床')]
                                if vv!="":
                                    sysptom_list.append(vv.replace('，随访',''))

                            else:
                                sysptom_list.append(vv.replace('，随访',''))
                        temp.setdefault(jiancha_name,sysptom_list)
                else:
                    if '正常' not in item[6]:
                        jiancha_name='心电图'
                        sysptom_list=[]
                        sysptom_list.append(item[6])
                        temp.setdefault(jiancha_name,sysptom_list)
            if "检查异常" not in source[key]:
                source[key]["出院带药医嘱"].setdefault("检查异常",[])
            temp222={"book_name":"检查","content":temp}
            source[key]["出院带药医嘱"]["检查异常"].append(temp222)
            temp_zong.setdefault(key,temp)
            i=i+1
    




    #例子
    text1 = '''心电图提示：T波轻度改变'''

    answer1 = '''心内科'''

    text2 = '''胸部CT检查两肺多发小结节，左肺舌段索条'''

    answer2 = '''呼吸科'''

    text3 = '''腹部超声提示：胆囊隆起样病变（考虑胆囊息肉）'''

    answer3 = '''肝胆外科'''

    promote = '''你是一位专业医生，请根据检查结果，参考上面例子，从科室列表中选择随访科室:["呼吸科","胰腺外科","消化科","高血压科","骨科","心内科","妇科","血液科","肝胆外科"]''' # ,并且通过自己的语言精简的描述小事件

    ICL = compose_zs_prompt_jiancha(text1, answer1) + '\n' + compose_zs_prompt_jiancha(text2, answer2)+ '\n' + compose_zs_prompt_jiancha(text3, answer3)



    list_keshi=["呼吸科","胰腺外科","消化科","高血压科","骨科","心内科","妇科","血液科","肝胆外科"]
    for key,value in temp_zong.items():
        temp_list=[]
        for key2,value2 in value.items():
            temp_sys=[]
            for item in value2:
                text_input=key2+'提示'+item
                response,history= model.chat(tokenizer, input_all_jiancha(ICL, promote,text_input), history=[],temperature=0.2)
                print(input_all_jiancha(ICL, promote,text_input),response)
                for vv in list_keshi:
                    if vv in response:
                        if vv not in temp_sys:
                            temp_sys.append(vv)
            if len(temp_sys)>0:
                text_out=key2+'提示'+"，".join(value2)+"，"+"、".join(temp_sys)+"随访"
                temp_list.append(text_out)
        yizhu.setdefault("检查医嘱",temp_list)
    print("检查检验医嘱:\n",temp_list)


    str1="病理报告及相关检查报告出齐后，专科护士电话通知后来我院制定下一步治疗方案。"
    str_ba1="保持伤口清洁干燥，拔管前避免洗澡；拔除引流管前，每3天来院换药一次，换药门诊时间：每周一～周五15:00-16:30门诊大楼22楼乳腺中心门诊。如有发热，切口局部红肿、疼痛、化脓等不适，及时来院就诊。"
    str_ba2='拔管前尽量避免患侧上肢外展、上举、拎提重物；拔管后可适当进行上肢功能锻炼，康复锻炼详见专页。'
    str_00="保持伤口清洁干燥，如有发热，切口局部红肿、疼痛、化脓等不适，及时来院就诊。"
    list1=["注意营养及休息，如有不适，及时就诊。","□近一月内避免上肢剧烈运动。 □术后康复指导详见专页"]
    for key,value in elc.items():
        kenei_yizhu=[]
        flag_guan=0
        flag_bing=0
        temp,book_name_kenei=get_last_day_value_kenei(value)
        for item in temp:
            if "带管出院" in item:
                flag_guan=1
                if "科内医嘱" not in source[key]:
                    source[key]["出院带药医嘱"].setdefault("科内医嘱",[])
                temp222={"book_name":book_name_kenei,"content":item}
                source[key]["出院带药医嘱"]["科内医嘱"].append(temp222)
            if "病理报告" in item:
                if "科内医嘱" not in source[key]:
                    source[key]["出院带药医嘱"].setdefault("科内医嘱",[])
                temp222={"book_name":book_name_kenei,"content":item}
                source[key]["出院带药医嘱"]["科内医嘱"].append(temp222)
                flag_bing=1
        if flag_guan==0 and flag_bing==0:
            kenei_yizhu.append(str_00)     
            kenei_yizhu.extend(list1)
        elif flag_guan==1 and flag_bing==0:
            kenei_yizhu.append(str_ba1)
            kenei_yizhu.append(str_ba2)
            kenei_yizhu.extend(list1)
        elif flag_bing==1 and flag_guan==0:
            kenei_yizhu.append(str1)
            kenei_yizhu.append(str_00)
            kenei_yizhu.extend(list1)
        elif flag_bing==1 and flag_guan==1:
            kenei_yizhu.append(str1)
            kenei_yizhu.append(str_ba1)
            kenei_yizhu.append(str_ba2)
            kenei_yizhu.extend(list1)
        yizhu.setdefault("科内医嘱",kenei_yizhu)
    print("科内医嘱:\n",kenei_yizhu)

    i=1
    temp_yizhu_str=""
    for item in yizhu["科内医嘱"]:
        temp_yizhu_str=temp_yizhu_str+str(i)+'.'+item+'\n'
        i=i+1
    for item in yizhu["慢性病医嘱"]:
        temp_yizhu_str=temp_yizhu_str+str(i)+'.'+item+'\n'
        i=i+1
    for item in yizhu["检查医嘱"]:
        temp_yizhu_str=temp_yizhu_str+str(i)+'.'+item+'\n'
        i=i+1
    for key in total_dict.keys():
        total_dict[key]["出院后用药建议"]=temp_yizhu_str

    print("+++++++++++++++++++++++医嘱字段推理成功++++++++++++++++++++++++++++")
    print("医嘱字段:\n",temp_yizhu_str)
    print("======================开始推理出院时情况===========================")
    source[key_id].setdefault("出院时情况",{})

    str1="神清，精神可，一般情况良好。伤口愈合I/甲，经上级医师同意后，予以带管出院。"
    str2="神清，精神可，一般情况良好。伤口愈合I/甲，经上级医师同意后，予以出院。"
    out={}
    for key,value in elc.items():
        flag_guan=0
        flag_bing=0
        temp,book_name_chuyuan=get_last_day_value_chuyuan(value)
        for item in temp:
            if "带管出院" in item:
                flag_guan=1
                if "患者情况" not in source[key]:
                    source[key]["出院时情况"].setdefault("患者情况",[])
                temp222={"book_name":book_name_chuyuan,"content":item}
                source[key]["出院时情况"]["患者情况"].append(temp222)
        if flag_guan==0:
            yizhu=str2    
        elif flag_guan==1:
            yizhu=str1
    for key in total_dict.keys():
        total_dict[key]["出院时情况"]=yizhu
    print("======================出院时情况推理成功===========================")
    print(yizhu)
    #==========推理完毕，保存==============================


    rname="演示示例/复杂字段"+key_id+".json"
    save_json(rname,total_dict)
    rname="演示示例/复杂字段溯源"+key_id+".json"
    save_json(rname,source)
    print('复杂字段推理成功')
# main(model,tokenizer,key_id)

# import torch
# with torch.cuda.device(1):
#     tokenizer = AutoTokenizer.from_pretrained("/data/yuguangya/ALLYOUNEED/7B/chatglm/chat/chatglm3-6b", trust_remote_code=True)
#     model = AutoModel.from_pretrained("/data/yuguangya/ALLYOUNEED/7B/chatglm/chat/chatglm3-6b", trust_remote_code=True, device='cuda')
#     model = model.eval()
# # device = 'cuda'
# main(model,tokenizer,'20060500000379',file_path_zhen="processed/合并.json")