from py_cyxj_2024_0324_change import *

def get_cyxj_batch(data_dir,out_dir,keshi,start_num=0,end_num=-1,data_type=1): # datatype: 0是训练、1是测试
    if out_dir != "":
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    random.seed(2023)
    if isinstance(data_dir,str):
        datas = load_excel_csv(data_dir)
        datas.fillna("",inplace=True)
    else:
        datas = data_dir
    data_lengths = {}
    data_lengths[keshi] = {}
    data_maps = all_data_maps[keshi]
    for key in data_maps.keys():
        if key == "医嘱介绍" or key=="病程与治疗情况介绍":
            continue
        data_lengths[keshi][key] = defaultdict(int)

    model_dir = cons_model_dir
    # tokenizer = AutoTokenizer.from_pretrained(model_dir,trust_remote_code=True)

    partion = 0.85
    out_name = "出院小结及子字段.jsonl"
    delete_tokens = {
        "患者基本信息":99999,
        "住院期间医疗情况":99999,
        "出院诊断":99999,
        "病程与治疗情况":99999,
        "出院后用药建议":99999,
        "出院时情况":99999,
    }
    keep_nums = 0
    delete_nums = 0

    needs = int(datas.shape[0]*partion)
    if data_type == 0:
        datas = datas[:needs]
    elif data_type == 1:
        datas = datas[needs:]
        out_name = out_name.split('.')[0]+'_test.'+out_name.split('.')[1]

    datas = datas[start_num:end_num]

    for col in datas.columns[1:]:
        datas[col] = datas[col].apply(transfer_value)

    final_datas = []
    
    for i in tqdm(range(datas.shape[0])):
        res_data = build_data(i,datas.iloc[i,:].copy(),data_maps,data_lengths,keshi)
        # break
        if res_data == None:
            continue
        final_datas.extend(res_data)

    # print("keep_nums:{}\tdelete_nums:{}".format(keep_nums,delete_nums))

    with jsonlines.open(os.path.join(out_dir,out_name),"w") as f:
        for final_data in final_datas:
            f.write(final_data)
    return final_datas


if __name__ == "__main__":
    print("构造指令数据")
    data_dir = sys.argv[1]
    out_dir = sys.argv[2]
    keshi = sys.argv[3]
    data_type = int(sys.argv[4]) # 0是训练数据 1是测试数据 -1是单个病人
    start_num=int(sys.argv[5])
    end_num=int(sys.argv[6])
    data_dir = os.path.join(data_dir,keshi)
    data_name = "new_最终处理并合并后数据.csv"

    print("处理{}个病例".format(len(zylshs)))
    if data_type == 0 or data_type==1: # 批量生成数据
        csv_data_path = os.path.join(data_dir,data_name)
        now_out_dir = os.path.join(out_dir,keshi)
        get_cyxj_batch(csv_data_path,now_out_dir,keshi,data_type)
