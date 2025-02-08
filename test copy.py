import os
# from transformers import AutoModel, AutoTokenizer
import gradio as gr
import json
import global_variable
import subprocess
import sys
import pipeline4fuza
import pipeline4simple
from datetime import datetime, timedelta
import threading
import warnings
import process_ori_datas_1
import get_instructions_1201
import py_cyxj_2024_0324
import process_csv
import pipeline_wjc
import postprocess_wjc
import shutil
import gc
import re
import jsonlines
warnings.filterwarnings("ignore")

def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

def create_empty_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)

def delete_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def upload_file(file):
    # path = file.name
    if which_model == 'ruxianwaike_singlecuda' or which_model == 'ruxianwaike':
        create_empty_dir('乳腺外科示例')
        for item in file:
            src_file = item.name
            dest_file = '乳腺外科示例/'+src_file.split('/')[-1]
            shutil.move(src_file, dest_file)
        data_dir = '乳腺外科示例'
        out_dir = 'processed'
        df_datas,json_datas = process_ori_datas_1.process_and_merge(data_dir,out_dir)
        global_variable.set_value('key_id',next(iter(json_datas)))
        global_variable.set_value('file_path',out_dir + '/合并.json')
    elif which_model == 'quankeshi':
        temp_input_csv_path = './temp/input_csv_path'
        temp_processed_path = './temp/processed_path'
        create_empty_dir(temp_input_csv_path)
        create_empty_dir(temp_processed_path)
        for item in file:
            src_file = item.name
            dest_file = f'{temp_input_csv_path}/'+src_file.split('/')[-1]
            shutil.move(src_file, dest_file)
        merged_df,json_datas,cyxjs = process_csv.process_and_merge(temp_input_csv_path,temp_processed_path)
        zylsh = next(iter(json_datas))
        global_variable.set_value('key_id',zylsh)
        processed_out_dir = global_variable.get_value('processed_out_dir')
        keshi = global_variable.get_value('keshi')
        print(processed_out_dir,keshi, zylsh)
        processed_out_path = os.path.join(processed_out_dir,keshi, zylsh)
        create_dir(processed_out_path)
        for filename in os.listdir(temp_processed_path):
            shutil.copy(os.path.join(temp_processed_path,filename), processed_out_path) 

    return json.dumps(json_datas,indent=4,ensure_ascii=False)

def get_time():
    # now = datetime.now() + timedelta(hours=8)
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

def capture_stdout_and_append_to_array(text):
    global std_out_list
    # 解码并将结果添加到数组中
    if text.strip():
        text = re.sub('\n',f'\n{get_time()}:',text)
        std_out_list.append(f'{get_time()}:{text}\n')

def current_stdout():
    def inner():
        global std_out_list
        current_time = get_time()
        if std_out_list == []:
            return str(current_time)
        else:
            return ''.join(std_out_list)
    return inner

def generate_file():
    global std_out_list

    original_write = sys.stdout.write
    sys.stdout.write = capture_stdout_and_append_to_array

    current_time = get_time()
    std_out_list =[]
    std_out_list.append(f"{current_time}:文件提交成功\n")

    # 读取全局变量
    key_id = global_variable.get_value('key_id')
    file_path = global_variable.get_value('file_path')

    # 转指令数据
    if which_model == 'ruxianwaike_singlecuda' or which_model == 'ruxianwaike':
        data_dir = './processed/new_最终处理并合并后数据.csv'
        out_dir = './instructions'
        ins_datas_v1201 = get_instructions_1201.get_instructions_v1201(data_dir,out_dir,'ruxianwaike')
    elif which_model == 'quankeshi':
        zylsh = global_variable.get_value('key_id')
        keshi = global_variable.get_value('keshi')
        processed_out_dir = global_variable.get_value('processed_out_dir')
        csv_data_path = os.path.join(processed_out_dir,keshi,zylsh,'new_最终处理并合并后数据.csv')
        ins_out_dir = global_variable.get_value('ins_out_dir')
        exact_ins_out_dir = os.path.join(ins_out_dir,keshi,zylsh)
        ins_datas_v2024_0324 = py_cyxj_2024_0324.get_instructions_v2024_0324(csv_data_path,exact_ins_out_dir,keshi)

    if which_model == 'ruxianwaike_singlecuda': # 单卡乳腺外科推理
        singlemodel,singletokenizer = global_variable.load_model('model1',cuda_DEVICE[0])
        # 执行命令
        thread1 = threading.Thread(target=pipeline4fuza.main, args=(singlemodel,singletokenizer,key_id,file_path))
        thread1.start()
        thread1.join()
        # 清除空间
        del singlemodel,singletokenizer
        gc.collect()
        # 训练后模型
        singlemodel,singletokenizer = global_variable.load_model('model2',cuda_DEVICE[0])
        thread2 = threading.Thread(target=pipeline4simple.main, args=(singlemodel,singletokenizer,ins_datas_v1201,key_id))
        thread2.start()
        thread2.join()
        # 合并处理结果
        cmd = 'python pipeline_total.py '+ key_id + ' \\'  
        result = subprocess.Popen(cmd,shell=True,close_fds=True)
        result.wait()
    elif which_model == 'ruxianwaike': # 双卡乳腺外科推理
        # 执行命令
        thread1 = threading.Thread(target=pipeline4fuza.main, args=(model1,tokenizer1,key_id,file_path))
        thread2 = threading.Thread(target=pipeline4simple.main, args=(model2,tokenizer2,ins_datas_v1201,key_id))
        # 启动线程
        thread1.start()
        thread2.start()
        # 等待线程完成
        thread1.join()
        thread2.join()
        # 合并处理结果
        cmd = 'python pipeline_total.py '+ key_id + ' \\'  
        result = subprocess.Popen(cmd,shell=True,close_fds=True)
        result.wait()
    elif which_model == 'quankeshi':
        global quankeshi_model,quankeshi_tokenizer
        generate_out_dir = global_variable.get_value('generate_out_dir')
        read_dir = os.path.join(generate_out_dir,keshi,zylsh)
        now_out_dir = os.path.join(generate_out_dir,keshi,zylsh)
        now_out_data_dir = os.path.join(generate_out_dir,keshi)
        pipeline_wjc.main(quankeshi_model,quankeshi_tokenizer,ins_datas_v2024_0324,zylsh,now_out_dir)
        postprocess_wjc.postprocess(zylsh,read_dir,now_out_dir,now_out_data_dir)
    # 存储测试用例
    if key_id not in example_list:
        example_list.append(key_id)
    example_list.sort()

    print('结束')
    sys.stdout.write = original_write
    return gr.update(choices=example_list,value=key_id)

