1. 源文件处理完，放入`/HL_user01/2024_03_24_生成出院小结_演示/自动生成出院小结/源文件/**指定科室**/**自定义文件名**`下
2. 在`/HL_user01/2024_03_24_生成出院小结_演示/自动生成出院小结/scripts`目录下
3. 查看目录下的`run.sh`文件，修改前两行(定义的文件名和科室)，zylsh为-1表示该科室的全部生成
4. `conda activate llama_factory`
5. `bash run.sh`，直至生成完毕
6. `cd /HL_user01/2024_03_24_生成出院小结_演示/演示`
7. `python test.py`
8. 浏览器打开`http://localhost:7860/`，左下角选择住院流水号，点击`出院小结`条目，查看


传输文件：
global_variable.py, readme.md, run.sh, test.py

添加文件夹：
非必须：flagged,源文件
必须：commons, instructions,model_generated,original_csv,processed, 出院小结及子字段

添加文件:
脱敏修复.txt, pipeline_wjc.py, postprocess_wjc.py, py_cyxj_2024_0324.py, template_backtracking.html, template_highlight.html, template_red.html, template.html, transfer_keys.txt ,process_ori_datas_1, pipeline4simple, pipeline4fuza, get_instructions_1201 


