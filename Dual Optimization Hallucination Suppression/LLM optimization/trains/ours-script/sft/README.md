[**English**](./README.md) | [**中文**](./README_zh.md)

1. The running order is from stage1 to stage4.
2. run `bash 1_chatglm_cache_stage1.sh` to load and tokenize the datasets, then it will save the tokenized datast to `tokenized_path`.
3. run `bash 2_chatglm_train_stage1_lora.sh` to start pretraining, make sure the `tokenized_path` parameter is the same as the one in `1_chatglm_cache_stage1.sh`, the pretrained model will be saved at `output_dir`.