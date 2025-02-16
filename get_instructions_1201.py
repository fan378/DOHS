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

def get_instructions_v1201(data_dir,out_dir,keshi):
    if out_dir != '':
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    random.seed(2023)
    if isinstance(data_dir,str):
        datas = load_excel_csv(data_dir)
        datas.fillna('',inplace=True)
    else:
        datas = data_dir

    out_name = '出院小结及子字段_v1201.jsonl'
    delete_tokens = {
        '患者基本信息':2000,
        '住院期间医疗情况':6000,
        '出院诊断':1000,
        '病程与治疗情况':2000,
        '出院后用药建议':2000,
        '出院时情况':1000,
    }
    keep_nums = 0
    delete_nums = 0



    def transfer_value(val):
        if val == '':
            return {}
        else:
            return json.loads(val)


    for col in datas.columns[1:]:
        datas[col] = datas[col].apply(transfer_value)


    datas.head()


    from copy import deepcopy
    ori_data = deepcopy(datas)


    # 输入：instruction 带html标签数据
    # 输出 纯文本


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


    instructions


    # # 构造数据


    all_data_maps = {}


    tips = {
        'detail':[
            '请以标准的json格式输出，字段为{keys}，并包含{detail_keys}这些子字段。',
            '输出应符合标准的json格式，包含字段{keys}，其中要包括子字段{detail_keys}。',
            '请按照标准json格式输出，使用字段{keys}，并且包含子字段{detail_keys}。',
            '确保输出遵循标准的json格式，包括{keys}字段和其子字段{detail_keys}。',
            '以标准的json格式进行输出，包含字段{keys}，并且要有子字段{detail_keys}。',
            '输出应为标准json格式，字段为{keys}，包括子字段{detail_keys}。',
            '请确保输出遵守标准json格式，并包含字段{keys}以及子字段{detail_keys}。',
            '输出要求为标准json格式，包含字段{keys}和子字段{detail_keys}。',
            '按照标准json格式输出，请使用字段{keys}并包含子字段{detail_keys}。',
            '输出标准json格式数据，请包含字段{keys}及其子字段{detail_keys}。',
            '使用标准的json格式进行输出，确保包含字段{keys}和子字段{detail_keys}。',
        ],
        'normal':[
            '请以标准的json格式输出，并包含{keys}字段。',
            '输出应遵循标准的json格式，确保包含字段{keys}。',
            '请按标准json格式输出，包括{keys}字段。',
            '确保输出为标准json格式，并包含{keys}字段。',
            '标准json格式的输出中，请包含字段{keys}。',
            '以标准的json格式进行输出，确保有{keys}字段。',
            '输出时，请使用标准json格式并包含字段{keys}。',
            '请以标准json格式输出数据，并且包括{keys}字段。',
            '标准json格式输出中应包含{keys}字段。',
            '输出标准json格式数据，确保有{keys}字段。',
            '使用标准的json格式输出，确保包含字段{keys}。',
        ]
    }


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
                '出院时间':'cons_出院时间',
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
                '无24':['新入院评估单---三、生理状况评估','入院告知书---患者信息','乳腺中心入院记录---专科情况','乳腺中心入院记录---现病史','乳腺中心入院记录---初步诊断','出院医嘱'],
                '有24':['新入院评估单---三、生理状况评估','入院告知书---患者信息','24小时内入出院记录---入院情况','出院医嘱']
            }
        },
        '住院期间医疗情况':{
            'output_keys':{
                '住院期间医疗情况':'住院期间医疗情况'
            },
            'source_keys':['检查','检验']
        },
        '出院诊断':{
            'output_keys':{
                '出院诊断':'出院诊断'
            },
            'source_keys':['乳腺中心主治医师首次查房记录---诊断','乳腺中心术后首次病程记录---术中诊断','主治医师首次查房记录---诊断','术后首次病程记录---术中诊断']
        },
        '病程与治疗情况':{
            'output_keys':{
                '病程与治疗情况':'病程与治疗情况'
            },
            'source_keys':{
                '无手术':['乳腺中心主治医师首次查房记录---诊疗计划','乳腺中心主任医师首次查房记录---诊疗意见','主治医师首次查房记录---诊疗计划','主任医师首次查房记录---诊疗意见','常规医嘱'],
                '有手术':['乳腺中心术后首次病程记录','术后最后一日记录','术后首次病程记录']
            }
        },
        '出院后用药建议':{
            'output_keys':{
                '出院后用药建议':'出院后用药建议'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','既往史','异常检验指标','出院带药','检查随访','未出检查结果报告','未出病理结果报告']
        },
        '出院时情况':{
            'output_keys':{
                '出院时情况':'出院时情况'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','乳腺中心术后首次病程记录---手术方式']
        },
        '医嘱介绍':'请先检查患者报告是否出齐,针对患者的出院带药进行描述，随后阐述患者应注意的伤口处理,对患者的复诊与换药提供指示,最后对患者在检验检查中的异常情况、以及患者的其他诊断进行随诊建议'
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
                '出院时间':'cons_出院时间',
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
                '无24':['新入院评估单---三、生理状况评估','入院记录---体格检查','呼吸日间病房护理记录---护理评估','入院告知书---患者信息','首次病程记录---病例特点','入院记录---现病史','入院记录---初步诊断','出院医嘱'],
                '有24':['新入院评估单---三、生理状况评估','呼吸日间病房护理记录---护理评估','入院告知书---患者信息','24小时内入出院记录---入院情况','出院医嘱']
            }
        },
        '住院期间医疗情况':{
            'output_keys':{
                '住院期间医疗情况':'住院期间医疗情况'
            },
            'source_keys':['检查','检验','入院记录---现病史','24小时内入出院记录---入院情况','既往史']
        },
        '出院诊断':{
            'output_keys':{
                '出院诊断':'出院诊断'
            },
            'source_keys':['主治医师首次查房记录---诊断','入院记录---主治医师48小时诊断']
        },
        '病程与治疗情况':{
            'output_keys':{
                '病程与治疗情况':'病程与治疗情况'
            },
            'source_keys':{
                '无手术':['主治医师首次查房记录---诊疗计划','主任医师首次查房记录---诊疗意见','常规医嘱'],
                '有手术':['术后首次病程记录','术后最后一日记录']
            }
        },
        '出院后用药建议':{
            'output_keys':{
                '出院后用药建议':'出院后用药建议'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','异常检验指标','出院带药','检查随访','未出检查结果报告','未出病理结果报告']
        },
        '出院时情况':{
            'output_keys':{
                '出院时情况':'出院时情况'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','主任医师首次查房记录---对病情的分析']
        },
        '医嘱介绍':'请描述患者出院后应注意的内容,介绍患者的出院带药,并对患者的复诊项进行建议,提醒患者查询未出齐的报告,最后提醒随诊注意事项'
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
                '出院时间':'cons_出院时间',
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
                '无24':['新入院评估单---三、生理状况评估','入院记录---体格检查','入院告知书---患者信息','首次病程记录---病例特点','入院记录---现病史','入院记录---初步诊断','出院医嘱'],
                '有24':['新入院评估单---三、生理状况评估','入院告知书---患者信息','24小时内入出院记录---入院情况','出院医嘱']
            }
        },
        '住院期间医疗情况':{
            'output_keys':{
                '住院期间医疗情况':'住院期间医疗情况'
            },
            'source_keys':['检查','检验']
        },
        '出院诊断':{
            'output_keys':{
                '出院诊断':'出院诊断'
            },
            'source_keys':['主治医师首次查房记录---诊断','入院记录---主治医师48小时诊断']
        },
        '病程与治疗情况':{
            'output_keys':{
                '病程与治疗情况':'病程与治疗情况'
            },
            'source_keys':{
                '无手术':['主治医师首次查房记录---诊疗计划','主任医师首次查房记录---诊疗意见','常规医嘱'],
                '有手术':['术后首次病程记录','术后最后一日记录']
            }
        },
        '出院后用药建议':{
            'output_keys':{
                '出院后用药建议':'出院后用药建议'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','异常检验指标','出院带药','检查随访','未出检查结果报告','未出病理结果报告','术后首次病程记录---手术简要经过']
        },
        '出院时情况':{
            'output_keys':{
                '出院时情况':'出院时情况'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','术后最后一日记录']
        },
        '医嘱介绍':'请描述患者出院后应注意的内容,介绍患者的出院带药,并根据患者的手术过程提醒患者对伤口与拆线的注意事项,与部分手术可能造成的术后情况'
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
                '出院时间':'cons_出院时间',
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
                '无24':['新入院评估单---三、生理状况评估','入院记录---体格检查','入院告知书---患者信息','首次病程记录---病例特点','入院记录---现病史','入院记录---初步诊断','出院医嘱'],
                '有24':['新入院评估单---三、生理状况评估','入院告知书---患者信息','24小时内入出院记录---入院情况','出院医嘱']
            }
        },
        '住院期间医疗情况':{
            'output_keys':{
                '住院期间医疗情况':'住院期间医疗情况'
            },
            'source_keys':['检查','检验']
        },
        '出院诊断':{
            'output_keys':{
                '出院诊断':'出院诊断'
            },
            'source_keys':['主治医师首次查房记录---诊断','入院记录---主治医师48小时诊断']
        },
        '病程与治疗情况':{
            'output_keys':{
                '病程与治疗情况':'病程与治疗情况'
            },
            'source_keys':{
                '无手术':['主治医师首次查房记录---诊疗计划','主任医师首次查房记录---诊疗意见','常规医嘱'],
                '有手术':['术后首次病程记录','术后最后一日记录']
            }
        },
        '出院后用药建议':{
            'output_keys':{
                '出院后用药建议':'出院后用药建议'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','出院带药','检查随访','未出检查结果报告','未出病理结果报告','术后评估/治疗后病程记录---术后/治疗后处理措施','术后评估/治疗后病程记录---术后/治疗后应当特别注意观察的事项','术后首次病程记录---术后处理措施','术后首次病程记录---术后应当特别注意观察的事项']
        },
        '出院时情况':{
            'output_keys':{
                '出院时情况':'出院时情况'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','术后最后一日记录','上级医师查房记录---诊断依据']
        },
        '医嘱介绍':'请描述患者术后注意事项,介绍患者的出院带药,并建议患者复诊时间,提醒患者是否有未出齐的检查与病理报告,最后根据住院期间部分检查情况进行随诊建议'
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
                '出院时间':'cons_出院时间',
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
                '无24':['新入院评估单---三、生理状况评估','入院记录---体格检查','入院告知书---患者信息','首次病程记录---病例特点','入院记录---现病史','入院记录---初步诊断','出院医嘱'],
                '有24':['新入院评估单---三、生理状况评估','入院告知书---患者信息','24小时内入出院记录---入院情况','出院医嘱']
            }
        },
        '住院期间医疗情况':{
            'output_keys':{
                '住院期间医疗情况':'住院期间医疗情况'
            },
            'source_keys':['检查','检验']
        },
        '出院诊断':{
            'output_keys':{
                '出院诊断':'出院诊断'
            },
            'source_keys':['主治医师首次查房记录---诊断','入院记录---主治医师48小时诊断']
        },
        '病程与治疗情况':{
            'output_keys':{
                '病程与治疗情况':'病程与治疗情况'
            },
            'source_keys':{
                '无手术':['主治医师首次查房记录---诊疗计划','主任医师首次查房记录---诊疗意见','常规医嘱'],
                '有手术':['术后首次病程记录','术后最后一日记录']
            }
        },
        '出院后用药建议':{
            'output_keys':{
                '出院后用药建议':'出院后用药建议'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息','出院带药','主治医师首次查房记录---诊疗计划']
        },
        '出院时情况':{
            'output_keys':{
                '出院时情况':'出院时情况'
            },
            'source_keys':['科室','入院诊断','出院诊断','入院告知书---患者信息']
        },
        '医嘱介绍':'请描述患者术后注意事项,介绍患者的出院带药,根据患者诊疗计划对后续诊疗安排进行提醒(如定期化疗等)'
    }
    all_data_maps['zhongliuke'] = zhongliuke_data_maps


    # 直接从出院小结中拿到的一些常量
    constant_names_1 = ['科室','入院诊断','出院诊断','性别','出院时间']
    # 要自己构造的常量
    # 常规医嘱（没有带药）(√)；既往史 (√)；异常检验指标；检查随访(√)；未出结果报告 (√)；术后最后一日记录(√)


    # 把医嘱转为字符串类型
    def transfer_yizhu_to_str(data):
        columns = ['医嘱类型名称','医嘱类型','医嘱项类别','医嘱项名称','医嘱项规格','单次剂量数量','单次给药数量','给药途径','给药频次']
        res_str = ''
        for need_key in columns:
            res_str = res_str + '{}:{}\n'.format(need_key,data[need_key])
        return res_str.strip()


    # 拿到三类医嘱（出院带药；常规；出院医嘱）
    def get_chuyuandaiyao(yizhu_list):
        chuyuandaiyao_list = []
        not_chuyuandaiyao_list = []
        chuyuanyizhu = ''
        for data in yizhu_list:
            for data_item in data['医嘱详情']:
                if '出院' in data_item['医嘱项名称']:
                    chuyuanyizhu = transfer_yizhu_to_str(data_item)
                elif data_item['医嘱类型'] == '出院带药':
                    chuyuandaiyao_list.append(transfer_yizhu_to_str(data_item))
                else:
                    not_chuyuandaiyao_list.append(transfer_yizhu_to_str(data_item))
        return chuyuandaiyao_list,not_chuyuandaiyao_list,chuyuanyizhu


    # 把检查转为字符串类型
    def transfer_jiancha_to_str(data):
        # 全部的
        columns = ['报告时间','检查类型','检查部位','检查描述','检查子类型','图像所见','图像分析']
        # 太多了 筛选
        data['描述'] = data['检查类型'].strip() + '|' + data['检查部位'].strip() + '|' + data['检查子类型'].strip() + '|' + data['检查描述']
        columns = ['报告时间','描述','图像分析','图像分析']
        res_str = ''
        for need_key in columns:
            res_str = res_str + '{}:{}\n'.format(need_key,data[need_key])
        return res_str.strip()


    # 只保留部分的字段
    def transfer_masked_jiancha_to_str(data):
        # 太多了 筛选
        data['描述'] = data['检查类型'].strip() + '|' + data['检查部位'].strip() + '|' + data['检查子类型'].strip() + '|' + data['检查描述']
        columns = ['检查时间','描述']
        res_str = ''
        for need_key in columns:
            res_str = res_str + '{}:{}\n'.format(need_key,data[need_key])
        return res_str.strip()


    # 把检查转为字符串
    def transfer_jianyan_to_str(data):
        columns = ['检验指标','检测值','单位','检验结果','下限','上限','单位']
        res_str = '报告时间:{}\n检验详情:'.format(data['检验详情'][0]['报告时间'])
        maps = {
            '结果在参考范围之内':'正常',
            '超出了参考范围上限':'偏高',
            '超出了参考范围下限':'偏低'
        }
        for jianyan_item in data['检验详情']:
            if jianyan_item['检验结果'] in maps.keys():
                jianyan_item['检验结果'] = maps[jianyan_item['检验结果']]
            res_str = res_str + '{}:{} {},{}(参考值:{} - {} {})\t'.format(*tuple([jianyan_item[k] for k in columns]))
        return res_str.strip()


    # 把病理转为字符串
    def transfer_bingli_to_str(data):
        columns = ['报告时间','临床诊断','病理类型','病理诊断结果','镜下所见','肉眼所见','免疫组化','报告内容']
        res_str = ''
        for need_key in columns:
            res_str = res_str + '{}:{}\n'.format(need_key,data[need_key])
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


    def get_jiancha_list(jiancha_list,discharge_time):
        true_jiancha_list = []
        masked_jiancha_list = []
        suifang_jiancha_list = []
        for index,jiancha in enumerate(jiancha_list):
            try:
                report_time = jiancha['报告时间']
                report_time = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
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
                    if '随访'  in jiancha['图像分析'] or '随诊' in jiancha['图像分析']:
                        suifang_jiancha_list.append(jiancha)

        return true_jiancha_list,masked_jiancha_list,suifang_jiancha_list


    def get_weichu_bingli_list(bingli_list,discharge_time):
        masked_bingli_list = []
        for index,bingli in enumerate(bingli_list):
            try:
                report_time = bingli['报告时间']
                report_time = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
                if report_time > discharge_time:
                    bingli['病理诊断结果'] = ""
                    bingli['镜下所见'] = ""
                    bingli['肉眼所见'] = ""
                    bingli['免疫组化'] = ""
                    bingli['报告内容'] = ""
                    masked_bingli_list.append(bingli)
            except:
                    pass

        return masked_bingli_list


    # 拿到没出的病理
    def transfer_weichu_bingli_to_str(data):
        columns = ['检查时间','临床诊断','病理类型']
        res_str = ''
        for need_key in columns:
            res_str = res_str + '{}:{}\n'.format(need_key,data[need_key])
        return res_str.strip()


    # 处理一下异常检验，只要指标、值和结果
    def transfer_yichang_jianyan_to_str(data):
        columns = ['检验指标','检测值','单位','检验结果']
        res_str = ''
        maps = {
            '结果在参考范围之内':'正常',
            '超出了参考范围上限':'偏高',
            '超出了参考范围下限':'偏低'
        }
        for jianyan_item in data:
            if jianyan_item['检验结果'] in maps.keys():
                jianyan_item['检验结果'] = maps[jianyan_item['检验结果']]
            res_str = res_str + '{}:{} {},{}\t'.format(*tuple([jianyan_item[k] for k in columns]))
        return res_str.strip()


    def transfer_wenshu_to_str(data):
        columns = ['文书名','时间','内容']
        res_str = ''
        for col in columns:
            res_str = res_str + '{}:{}\n'.format(col,data[col])
        return res_str.strip()


    # 拿到异常检验
    def get_yichang_jianyan(jianyan_list):
        items = []
        # 单个检验单
        for jianyan in jianyan_list:
            # 检验项
            for jianyan_item in jianyan['检验详情']:
                if jianyan_item['检验结果'] == '超出了参考范围上限' or jianyan_item['检验结果'] == '超出了参考范围下限' or '阳' in jianyan_item['检验结果']:
                    items.append(jianyan_item)
        return items


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


    def find_chuyuan_time_in_wenshu(i,wenshu_list):
        wenshu_times = []
        for wenshu in wenshu_list:
            if '出院记录' in wenshu['文书名'] and '24小时' not in wenshu['文书名']:
                try:
                    wenshu_times.append(check_date_format(wenshu['时间'])[0])
                    time_out = wenshu['内容']['出院日期']
                    stand_time,flag = check_date_format(time_out)
                    if flag == False:
                        # print('at index:{} 原字符串:{} ||日期格式化错误'.format(i,stand_time))
                        pass
                    else:
                        return stand_time.split(' ')[0]
                except:
                    # print('at index:{} 字段:{} 出院日期 字段错误'.format(i,wenshu['文书名']))
                    pass
            if '24小时' in wenshu['文书名']:
                try:
                    wenshu_times.append(check_date_format(wenshu['时间'])[0])
                    text = wenshu['内容']['姓名']
                    time_out = text[text.index('出院时间:'):].replace('出院时间:','').strip()
                    stand_time,flag = check_date_format(time_out)
                    if flag == False:
                        # print('at index:{} 原字符串:{} ||日期格式化错误'.format(i,stand_time))
                        pass
                    else:
                        return stand_time.split(' ')[0]
                except:
                    try:
                        text = text
                        # print('at index:{} 文书名:{} 在姓名中抽取出院时间错误'.format(i,wenshu['文书名']))
                        # print('内容:{}'.format(text))
                        pass
                    except:
                        # print('at index:{} 文书名:{} 查找[内容][姓名]字段错误'.format(i,wenshu['文书名']))
                        pass
        return wenshu_times[0].split(' ')[0]        


    # 把删除状态的医嘱去掉
    def process_yizhu(yizhu_list):
        for item in yizhu_list:
            # 创建一个新的医嘱详情列表，用于存放筛选后的元素
            filtered_details = []
            for detail in item['医嘱详情']:
                # 检查 '状态' 字段是否为 '删除'，如果不是，则加入新的列表
                if '状态' in detail and detail['状态'] != '删除':
                    filtered_details.append(detail)
            # 将筛选后的医嘱详情列表替换原来的 '医嘱详情' 字段
            item['医嘱详情'] = filtered_details

        # 删除 '医嘱详情' 字段为空的字典元素
        return [item for item in yizhu_list if item['医嘱详情']]


    def process_wenshu(wenshu_list):
        drop_keys = ['jlysxgsj','cfysxgsj','sjysxgsj','录入日期','最后修改日期']
        for wenshu in wenshu_list:
            for drop_key in drop_keys:
                try:
                    wenshu.pop(drop_key)
                except:
                    pass
        return wenshu_list


    def build_data(index,ori_data):
        global keep_nums,delete_nums
        res_data = []
        # xiaojie = {}
        zylsh = ori_data.iat[0]
        # 来源字典
        source_data = {zylsh:{}}
        # 病理
        bingli_list = ori_data.iat[1]
        # 医嘱
        yizhu_list = ori_data.iat[3]
        # 把删除状态的医嘱去掉
        yizhu_list = process_yizhu(yizhu_list)
        # 文书
        wenshu_list = ori_data.iat[5]
        wenshu_list = process_wenshu(wenshu_list)
        wenshu_text_list = ori_data.iat[6]
        wenshu_text_list = process_wenshu(wenshu_text_list)


        # 检查
        jiancha_list = ori_data.iat[9]
        # 检验
        jianyan_list = ori_data.iat[11]

        flag = False

        # 处理一下 年龄 和 入院、出院时间的错误情况
        ############################################
        # 24小时中，会把出院的信息也放在里面，要删掉
        drop_keys = ['诊疗经过','出院情况','出院诊断','出院医嘱']
        for index,data in enumerate(wenshu_list):
            if '24小时' in data['文书名']:
                data_keys = data['内容'].keys()
                for drop_key in drop_keys:
                    if drop_key in data_keys:
                        data['内容'].pop(drop_key)
                    else:
                        print('index:{} 住院流水号:{} 文书为:{} 没找到需要删掉的字段:{} 所有字段:{}'.format(index,zylsh,data['文书名'],drop_key,data_keys))
                # 出院时间删掉
                try:
                    data['内容']['姓名'] = data['内容']['姓名'][:data['内容']['姓名'].index('出院时间')].strip()
                except:
                    print('24小时中无法删除出院记录:{}'.format(data['内容']['姓名']))
                start_index = wenshu_text_list[index]['内容'].find('入院诊断:')
                wenshu_text_list[index]['内容'] = wenshu_text_list[index]['内容'][:start_index].strip()

        # 把出院前没出结果的检查和检验mask掉，防止影响"住院期间医疗情况"字段
        chuyuan_time = '9999-99-99'
        jiancha_list,weichujieguo_jiancha_list,suifang_jiancha_list = get_jiancha_list(jiancha_list,chuyuan_time)
        # 检验的话，直接把检测结果和检测值去掉
        for index,jianyan in enumerate(jianyan_list):
            report_time = jianyan['检验详情'][0]['报告时间']
            try:
                report_time = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d')
                if report_time > chuyuan_time:
                    for jianyan_item in jianyan['检验详情']:
                        jianyan_item['报告时间'] = ""
                        jianyan_item['检测值'] = ""
                        jianyan_item['检验结果'] = ""
            except:
                # print('检验时间转换错误:{}'.format(report_time))
                pass


        ############################################
        # 一些常量
        constants = {}
        constants['入院诊断'] = '入院记录---初步诊断'
        for wenshu in wenshu_list:
            if '24' not in wenshu['文书名'] and '入院记录' in wenshu['文书名']:
                constants['入院诊断'] = wenshu['内容']['初步诊断']
                break
            if '24小时' in wenshu['文书名'] and ('入院记录' in wenshu['文书名'] or '出院记录' in wenshu['文书名']):
                constants['入院诊断'] = wenshu['内容']['入院诊断']
                break
        constants['科室'] = cons_chinese_keshis[keshi]

        # 拿到既往史
        for data in wenshu_list:
            if '入出院记录' in data['文书名']:
                try:
                    if data['内容']['入院情况'].strip() != '':
                        constants['既往史'] = data['内容']['入院情况']
                except:
                    pass
            elif '入院记录' in data['文书名'] and '24小时' not in data['文书名']:
                try:
                    if data['内容']['既往史'].strip() != '':
                        constants['既往史'] = data['内容']['既往史']
                except:
                    pass
        # 拿到三类型医嘱：[出院带药；常规；出院医嘱]
        chuyuandaiyao_list,no_chuyuandaiyao_list,chuyuanyizhu = get_chuyuandaiyao(yizhu_list)
        constants['出院带药'] = ('\n'.join(chuyuandaiyao_list)).strip()
        constants['常规医嘱'] = ('\n'.join(no_chuyuandaiyao_list)).strip()
        constants['出院医嘱'] = chuyuanyizhu.strip()
        # 检查
        # 把检查转为字符串
        jiancha_str = ''
        for data in jiancha_list:
            jiancha_str = jiancha_str + '\n' + transfer_jiancha_to_str(data)
        constants['检查'] = jiancha_str
        # 未出结果的检查
        weichujieguo_jiancha_str = ''
        for data in weichujieguo_jiancha_list:
            weichujieguo_jiancha_str = weichujieguo_jiancha_str + '\n' + transfer_masked_jiancha_to_str(data)
        constants['未出检查结果报告'] = weichujieguo_jiancha_str
        # 检查随访
        suifang_jiancha_str = ''
        for data in suifang_jiancha_list:
            suifang_jiancha_str = suifang_jiancha_str + '\n' + transfer_jiancha_to_str(data)
        constants['检查随访'] = suifang_jiancha_str
        # 检验
        jianyan_str = ''
        for data in jianyan_list:
            jianyan_str = jianyan_str + '\n' + transfer_jianyan_to_str(data)
        constants['检验'] = jianyan_str.strip()
        # 异常检验
        yichang_jianyan_list = get_yichang_jianyan(jianyan_list)
        constants['异常检验指标'] = transfer_yichang_jianyan_to_str(yichang_jianyan_list).strip()
        # 病理
        bingli_str = ''
        for data in bingli_list:
            bingli_str = bingli_str + '\n' + transfer_bingli_to_str(data)
        constants['病理报告'] = bingli_str
        # 未出病理
        weichu_bingli_str = ''
        weichu_bingli_list = get_weichu_bingli_list(bingli_list,chuyuan_time)
        for data in weichu_bingli_list:
            weichu_bingli_str = weichu_bingli_str + '\n' + transfer_weichu_bingli_to_str(data)
        constants['未出病理结果报告'] = weichu_bingli_str
        shuhou_last = None
        for wenshu in wenshu_list:
            if '术后' in wenshu['文书名']:
                shuhou_last = transfer_wenshu_to_str(wenshu)
        constants['术后最后一日记录'] = shuhou_last
        #################################################################
        # 构造数据
        for key,value in data_maps.items():
            if key in ['医嘱介绍','病程与治疗情况','出院后用药建议','出院时情况']:
                continue
            data_ins = random.choice(instructions)
            data_output = {}
            data_input = ''
            out_maps = value['output_keys']
            source_keys = value['source_keys']

            # 输入
            #######################
            # 根据特殊情况判断一下
            # 根据患者的情况分为['有24小时','无24小时'],['有手术','无手术']这两类
            # 确定患者类别，以确定所需字段
            if isinstance(source_keys,dict):
                # 需要特殊情况判断
                pass
                if '有24' in source_keys.keys():
                    flag = False
                    for data in wenshu_list:
                        if data['文书名'] == '24小时内入出院记录':
                            flag=True
                            break
                    if flag:
                        source_keys = source_keys['有24']
                    else:
                        source_keys = source_keys['无24']
                elif '有手术' in source_keys.keys():
                    flag = False
                    for data in wenshu_list:
                        if '手术记录单' in data['文书名']:
                            flag=True
                            break
                    if flag:
                        source_keys = source_keys['有手术']
                    else:
                        source_keys = source_keys['无手术']
                else:
                    raise Exception('source keys找不到')
            cons_keys = constants.keys()
            new_wenshu_list = {}
            for wenshu in wenshu_list:
                new_wenshu_list[wenshu['文书名']] = wenshu
            try:
                new_wenshu_list['入院告知书']['内容']['患者信息'] = new_wenshu_list['入院告知书']['内容']['患者信息'][:new_wenshu_list['入院告知书']['内容']['患者信息'].index('为了保障')]
            except:
                pass
            new_wenshu_text_list = {}
            for wenshu in wenshu_text_list:
                new_wenshu_text_list[wenshu['文书名']] = wenshu
            # 造数据  
            for s_key in source_keys:
                # 在常量中，从常量找
                if s_key in cons_keys:
                    data_input = data_input + '###{}:\n{}\n'.format(s_key,constants[s_key])
                else:
                    # 看有没有'---'，没有的话就是整个文书，从text_wenshu找
                    if '---' not in s_key:
                        try:
                            data_input = data_input + '###{}:\n{}\n'.format(s_key,new_wenshu_text_list[s_key]['内容'])
                        except:
                            pass
                            # print('{}找不到:{}'.format(s_key,ori_data.iat[0]))
                    # 有的话，就是文书子字段，从wenshu找
                    else:
                        try:
                            main_key,sub_key = s_key.split('---')
                            data_input = data_input + '###{}:\n{}\n'.format(s_key,new_wenshu_list[main_key]['内容'][sub_key])
                        except:
                            pass
                            # print('{}找不到:{}'.format(s_key,ori_data.iat[0]))
            if key == '出院后用药建议':
                data_input = data_input + '\n撰写建议:{}'.format(data_maps['医嘱介绍'])
            if len(out_maps.keys()) != 1:

                tip = random.choice(tips['detail'])
                tip = tip.replace('{keys}',key)
                tip = tip.replace('{detail_keys}','，'.join(list(out_maps.keys())))
            else:
                tip = random.choice(tips['normal'])
                tip = tip.replace('{keys}',key)
                
            data_ins = data_ins.replace('{key}',key)
            data_ins = data_ins.replace('{tip}',tip)
            data_ins = data_ins.replace('\\n','\n')
            data_ins = data_ins.replace('{input}',data_input)
            data_output = json.dumps(data_output,ensure_ascii=False)
            data_ins = re.sub('(\n)+','\n',data_ins)
            tmp_data = {
                'instruction':data_ins.strip()+'\n',
                'input':'',
                'output':'',
                'zylsh':zylsh,
                'key':key
            }
            tmp_source_data = {key:data_input}
            source_data[zylsh].update(tmp_source_data)
            res_data.append(tmp_data)
                    
        return res_data,source_data


    data_maps = all_data_maps[keshi]

    final_datas = []
    final_source_datas = []
    datas = deepcopy(ori_data)
    for i in tqdm(range(datas.shape[0])):
        res_data,source_data = build_data(i,datas.iloc[i,:])
        # break
        if res_data == None:
            continue
        final_source_datas.append(source_data)
        final_datas.extend(res_data)

    if out_dir != '':
        with jsonlines.open(os.path.join(out_dir,out_name),'w') as f:
            for final_data in final_datas:
                f.write(final_data)
        for final_source_data in final_source_datas:
            with open(f'演示示例/简单字段溯源{next(iter(final_source_data))}.json','w') as f:
                json.dump(final_source_data,f,ensure_ascii=False)
    return final_datas