def open_file(prefix, example_path = '演示示例'):
    key_id = global_variable.get_value('key_id')
    if prefix == '整体结果':
        prefix=''
    file_name = f"./{example_path}/{prefix}{key_id}.json"
    if os.path.exists(file_name):
        with open(file_name,'r',encoding='utf8') as f:
            content = json.load(f)
            content = json.dumps(content,indent=4,ensure_ascii=False)    
        return content
    else:
        return '模型正在努力生成，请稍后再试^_^'

def reset_stdout():
    global std_out_list
    std_out_list = []
    return ''

def addDoctorExample(file):
    for item in file:
        src_file = item.name
        with open(src_file,'r',encoding='utf-8') as f:
            json_data = json.load(f)
            key_id = next(iter(json_data))
            if key_id not in example_list:
                example_list.append(key_id)
            example_list.sort()
            # json_data[key_id] = json_data[key_id]['出院小结']
        if which_model == 'ruxianwaike' or which_model == 'ruxianwaike_singlecuda':
            with open(f'医生示例/{key_id}.json','w',encoding='utf-8') as f:
                json.dump(json_data,f,indent=4,ensure_ascii=False)
        elif which_model == 'quankeshi':
            doctor_generated_path = global_variable.get_value('doctor_generated_path')
            keshi = global_variable.get_value('keshi')
            create_dir(os.path.join(doctor_generated_path,keshi,key_id))
            with open(f'{doctor_generated_path}/{keshi}/{key_id}/{key_id}.json','w',encoding='utf-8') as f:
                json.dump(json_data,f,indent=4,ensure_ascii=False)
    return  gr.update(choices=example_list,value=key_id)

def change_showing_mode(value,html_content_doctor,html_content_backtrack):
    if value == '出院小结对比':
        return gr.update(visible=True,value=html_content_doctor),gr.update(visible=False,value=html_content_backtrack)
    elif value == '出院小结溯源':
        return  gr.update(visible=False,value=html_content_doctor),gr.update(visible=True,value=html_content_backtrack)

def delete_patient(key_id):
    keshi = 'ruxianwaike'
    processed_out_dir = global_variable.get_value('processed_out_dir')
    ins_out_dir = global_variable.get_value('ins_out_dir')
    delete_dir(f'./{model_generated_path}/{keshi}/{key_id}')
    delete_dir(f'./{doctor_generated_path}/{keshi}/{key_id}')
    delete_dir(f'./{processed_out_dir}/{keshi}/{key_id}')
    delete_dir(f'./{ins_out_dir}/{keshi}/{key_id}')
    example_list.remove(key_id)
    return gr.update(choices=example_list,value=example_list[0])

head="""
<script>
function highlightText(id) {
    var elements = document.querySelectorAll('#'+id);

    elements.forEach(function(element) {
    element.classList.add('highlight');
    });
}

function removeHighlight(id) {
    var elements = document.querySelectorAll('#'+id);

    elements.forEach(function(element) {
    element.classList.remove('highlight');
    });
}
</script>"""

