# 需要修改的内容
start_num=6 # 抽取从第start_num个病人到第end_num个病人的csv文件
end_num=100
zylsh='-2'      #如果设置为-1，一个科室下所有病例都生成;设置成-2，处理start_num到end_num个病人的csv文件
# keshi_list=('yanke' 'zhongyike' 'neifenmi' 'xiaohuaneike' 'huxineike' 'shenjingneike' 'shenzangneike' 'ruxianwaike' 'fuke' 'jiazhuangxianxueguanwaike' 'zhongliuke' 'xiaoerke' 'erbihouke' 'shenjingwaike' 'weichangwaike')
keshi_list=('ruxianwaike') 
zylsh='21012600000287'  
  
# 使用for循环遍历数组  
for keshi in "${keshi_list[@]}"  
do  
    echo "$keshi"  
    ##################################################################
    # 抽取病人
    echo "抽取病人源文件"
    csv_dir='./original_csv'
    python get_patients_csv.py $keshi $zylsh $start_num $end_num $csv_dir

    # 处理csv文件
    echo "处理源文件"
    processed_out_dir='./processed' # new_最终合并......
    python process_csv.py $csv_dir $keshi $zylsh $processed_out_dir

    # 生成指令数据
    echo "生成指令数据"
    ins_out_dir='./instructions'
    python py_cyxj_2024_0324_change.py $processed_out_dir $keshi $zylsh $ins_out_dir

    # 调用模型
    echo "调用模型"
    gpu='cuda:0'
    generate_out_dir='./model_generated'
    model_path='/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
    CUDA_VISIBLE_DEVICES=2 python pipeline_wjc.py $ins_out_dir $keshi $zylsh $generate_out_dir $model_path $gpu

    # 后处理
    echo "后处理"
    CUDA_VISIBLE_DEVICES=2 python postprocess_wjc.py $generate_out_dir $keshi $zylsh $generate_out_dir

    # 抽取医生出院小结
    echo "抽取医生出院小结"
    doctor_dir='./doctor_generated'
    python get_doctor_cyxj.py $zylsh $keshi $processed_out_dir $doctor_dir
    
done

