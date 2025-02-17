# 需要修改的内容
keshi_list=('yanke' 'zhongyike' 'neifenmi' 'xiaohuaneike' 'huxineike' 'shenjingneike' 'shenzangneike' 'ruxianwaike' 'fuke' 'jiazhuangxianxueguanwaike' 'zhongliuke' 'xiaoerke' 'erbihouke' 'shenjingwaike' 'weichangwaike') # 要处理的科室
keshi_list=('ruxianwaike') 
zylsh='-1'  # 设置为具体流水号（例如：19010300000147）只生成单个病人，设置为-1则生成所有病人
  
# 使用for循环遍历数组  
for keshi in "${keshi_list[@]}"  
do  
    echo "$keshi"  
    ###################################################################
    
    # 数据预处理
    echo "数据预处理"
    data_dir='data/病人原始数据'
    processed_out_dir='Intermediate_process/processed'
    docotr_dir="results/doctor_generated"
    python pipeline_quankeshi/process_csv.py $data_dir $keshi $zylsh $processed_out_dir $docotr_dir

    # 生成指令数据
    echo "生成指令数据"
    ins_out_dir='Intermediate_process/instructions'
    python pipeline_quankeshi/py_cyxj_2024_0324_change.py $processed_out_dir $keshi $zylsh $ins_out_dir

    # 调用模型
    echo "调用模型"
    model_path='/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
    generate_out_dir='results/model_generated'
    gpu='cuda:7'
    python pipeline_quankeshi/pipeline_wjc.py $ins_out_dir $keshi $zylsh $generate_out_dir $model_path $gpu

    # 后处理
    echo "后处理"
    python pipeline_quankeshi/postprocess_wjc.py $generate_out_dir $keshi $zylsh $generate_out_dir $model_path $gpu $processed_out_dir
done

