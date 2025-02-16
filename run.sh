# 需要修改的内容
zylsh='-1'      #如果设置为-1，一个科室下所有病例都生成
keshi_list=('yanke' 'zhongyike' 'neifenmi' 'xiaohuaneike' 'huxineike' 'shenjingneike' 'shenzangneike' 'ruxianwaike' 'fuke' 'jiazhuangxianxueguanwaike' 'zhongliuke' 'xiaoerke' 'erbihouke' 'shenjingwaike' 'weichangwaike')
keshi_list=('shenjingneike') 
zylsh='21011900000260'  
  
# 使用for循环遍历数组  
for keshi in "${keshi_list[@]}"  
do  
    echo "$keshi"  
    ###################################################################
    data_dir='../病人原始数据' 
    processed_out_dir='./processed' # new_合并......
    # 处理源文件
    echo "处理源文件"
    python process_csv.py $data_dir $keshi $zylsh $processed_out_dir

    # ins_out_dir='/HL_user01/2024_03_24_生成出院小结_演示/自动生成出院小结/指令数据'
    ins_out_dir='./instructions'
    # 生成指令数据
    echo "生成指令数据"
    python py_cyxj_2024_0324.py $processed_out_dir $keshi $zylsh $ins_out_dir

    model_path='/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
    # generate_out_dir='/HL_user01/2024_03_24_生成出院小结_演示/自动生成出院小结/模型生成结果'
    # model_path='/data/wangjiacheng/瑞金/1228_测试/export_models/chuyuanxiaojie_1201'
    generate_out_dir='./model_generated'
    # 调用模型
    echo "调用模型"
    gpu='cuda:0'
    python pipeline_wjc.py $ins_out_dir $keshi $zylsh $generate_out_dir $model_path $gpu

    # 后处理
    echo "后处理"
    python postprocess_wjc.py $generate_out_dir $keshi $zylsh $generate_out_dir
done

