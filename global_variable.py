from transformers import AutoModel, AutoTokenizer
import os
import json
import re
import torch
from decimal import Decimal

[file_path,key_id] = ['','']
[model1,tokenizer1] = ['','']
[model2,tokenizer2] = ['','']
[keshi,ins_out_dir,generate_out_dir,processed_out_dir] = ['','','','']
[model_generated_path,doctor_generated_path] =['演示示例','医生示例']
now_mode = ''
# kebie_to_chinesekeshi = {
#     '乳腺外科一':'乳腺外科',
#     '消化一病区':'消化内科',
#     '内分泌一':'内分泌'
# }

def _init(): #初始化
    global model1,tokenizer1
    global model2,tokenizer2
    global file_path,key_id
    global keshi,ins_out_dir,generate_out_dir
    [file_path,key_id] = ['','']
    [model1,tokenizer1] = ['','']
    [model2,tokenizer2] = ['','']
    [keshi,ins_out_dir,generate_out_dir] = ['','','']
 
def load_model(which_model,DEVICE):
    if which_model == 'model1': # 原始模型
        model_path = '/data/yuguangya/ALLYOUNEED/7B/chatglm/chat/chatglm3-6b'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path, trust_remote_code=True, device=DEVICE)
    elif which_model == 'model2': # 训练后的模型
        model_path = '/data/wangjiacheng/瑞金/1228_测试/export_models/chuyuanxiaojie_1201'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path,torch_dtype=torch.float16, trust_remote_code=True, device=DEVICE)
    elif which_model == 'model_wjc': # 全科室模型
        model_path = '/data/xiazhentao/System/ruijin/model/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
        # model_path = '/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
        # model_path = '/data/wangjiacheng/瑞金/1228_测试/export_models/chuyuanxiaojie_1201'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path,torch_dtype=torch.float16, trust_remote_code=True, device=DEVICE)
    model = model.eval()
    return model,tokenizer

def set_value(which_model,DEVICE):
    global model1,tokenizer1,model2,tokenizer2,file_path,key_id
    global keshi,ins_out_dir,generate_out_dir, now_mode,processed_out_dir
    global model_generated_path,doctor_generated_path
    
    if which_model == 'model1':
        model1,tokenizer1 = load_model(which_model,DEVICE)
    elif which_model == 'model2':
        model2,tokenizer2 = load_model(which_model,DEVICE)
    elif which_model == "file_path":
        file_path = DEVICE
    elif which_model == "key_id":
        key_id = DEVICE
    elif which_model == "keshi":
        keshi = DEVICE
    elif which_model == "ins_out_dir":
        ins_out_dir = DEVICE
    elif which_model == "generate_out_dir":
        generate_out_dir = DEVICE
    elif which_model == "processed_out_dir":
        processed_out_dir = DEVICE
    elif which_model == "now_mode":
        now_mode = DEVICE
    elif which_model == "doctor_generated_path":
        doctor_generated_path = DEVICE
    elif which_model == "model_generated_path":
        model_generated_path = DEVICE
    else:
        print('error')
      
def get_value(which_model):
    global model1,tokenizer1,model2,tokenizer2,file_path,key_id
    global keshi,ins_out_dir,generate_out_dir, now_mode, processed_out_dir
    global model_generated_path,doctor_generated_path

    if which_model == 'model1':
        return model1,tokenizer1
    elif which_model == 'model2':
        return model2,tokenizer2
    elif which_model == "file_path":
        return file_path
    elif which_model == "key_id":
        return key_id    
    elif which_model == "keshi":
        return keshi
    elif which_model == "ins_out_dir":
        return ins_out_dir 
    elif which_model == "generate_out_dir":
        return generate_out_dir 
    elif which_model == "now_mode":
        return now_mode 
    elif which_model == "doctor_generated_path":
        return doctor_generated_path 
    elif which_model == "model_generated_path":
        return model_generated_path 
    elif which_model == "processed_out_dir":
        return processed_out_dir 

