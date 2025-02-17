# Discharge-Summary
Discharge summaries (DSs) are crucial in clinical healthcare, but existing research faces challenges such as inadequate optimization of large medical models, hallucinations caused by lengthy information, and difficulties in usage due to high customization. To address these issues, we propose a Dual Optimization Hallucination Suppression framework (DOHS), combining electronic medical record large language model (EMR-LLM) instruction tuning and Prompt Hallucination Suppression (PHS) strategies. First, the DOHS improves numerical sensitivity through six instruction tasks, then, splits sub-fields to focus on key information, and effectively handles the large volume of medical information. Finally, it uses logical template combinations to resolve the challenges of high customization, making it easier for doctors to use. Extensive experiments validate the effectiveness of our approach. 
# Brief introduction
(1) We propose a novel DOHS framework, including EMR-LLM instruction tuning and PHS strategies. EMR-GPT, as the first multi-department clinical business LLM, enhances the LLM's sensitivity to numerics by the design of six instruction tasks, effectively suppressing hallucinations.
(2) We introduce a novel PHS strategy to optimize LH and LoH, controlling input length through subfield splitting, enhancing reasoning consistency with logical templates and a knowledge base, and suppressing hallucinations from long texts and logical combinations.
(3) We validate the DOHS framework through large-scale experiments, with all results reaching SOTA performance. EMR-GPT achieves 95.78\% on the discharge status task, a 1.43\% improvement over pure manual reasoning, demonstrating the effectiveness of logical template combinations. This significantly suppresses hallucinations and enhances the accuracy and clinical usability of DSs.
![framework](https://github.com/user-attachments/assets/2ec78978-7c83-44e1-a37a-1b9339aa83bc)


# Requirements
# Instruction fine-tuning
```python
To run our code, please install dependency packages.
accelerate	    0.27.2
deepspeed	    0.14.2
fire	        0.5.0
flash-attn	    2.5.8
ninja	        1.11.1.1
sentencepiece	0.1.99
torch	        2.2.1
vllm	        0.4.1
peft	        0.10.0
trl	            0.8.1
datasets    	2.17.1	
transformers	4.40.0	
scipy	        1.12.0
tiktoken    	0.6.0	
protobuf	    3.20.3	
pydantic    	2.6.1	
matplotlib	    3.8.3	
sse-starlette	2.0.0	
packaging	    23.2	
pyyaml      	6.0.1
pandas	        1.5.3
numpy	        1.23.4
```

# Code Structure
./Complete process:The dictory of system code.

./Optimized block/LLM optimization:The directory of fine-tuning code.

./Optimized block/Prompt optimization:The directory of length control and logic templates code.


# Pre-training
```python
# go to the directory
cd Optimized block/LLM optimization/train/LLaMA-Factory/ours-script/pretrain

# get the dataset cache
bash 1_get_cache.sh

# start pre-training
bash 2_start_pretrain.sh
```

# SFT
```python
# go to the directory
cd Optimized block/LLM optimization/train/LLaMA-Factory/ours-script/sft

# get the dataset cache of stage1 to stage4
bash 1_chatglm_cache_stage1.sh
bash 1_chatglm_cache_stage2.sh
bash 1_chatglm_cache_stage3.sh
bash 1_chatglm_cache_stage4.sh

# start sft stage by stage
bash 2_chatglm_train_stage1_lora.sh
# Modify Configuration
bash /train/LLaMA-Factory/ours-script/export_lora_model.sh
bash 2_chatglm_train_stage2_lora.sh
# Modify Configuration
bash /train/LLaMA-Factory/ours-script/export_lora_model.sh
bash 2_chatglm_train_stage3_lora.sh
# Modify Configuration
bash /train/LLaMA-Factory/ours-script/export_lora_model.sh
bash 2_chatglm_train_stage4_lora.sh
# Modify Configuration
bash /train/LLaMA-Factory/ours-script/export_lora_model.sh
```

# Prompt optimization
```python
key_desps = {
"Basic patient information": [
# Role
"You are a medical data processing expert, responsible for extracting basic patient information and generating structured records.",

# Task
"Extract basic information from the patient's input data, including name, gender, age, hospitalization number, bed number, ward name, admission date, admission diagnosis, etc., and calculate the patient's discharge time based on the doctor's order information.",

# Steps (disassembly)
"1. **Extract** the patient's basic information fields from the input data, including name, gender, age, hospitalization number, bed number, ward name, admission date, admission diagnosis, etc.;"
"2. Perform integrity check on each field. If the field is missing, mark it as 'missing' and add a description to the output;"
"3. According to the doctor's order content (such as 'discharged this afternoon', etc.), **inference** is performed through date information to calculate the accurate discharge time and add it to the record;"
"4. Extract the patient's vital signs data (such as blood pressure, heart rate, blood oxygen, etc.), extract the latest results from multiple records, and generate a brief summary; "
"5. Integrate all information and generate clear and standardized basic information output in the order of fields. ",

# Output format
"""
Patient basic information:
- Name: XXX
- Gender: XXX
- Age: XXX
- Hospitalization number: XXX
- Bed number: XXX
- Ward name: XXX
- Admission date: YYYY-MM-DD
- Admission diagnosis: XXX
- Discharge date (estimated): YYYY-MM-DD
- Vital signs:
1. Blood pressure: XXX
2. Heart rate: XXX
3. Blood oxygen: XXX
"""
],

"Discharge diagnosis": [
# Role
"You are a medical data analyst responsible for extracting and verifying the patient's discharge diagnosis information. ",

# Task
"Extract discharge diagnosis information from the patient's diagnosis and medical history records, and ensure that the diagnosis content meets the standardization requirements.",

# Steps (disassembly)
"1. **Extract** the core diagnosis content from the patient's discharge record, and ensure that the name conforms to the standardized diagnosis description;"
"2. If the diagnosis information contains additional descriptions (such as complications or notes), the relevant content needs to be extracted and marked in brackets after the diagnosis;"
"3. Logically organize the diagnosis content, remove redundant information, and ensure a clear structure;"
"4. Output the final discharge diagnosis record to ensure that the information is complete and standardized.",

# Output format
"""
Discharge diagnosis:
- Discharge diagnosis: XXX
- Supplementary description: XXX (if applicable)
"""
],

"Main test and examination results during hospitalization": [
# Role
"You are a medical information analyst responsible for extracting the test and examination data of patients during hospitalization and generating structured reports.",

# Task
"Extract medical data during hospitalization, focus on key test results and imaging examination content, and generate a clear summary of hospitalization medical conditions. ",

# Steps (disassembly)
"1. **Extract** all test records of the patient during hospitalization:"
" a. Extract normal test data and keep only the latest results;"
" b. Extract abnormal test data and keep the relevant records and analysis content in full;"
"2. **Extract** key content from the imaging report, including imaging type (such as CT, MRI) and core examination conclusions;"
"3. Organize the test and examination results, logicalize the data, and form a structured summary of the test and examination during hospitalization;"
"4. Check the accuracy of the extracted information to ensure that there are no omissions or logical errors in the results. ",

# Output format
"""
Main test results during hospitalization:
- Test information:
1. Normal test: XXX (latest result)
2. Abnormal test: XXX (complete record)
- Imaging examination:
- Type: XXX
- Conclusion: XXX
"""
],

"Course of illness and treatment": [
# Role
"You are a medical record analyst, responsible for extracting treatment information during hospitalization and generating medical reports. ",

# Task
"Analyze the patient's medical record, extract treatment methods (such as surgery, chemotherapy, etc.) and the description of the condition in the medical report, and generate structured medical and treatment records. ",

# Steps (disassembly)
"1. **Judge** whether the patient has received key treatment (such as surgery, chemotherapy, etc.), and extract the name, date and results of the relevant treatment methods;"
"2. **Extract** the description of the condition in the medical report, focusing on the changes in the condition and key symptoms;"
"3. Integrate the treatment information and the description of the condition in chronological order to ensure that the treatment record is logically consistent with the changes in the condition;"
"4. Summarize the information, extract the core content, and generate a clear structured medical record. ",

# Output format
"""
Medical course and treatment:
- Main treatment methods:
1. Surgery: XXX (yes/no)
2. Chemotherapy: XXX (yes/no)
- Description of the condition: XXX
- Summary of medical report: XXX
"""
],

"Discharge status": [
# Role
"You are a health record organizer, responsible for summarizing the health status of patients at discharge. ",

# Task
"Extract health status information from the patient's discharge record, including physical recovery, mental state, wound recovery, etc., and generate a discharge health summary. ",

# Steps (disassembly)
"1. **Judge** the description of health status in the discharge record, and analyze physical recovery, mental state and wound recovery;"
"2. According to the changes in the course of the disease during hospitalization, **infer** the patient's recovery trend (such as complete recovery, partial recovery, etc.);"
"3. Sort all health status information by category and generate a clear discharge health summary. ",

# Output format
"""
Discharge status:
- Physical recovery: XXX
- Mental state: XXX
- Wound condition: XXX
"""
],

"Post-discharge medication recommendations": [
# Role
"You are a medical medication analyst responsible for designing post-discharge medication recommendations for patients. ",

# Task
"Extract drug use recommendations from patient medical records, including the names, dosages, and precautions for conventional and special medications, and specify the patient's follow-up department. ",

# Steps (disassembly)
"1. **Extract** the patient's medication records, including conventional medications (such as maintenance treatment) and special medications (such as complication treatment);"
"2. **Judge** the rationality of drug use, and analyze whether the dosage and method of use need to be adjusted;"
"3. Based on medical records and diagnostic information, **infer or knowledge match** the patient's follow-up needs, and specify the corresponding follow-up department;"
"4. Extract drug-related precautions, indicate risk points or special care requirements;"
"5. Organize all medication recommendations and follow-up requirements to generate standardized structured output. ",

# Output format
"""
Medication recommendations after discharge:
- Conventional medication:
1. Drug name: XXX
2. Dosage: XXX
3. Medication time: XXX
- Special medication:
1. Drug name: XXX
2. Dosage: XXX
3. Medication time: XXX
- Precautions:
1. XXX
2. XXX
- Follow-up department: XXX
"""
]
}
```

# Run steps
Run Complete process/run.sh and wait for the build to complete.


