**操作流程：**

1. 将run.sh的第21行替换成训练好的模型地址
2. `sh run.sh`，直至生成完毕
3. 进入result文件夹下即可看到生成结果：model_generated为模型最终生成结果，doctor_generated为医生的书写结果 



**文件内容说明：**

- 出院小结及子字段：一些用来辅助生成的文件，包括指令模板等
- data：病人的原始病历数据
- Intermediate_process：中间处理结果，包括预处理的病历数据（processed）和生成指令（instructions）
- pipeline_quankeshi：数据预处理、指令生成、小结生成、格式处理等代码
- result：模型生成的小结和医生小结
- run.sh: 一键式生成脚本
