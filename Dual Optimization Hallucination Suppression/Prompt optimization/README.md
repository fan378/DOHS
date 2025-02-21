(1) Modify in template.py
```python
field_name = "Basic Information"
```
The fields are: basic information, discharge diagnosis, medical conditions during hospitalization, course of disease and treatment, conditions at discharge, and medication recommendations after discharge

Then run template.py to get the template prompt for each field. For example: The template prompt for basic information is as follows

Extraction: Extract the patient's medical history and chronic disease information from the medical record.
Judgment: Based on the patient's medical history and chronic disease information, determine whether the patient has a chronic disease.
Knowledge: Based on the patient's medical history and chronic disease information, if there is a chronic disease, match it with the knowledge base and get medication recommendations after discharge.
And so on for each field.

The logical template prompt is as follows:
```python
{
"Extraction": {
"description": "Used to directly extract structured information from medical records.",
"examples": [
"Directly extract the patient's name, gender, age, hospitalization number, bed number, ward name, admission date and other information from the medical record.",
"According to the diagnosis description in the medical document, directly extract the diagnosis information at the time of discharge.",
"Extract vital signs information and medical history content from the medical record.",
"Extract key results from the test and examination records, such as retaining the latest results of normal tests and all results of abnormal tests.",
"For post-operative conditions, extract relevant treatment information.",
"Extract the patient's medical history and chronic disease information."
]
},
"Summary": {
"description": "Used to summarize the text content and extract key information.",
"examples": [
"Summarize the vital signs information and medical history content obtained from the medical record.",
"Read and analyze the physical examination records, extract key information and form a summary.",
"Summarize the relevant treatment information obtained from the surgical situation during the treatment process."
]
},
"Judgement": {
"description": "Used to judge specific clinical situations."
"examples": [
"Judge whether surgery was performed during the treatment process."
"Judge the patient's overall condition based on the patient's recovery and medical records."
"Judge whether the patient has a chronic disease from the patient's medical history and chronic disease information obtained."
]
},
"Reasoning": {
"description": "Used to reason about results based on certain conditions."
"examples": [
"Based on the patient's recovery and medical records, infer the overall situation at the time of discharge."
"Combined with the discharge instructions and time in the doctor's order content, infer the discharge date and time."
]
},
"Knowledge": {
"description": "Based on the patient's medical history and chronic disease information matching the knowledge base, provide medication recommendations."
"examples": [
"Based on the patient's medical history and chronic disease information, if there is a chronic disease, it matches the knowledge base and obtains medication recommendations; otherwise, it does not match."
]
}
}

```

(2) Then use GPT-4o to combine the prompts of each field to obtain the final complete template prompt
```python
key_desps = {
"Basic patient information": [
# Role
"You are a medical data processing expert, responsible for extracting basic patient information and generating structured records.",

# Task
"Extract basic information from the patient's input data, including name, gender, age, hospitalization number, bed number, ward name, admission date, admission diagnosis, etc., and calculate the patient's discharge time based on the doctor's order information.",

# Steps (disassembly)
"1. **Extract** the patient's basic information fields from the input data, including name, gender, age, hospitalization number, bed number, ward name, admission date, admission diagnosis, etc.;"
"2. Perform integrity check on each field. If the field is missing, mark it as 'missing' and add a description in the output;"
"3. According to the content of the doctor's order (such as 'discharged this afternoon'), use the date information to **Inference**, calculate the accurate discharge time and add it to the record;"
"4. Extract the patient's vital signs data (such as blood pressure, heart rate, blood oxygen, etc.), extract the latest results from multiple records, and generate a brief summary;"
"5. Combine all information and generate clear and standardized basic information output in the order of fields. ",

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
# Roles
"You are a medical data analyst responsible for extracting and verifying the patient's discharge diagnosis information.",

# Task
"Extract discharge diagnosis information from the patient's diagnosis and medical records, and ensure that the diagnosis content meets the standardization requirements.",

# Steps (disassembly)
"1. **Extract** core diagnosis content from the patient's discharge record, ensuring that the name conforms to the standardized diagnosis description;"
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
"You are a medical information analyst responsible for extracting the test and examination data of patients during hospitalization and generating structured reports. ",

# Task
"Extract medical data during hospitalization, focus on key test results and imaging examination content, and generate a clear summary of hospitalization medical conditions. ",

# Steps (disassembly)
"1. **Extract** all test records of patients during hospitalization:"
" a. Extract normal test data and keep only the latest results;"
" b. Extract abnormal test data and keep relevant records and analysis content in full;"
"2. **Extract** key content from imaging examination reports, including imaging types (such as CT, MRI) and core examination conclusions;"
"3. Organize test and examination results, logicalize data, and form a structured summary of tests and examinations during hospitalization;"
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
2. Dose: XXX
3. Medication time: XXX
- Special medication:
1. Drug name: XXX
2. Dose: XXX
3. Medication time: XXX
- Notes:
1. XXX
2. XXX
- Follow-up department: XXX
"""
]
}
```

(3) Finally, the prompt obtained by the template is updated in py_cyxj_2024_0324_change.py to complete the processing of the length and logic template and optimize the prompt
