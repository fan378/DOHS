# 需要修改的内容
start_num=30 # 抽取从第start_num个病人到第end_num个病人的csv文件
end_num=60
zylsh='-2'      #如果设置为-1，一个科室下所有病例都生成;设置成-2，处理start_num到end_num个病人的csv文件
# keshi_list=('yanke' 'zhongyike' 'neifenmi' 'xiaohuaneike' 'huxineike' 'shenjingneike' 'shenzangneike' 'ruxianwaike' 'fuke' 'jiazhuangxianxueguanwaike' 'zhongliuke' 'xiaoerke' 'erbihouke' 'shenjingwaike' 'weichangwaike')
keshi_list=('ruxianwaike') 
zylsh='19030700000328'
data_type='1' # 0是批量训练数据 1是批量测试数据 -1是单个病人
# 19031500000377  19031600000179 19031600000188 19031600000203 19031600000127 19031800000446
# 21012100000198 19030700000328
# ['21012300000318','21012300000256','21012200000223','21012100000310','21012000000368']
# 使用for循环遍历数组  
for keshi in "${keshi_list[@]}"  
do  
    # echo "$keshi"  
    # ##################################################################
    # # 抽取病人
    # echo "抽取病人源文件"
    # csv_dir='../病人原始数据'
    # python get_patients_csv.py $keshi $zylsh $start_num $end_num $csv_dir

    # # 处理csv文件
    # echo "处理源文件"
    # processed_out_dir='./processed' # new_最终合并......
    # python process_csv.py $csv_dir $keshi $zylsh $processed_out_dir


    # echo "$keshi"  
    # ###################################################################
    # data_dir='../病人原始数据' 
    # processed_out_dir='./processed' # new_最终合并......
    # processed_out_dir='/HL_user01/processed_emr_datas/' # new_最终合并......
    # # 处理源文件
    # echo "处理源文件"
    # python process_csv.py $data_dir $keshi $zylsh $processed_out_dir

    # # ins_out_dir='/HL_user01/2024_03_24_生成出院小结_演示/自动生成出院小结/指令数据'
    # ins_out_dir='./instructions_202407'
    # # ins_out_dir='./批量数据_instructions_202407'
    # # ins_out_dir='./批量数据_instructions_202407_wjc'
    # # ins_out_dir='./批量数据_instructions_202407_test'

    # # 生成指令数据
    # echo "生成指令数据"
    # python py_cyxj_202407_gys.py $processed_out_dir $keshi $zylsh $ins_out_dir $data_type
    # # python py_cyxj_20240706_yc_copy.py $processed_out_dir $keshi $zylsh $ins_out_dir $data_type
    # # python py_cyxj_2024_0324_change.py $processed_out_dir $keshi $zylsh $ins_out_dir $data_type


    # model_path='/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
    # generate_out_dir='/HL_user01/2024_03_24_生成出院小结_演示/自动生成出院小结/模型生成结果'
    # model_path='/data/wangjiacheng/瑞金/1228_测试/export_models/chuyuanxiaojie_1201'
    generate_out_dir='./model_generated_test'
    # # 调用模型
    # echo "调用模型"
    # gpu='cuda:0'
    # python pipeline_wjc.py $ins_out_dir $keshi $zylsh $generate_out_dir $model_path $gpu

    # 后处理
    echo "后处理"
    python postprocess_fff.py $generate_out_dir $keshi $zylsh $generate_out_dir
done