if __name__ == '__main__':
    global_variable._init()
    global_variable.set_value('key_id','21012700000304')
    global_variable.set_value('file_path','./processed/合并.json')
    global_variable.set_value('keshi','ruxianwaike')
    global_variable.set_value('processed_out_dir','./processed')
    global_variable.set_value('ins_out_dir','./instructions')
    global_variable.set_value('generate_out_dir','./model_generated')

    # 用全科室模型还是乳腺外科科室模型 
    # 选项：[ruxianwaike, ruxianwaike_singlecuda, quankeshi] 
    # 分别代表 [双卡乳腺外科，单卡乳腺外科，单卡全科室]
    which_model = 'quankeshi' 
    # 空闲显卡列表，单卡时默认使用第0个值
    cuda_DEVICE = ['cuda:5','cuda:6']

    if which_model == 'quankeshi':
        quankeshi_model,quankeshi_tokenizer = global_variable.load_model('model_wjc',cuda_DEVICE[0])
        model_generated_path = global_variable.get_value('generate_out_dir')
        global_variable.set_value('model_generated_path',model_generated_path)
        global_variable.set_value('doctor_generated_path','doctor_generated')
        doctor_generated_path = global_variable.get_value('doctor_generated_path')
    elif which_model == 'ruxianwaike':
        model1,tokenizer1 = global_variable.load_model('model1',cuda_DEVICE[0]) # 原始模型
        model2,tokenizer2 = global_variable.load_model('model2',cuda_DEVICE[1]) # 训练后模型
        model_generated_path = '演示示例'
        doctor_generated_path = '医生示例'

    global_variable.set_value('now_mode',which_model)

    global std_out_list
    std_out_list = []

    keshi_list = os.listdir(f'./{model_generated_path}')
    keshi_zylsh = {}
    for keshi in keshi_list:
        example_list = []
        for zylsh in os.listdir(f'./{model_generated_path}/{keshi}'):
            if zylsh == '19031800000446_copy':
                continue
            for filename in os.listdir(f'./{model_generated_path}/{keshi}/{zylsh}'):
                pattern = r'^\d+\.json'
                if re.match(pattern, filename) and filename.lower().endswith('.json'):
                    example_list.append(filename[:-5])
            example_list.sort()
            keshi_zylsh[keshi] = example_list
    # print(example_list)
    # example_list = ["19122700000134","19030600000321",
    #                 "20010700000351","20102900000475","20122600000183"]
    # model_html,doctor_html,backtracking_html = global_variable.load_two_html(example_list[5],model_generated_path,doctor_generated_path)

    with gr.Blocks(css="custom.css",head=head) as demo:                
        with gr.Row():
            with gr.Column(scale=6,variant="panel"):
                with gr.Tab("数据预览") as Tab1:
                    file_content = gr.JSON(label="预览",elem_classes='container')
                with gr.Tab("进度概览") as Tab2:
                    user_input1 = gr.Textbox(show_label=False, placeholder="Input...",container=False,lines=40,max_lines=40,
                        value=current_stdout(),every=1,elem_classes='container')
                with gr.Tab("出院小结") as Tab3:
                    with gr.Row():           
                        with gr.Column(scale=2):
                            html_content= gr.HTML(value="Callable",elem_classes='container1',label='大模型结果') 
                        with gr.Column(scale=2):
                            html_content_doctor = gr.HTML(value="Callable",elem_classes='container1',label='医生结果',visible=False)
                            html_content_backtrack = gr.HTML(value="Callable",elem_classes='container1',label='溯源')

        with gr.Row(equal_height=True):
            keshi_table_list = gr.Dropdown(keshi_list,value=keshi_list[0],label='科室',allow_custom_value=False,
                                         container=False,show_label=False,min_width=60)
            table_colomn_1 = gr.Dropdown(choices=None,value=example_list[0],label='病人',allow_custom_value=False,
                                         container=False,show_label=False,min_width=60)
            radio = gr.Radio(['出院小结对比','出院小结溯源'],value='出院小结溯源',show_label=False,container=False,scale=2)
            addDoctorExample_button = gr.UploadButton("上传医生版出院小结", file_types=["file"],variant="primary",file_count='multiple')
            upload_button = gr.UploadButton("上传原始材料", file_types=["file"],variant="primary",file_count='multiple')
            submit_button = gr.Button(value="提交原始材料",variant="primary")
            delete_button = gr.Button(value="删除用例")

        upload_button.upload(upload_file, upload_button, file_content)
        submit_button.click(generate_file,[],[table_colomn_1],show_progress=True)
        delete_button.click(delete_patient,[table_colomn_1],[table_colomn_1],show_progress=True)
        addDoctorExample_button.upload(addDoctorExample, addDoctorExample_button, [table_colomn_1])

        table_colomn_1.change(global_variable.load_two_html, [table_colomn_1],[html_content,html_content_doctor,html_content_backtrack])
        radio.change(change_showing_mode,[radio,html_content_doctor,html_content_backtrack],[html_content_doctor,html_content_backtrack])
        
    demo.queue().launch(show_api= False,share=False, server_name="0.0.0.0", server_port=7861, inbrowser=False)