def replace_content(label,content,html_content):
    replaced_string = '这是' + label
    html_content = html_content.replace(replaced_string,content)
    return html_content

# 单科室模型读取html的函数，已废弃
def read_html():
    with open('template.html','r',encoding='utf-8') as f:
        html_content = f.read()
    global key_id
    file_name = f"./演示示例/{key_id}.json"
    if os.path.exists(file_name):
        with open(file_name,'r',encoding='utf8') as f:
            content = json.load(f)  
        content[key_id]['出院后用药建议'] = re.sub(r'\n', "<br/>", content[key_id]['出院后用药建议'])
        content[key_id]['出院后用药建议'] = re.sub(r'□', "", content[key_id]['出院后用药建议'])
        content[key_id]['住院期间医疗情况'] = re.sub(r'(\d{4}-\d{2}-\d{2})', r"<br>\1", content[key_id]['住院期间医疗情况'])
        content[key_id]['住院期间医疗情况'] = content[key_id]['住院期间医疗情况'].strip('<br>')
        key_list = list(content[key_id].keys())
        key_list.remove('基本信息')
        key_list.remove('病人信息')
        key_list.remove('生命体征')
        for item in key_list:
            html_content = replace_content(item,content[key_id][item],html_content)
        for item in list(content[key_id]['基本信息'].keys()):
            html_content = replace_content(item,content[key_id]['基本信息'][item],html_content)
        for item in list(content[key_id]['生命体征'].keys()):
            html_content = replace_content(item,content[key_id]['生命体征'][item],html_content)
        # for item in list(content[key_id]['病人信息'].keys()):
            # content = replace_content(item,content[key_id]['病人信息'][item],content)
        return html_content
    else:
        # return html_content
        return '模型正在努力生成，请稍后再试^_^'

def read_json(file_path):
    with open(file_path,'r',encoding='utf8') as f:
        file_content = json.load(f)  
    return file_content

# 使用正则表达式提取数字部分
def extract_numbers(sentence):
    # 使用正则表达式提取数字部分
    numbers = re.findall(r'(\d+(\.\d+)?)', sentence)
    notnumbers = set(sentence) - set(''.join(tpl[0] for tpl in numbers))
    return [Decimal(num[0]) if '.' in num[0] else int(num[0]) for num in numbers],notnumbers,[num[0] for num in numbers]

# 判断model和doctor数值是否一样
def compare_values(model_number_list,model_number_string_list,doctor_number_list,doctor_number_string_list,model_content,doctor_content):
    # 判断数值是否一样
    for i in range(len(model_number_list)):
        if model_number_list[i] in doctor_number_list:
            # doctor_index = doctor_number_list.index(model_number_list[i])
            model_content = re.sub(r'(?<!\d|\.)(?<!<span style="color: green;">)'+model_number_string_list[i]+r'(?!\d|\.)',f'<span style="color: green;">{model_number_string_list[i]}</span>',model_content)
            doctor_content = re.sub(r'(?<!\d|\.)(?<!<span style="color: green;">)'+model_number_string_list[i]+r'(?!\d|\.)',f'<span style="color: green;">{model_number_string_list[i]}</span>',doctor_content)
    return model_content,doctor_content

# 把model和doctor重叠的字变绿
def word_turns_green(model_content,doctor_content):
    model_number_list,temp_model_content, model_number_string_list = extract_numbers(model_content)
    doctor_number_list,temp_doctor_content, doctor_number_string_list = extract_numbers(doctor_content)
    intersection_content = temp_model_content.intersection(temp_doctor_content)
    # model_difference_content = temp_model_content.difference(temp_doctor_content)
    # doctor_difference_content = temp_doctor_content.difference(temp_model_content)
    model_content = ''.join([f'<span style="color: green;">{char}</span>' if char in intersection_content else char for char in model_content])
    doctor_content = ''.join([f'<span style="color: green;">{char}</span>' if char in intersection_content else char for char in doctor_content])
    model_content,doctor_content = compare_values(model_number_list,model_number_string_list,doctor_number_list,doctor_number_string_list,model_content,doctor_content)
    return model_content,doctor_content

# 对各字段做预处理，然后调用word_turns_green将字变绿
def string_matching(model_json_path,doctor_json_path,key_id):
    model_json = read_json(model_json_path)
    doctor_json = read_json(doctor_json_path)
    key_list = list(model_json[key_id].keys())
    key_list.remove('基本信息')
    key_list.remove('病人信息')
    key_list.remove('生命体征')
    # model_json[key_id]['出院后用药建议'] = re.sub('。 ', '。<br>', model_json[key_id]['出院后用药建议'])    # 实现分点效果

    for item in key_list:
        model_json[key_id][item],doctor_json[key_id][item] = word_turns_green(model_json[key_id][item],doctor_json[key_id][item])
    for item in list(model_json[key_id]['基本信息'].keys()):
        model_json[key_id]['基本信息'][item],doctor_json[key_id]['基本信息'][item] = word_turns_green(model_json[key_id]['基本信息'][item],doctor_json[key_id]['基本信息'][item])
    for item in list(model_json[key_id]['生命体征'].keys()):
        model_json[key_id]['生命体征'][item],doctor_json[key_id]['生命体征'][item] = word_turns_green(model_json[key_id]['生命体征'][item],doctor_json[key_id]['生命体征'][item])
    return model_json,doctor_json

def single_json_to_html(json_content,key_id,html_name='template',title='出院小结'):
    with open(html_name+'.html','r',encoding='utf-8') as f:
        html_content = f.read()
    html_content = html_content.replace('出院小结',title)
    # 出院后用药建议
    json_content[key_id]['出院后用药建议'] = re.sub(r'</span><span style="color: green;">', r"", json_content[key_id]['出院后用药建议'])
    json_content[key_id]['出院后用药建议'] = re.sub('。 ', '。<br>', json_content[key_id]['出院后用药建议'])    # 实现分点效果
    json_content[key_id]['出院后用药建议'] = re.sub(r'\n', "<br>", json_content[key_id]['出院后用药建议'])
    # json_content[key_id]['出院后用药建议'] = re.sub(r'(\d(<span style="color: green;">)?\.)', r"<br/>\1", json_content[key_id]['出院后用药建议'])
    json_content[key_id]['出院后用药建议'] = re.sub(r'^<span style="color: green;"><br/>', r'<span style="color: green;">', json_content[key_id]['出院后用药建议'])     #  删除首尾的<br>
    json_content[key_id]['出院后用药建议'] = re.sub(r'□', "", json_content[key_id]['出院后用药建议'])
    json_content[key_id]['出院后用药建议'] = re.sub(r'(\d\.)', r'<span style="color: green;">\1</span>', json_content[key_id]['出院后用药建议']) 
    json_content[key_id]['出院后用药建议'] = re.sub(r'^<br/>|<br/>$', '', json_content[key_id]['出院后用药建议']) 
    # 住院期间医疗情况
    json_content[key_id]['出院后用药建议'] = re.sub(r'\n', "<br>", json_content[key_id]['出院后用药建议'])
    json_content[key_id]['住院期间医疗情况'] = re.sub(r'</span><span style="color: green;">', r"", json_content[key_id]['住院期间医疗情况'])
    json_content[key_id]['住院期间医疗情况'] = re.sub(r'(\d{4}-\d{2}-\d{2})', r"<br>\1", json_content[key_id]['住院期间医疗情况'])
    json_content[key_id]['住院期间医疗情况'] = re.sub(r'^<br>|<br>$', '', json_content[key_id]['住院期间医疗情况'])     #  删除首尾的<br>
    json_content[key_id]['住院期间医疗情况'] = re.sub(r'^<span style="color: green;"><br>', r'<span style="color: green;">', json_content[key_id]['住院期间医疗情况'])     #  删除首尾的<br>
    key_list = list(json_content[key_id].keys())
    key_list.remove('基本信息')
    key_list.remove('病人信息')
    key_list.remove('生命体征')
    for item in key_list:
        html_content = replace_content(item,json_content[key_id][item],html_content)
    for item in list(json_content[key_id]['基本信息'].keys()):
        html_content = replace_content(item,json_content[key_id]['基本信息'][item],html_content)
    for item in list(json_content[key_id]['生命体征'].keys()):
        html_content = replace_content(item,json_content[key_id]['生命体征'][item],html_content)
    return html_content

def read_html_with_key_id(key_id=key_id,prefix='演示示例'):
    template_name = "template"
    if now_mode in ['ruxianwaike', 'ruxianwaike_singlecuda']:
        if prefix == '演示示例':
            title = '大模型版-出院小结'
            if os.path.exists(f"./{prefix}/复杂字段溯源{key_id}.json") and os.path.exists(f"./{prefix}/简单字段溯源{key_id}.json"):
                template_name = "template_highlight"
        else:
            title = '医生版-出院小结'
        file_name = f"./{prefix}/{key_id}.json" 
    elif now_mode in ['quankeshi']:
        if prefix == '演示示例':
            title = '大模型版-出院小结'
            if os.path.exists(f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_postprocessed.json"):
                template_name = "template_highlight"
            file_name = f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_postprocessed.json" 
        else:
            title = '医生版-出院小结'
            file_name = f"./{doctor_generated_path}/{keshi}/{key_id}/{key_id}.json" 

    if os.path.exists(file_name):
        with open(file_name,'r',encoding='utf8') as f:
            content = json.load(f)  
        html_content = single_json_to_html(content,key_id,html_name = template_name,title=title)
        return html_content
    else:
        return  f'''<div id="container" style="padding:20pt;height: 75vh;overflow-y: scroll;background-color: #f5f5f5;">
                    <section class="docx" style="padding: 40pt 60pt;background-color: #FFFFFF;height:100%;">
                        <p style="text-align: center;"><span style="font-family: 宋体; min-height: 18pt; font-size: 18pt;">{title}</span></p>
                        <p style="text-align: center;">
                            <span style="font-family: 微软雅黑; font-weight: bold; min-height: 12pt; font-size: 12pt;">未查询到相关文件，请稍后重试^_^</span>
                        </p>
                    </section>
                </div>
                '''

def load_backtracking_html_wjc(key_id=key_id):
    model_file_path = f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_findsource.json"
    if os.path.exists(model_file_path):
        json_content = read_json(model_file_path)
        with open('template_backtracking.html','r',encoding='utf-8') as f:
            backtracking_html = f.read()
        key_list = list(json_content[key_id].keys())
        # print(json_content[key_id]['住院期间医疗情况'])
        for item in key_list:
            # 删掉prompt部分
            temp_list = json_content[key_id][item].split('\n')[:-2] 
            if item in ['病程与治疗情况','出院后用药建议']: # 对这两字段，多删一次
                temp_list = temp_list[:-1]
            json_content[key_id][item] = '\n'.join(temp_list)
            # 处理一下输出格式
            # 处理开头的###
            json_content[key_id][item] = re.sub(r'^###(.*)(---|:)\n',r'<br/><span style="font-weight: bold;">###\1</span><br/>',json_content[key_id][item])
            # 处理非开头的
            json_content[key_id][item] = re.sub(r'\n###(.*)(---|:)\n',r'<br/><span style="font-weight: bold;">###\1</span><br/>',json_content[key_id][item])
            # print(json_content[key_id][item])
            json_content[key_id][item] = re.sub(r'\n', '<br/>', json_content[key_id][item])     #  删除首尾的<br>
            # print(json_content[key_id][item])
            json_content[key_id][item] = re.sub(r'^<br/>|<br/>$', '', json_content[key_id][item])     #  删除首尾的<br>
            
            # 替换到页面模板上
            backtracking_html = replace_content(item,json_content[key_id][item],backtracking_html)

        # 处理换行符
        json_content[key_id]['住院期间医疗情况'] = re.sub(r'(\n)+', '<br/>', json_content[key_id]['住院期间医疗情况'])
        return backtracking_html
    else:
        return '''<div id="container" style="padding:20pt;height: 75vh;overflow-y: scroll;background-color: #f5f5f5;">
                    <section class="docx" style="padding: 40pt 60pt;background-color: #FFFFFF;height:100%;">
                    <p style="text-align: center;"><span style="font-family: 宋体; min-height: 18pt; font-size: 18pt;">溯源</span></p>
                        <p style="text-align: center;">
                            <span style="font-family: 微软雅黑; font-weight: bold; min-height: 12pt; font-size: 12pt;">未查询到相关文件，请稍后重试^_^</span>
                        </p>
                    </section>
                </div>
                '''

def load_backtracking_html(key_id=key_id):
    if os.path.exists(f'演示示例/简单字段溯源{key_id}.json') and os.path.exists(f'演示示例/复杂字段溯源{key_id}.json'):
        # 处理简单字段
        json_content = read_json(f'演示示例/简单字段溯源{key_id}.json')
        with open('template_backtracking.html','r',encoding='utf-8') as f:
            backtracking_html = f.read()
        key_list = list(json_content[key_id].keys())
        # print(json_content[key_id]['住院期间医疗情况'])
        for item in key_list:
            json_content[key_id][item] = re.sub(r'###(.*)(---|:)',r'<br/><span style="font-weight: bold;">###\1</span><br/>',json_content[key_id][item])
            json_content[key_id][item] = re.sub(r'^<br/>|<br/>$', '', json_content[key_id][item])     #  删除首尾的<br>
            backtracking_html = replace_content(item,json_content[key_id][item],backtracking_html)
        json_content[key_id]['住院期间医疗情况'] = re.sub(r'(\n)+', '<br/>', json_content[key_id]['住院期间医疗情况'])
        # 处理复杂字段
        json_content = read_json(f'演示示例/复杂字段溯源{key_id}.json')
        key_list = list(json_content[key_id].keys())
        for item in key_list:
            if json_content[key_id][item] == {}:
                backtracking_html = replace_content(item,'无',backtracking_html)
                continue
            new_replaced_content = '' 
            for subitem in json_content[key_id][item].keys():
                new_replaced_content += '<span style="font-weight: bold;">※'+subitem +'</span><br>'
                for sub_dict in json_content[key_id][item][subitem]:
                    if sub_dict["content"] == {} or sub_dict["content"] == '':
                        new_replaced_content += f'<span style="font-weight: bold;">###{sub_dict["book_name"]}</span><br>无<br>'
                        continue
                    new_replaced_content += f'<span style="font-weight: bold;">###{sub_dict["book_name"]}</span><br>{sub_dict["content"]}<br>'
            new_replaced_content = re.sub(r'^<br>|<br>$', '', new_replaced_content) 
            backtracking_html = replace_content(item,new_replaced_content,backtracking_html)
        return backtracking_html
    else:
        return '''<div id="container" style="padding:20pt;height: 75vh;overflow-y: scroll;background-color: #f5f5f5;">
                    <section class="docx" style="padding: 40pt 60pt;background-color: #FFFFFF;height:100%;">
                    <p style="text-align: center;"><span style="font-family: 宋体; min-height: 18pt; font-size: 18pt;">溯源</span></p>
                        <p style="text-align: center;">
                            <span style="font-family: 微软雅黑; font-weight: bold; min-height: 12pt; font-size: 12pt;">未查询到相关文件，请稍后重试^_^</span>
                        </p>
                    </section>
                </div>
                '''

def backtracking_turn_green(key_id,model_json,doctor_json):
    key_list = list(model_json[key_id].keys())
    key_list.remove('基本信息')
    key_list.remove('病人信息')
    key_list.remove('生命体征')
    key_list.remove('入院时简要病史')
    key_list.remove('体检摘要')
    # model_json[key_id]['出院后用药建议'] = re.sub('。 ', '。<br>', model_json[key_id]['出院后用药建议'])    # 实现分点效果

    for item in key_list:
        model_json[key_id][item],doctor_json[key_id][item] = word_turns_green(model_json[key_id][item],doctor_json[key_id][item])
    for item in list(model_json[key_id]['基本信息'].keys()):
        if item != '出院诊断':
            model_json[key_id]['基本信息'][item],_ = word_turns_green(model_json[key_id]['基本信息'][item],doctor_json[key_id]['患者基本信息'])
        else:
           model_json[key_id]['基本信息'][item],_ = word_turns_green(model_json[key_id]['基本信息'][item],doctor_json[key_id]['出院诊断'])
    for item in list(model_json[key_id]['生命体征'].keys()):
        model_json[key_id]['生命体征'][item],_ = word_turns_green(model_json[key_id]['生命体征'][item],doctor_json[key_id]['患者基本信息'])
    model_json[key_id]['入院时简要病史'],_ = word_turns_green(model_json[key_id]['入院时简要病史'],doctor_json[key_id]['患者基本信息'])
    model_json[key_id]['体检摘要'],_ = word_turns_green(model_json[key_id]['体检摘要'],doctor_json[key_id]['患者基本信息'])
    return model_json

def load_model_to_backtracking_html(key_id=key_id):
    template_name = "template_red"
    if now_mode in ['quankeshi']:
        title = '大模型版-出院小结'
        file_name = f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_postprocessed.json" 
        backtracking_file_name = f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_findsource.json"

    if os.path.exists(file_name):
        model_content = read_json(file_name)
        reference_content = read_json(backtracking_file_name)
        model_json = backtracking_turn_green(key_id,model_content,reference_content)
        html_content = single_json_to_html(model_json,key_id,html_name = template_name,title=title)
        return html_content
    else:
        return  f'''<div id="container" style="padding:20pt;height: 75vh;overflow-y: scroll;background-color: #f5f5f5;">
                    <section class="docx" style="padding: 40pt 60pt;background-color: #FFFFFF;height:100%;">
                        <p style="text-align: center;"><span style="font-family: 宋体; min-height: 18pt; font-size: 18pt;">{title}</span></p>
                        <p style="text-align: center;">
                            <span style="font-family: 微软雅黑; font-weight: bold; min-height: 12pt; font-size: 12pt;">未查询到相关文件，请稍后重试^_^</span>
                        </p>
                    </section>
                </div>
                '''

def load_two_html(key_id=key_id):
    global model_generated_path,doctor_generated_path,keshi
    set_value('key_id',key_id)
    if now_mode == 'quankeshi':
        model_file_path = f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_postprocessed.json"
        doctor_file_path = f"./{doctor_generated_path}/{keshi}/{key_id}/{key_id}.json"
        # 溯源页面
        backtracking_html = load_backtracking_html_wjc(key_id)
        model_bactracking_html = load_model_to_backtracking_html(key_id)
    else:
        model_file_path = f"./{model_generated_path}/{key_id}.json"
        doctor_file_path = f"./{doctor_generated_path}/{key_id}.json"
        # 溯源页面
        backtracking_html = load_backtracking_html(key_id)
    # 如果两种出院小结都有，就将匹配文字变绿
    if os.path.exists(model_file_path) and os.path.exists(doctor_file_path):
        model_json,doctor_json = string_matching(model_file_path,doctor_file_path,key_id)
        model_content = single_json_to_html(model_json,key_id,html_name='template_red_comparison',title='大模型版-出院小结')
        doctor_content = single_json_to_html(doctor_json,key_id,title='医生版-出院小结')
    else:
        model_content = read_html_with_key_id(key_id)
        doctor_content = read_html_with_key_id(key_id,prefix='医生示例')
    return model_content,model_bactracking_html,doctor_content,backtracking_html
