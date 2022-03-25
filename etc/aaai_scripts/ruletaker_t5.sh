### POINTERS FOR RULETAKER EXPERIMENTS
### CHANGE DIRECTORY UP TO `transformer_tools`
## cd ../../transformers_tools
### conda activate transformer_tools (assumes installation detailed there)


RULERTAKER= "" # point to ruletaker data "../../etc/data/ruletaker_3ext_sat/"

### same as
python  -m transformer_tools T5Classifier \
        --output_dir  /output \
        --data_dir  /inputs \
        --num_train_epochs  "8" \
        --model_name_or_path  t5-large \
        --tokenizer_name_or_path t5-large \
        --learning_rate  "0.00005" \
        --train_batch_size  "32" \
        --seed  "42" \
        --max_seq_len  "280" \
        --data_dir  ${RULETAKER}
        --max_answer "10" \
        --early_stopping
        --dev_eval \
        --wdir  /output \
        --patience  "2" \
        --num_beams  "2" \
        --print_output \
        --no_repeat_ngram_size  "0" \
        --T5_type  T5ClassificationMultiQA \
        --data_builder  multi_qa \
        --remove_checkpoints \
        #--wandb_data 'nlsat/random-ksat2/ruletaker_sat:v1' \
        --eval_name  iid \
        --model_name rule_taker_sat

### expected results in `metrics.json`
# {
#   "best_dev_score": 0.9754628932711125,
#   "dev_eval": 0.9754628932711125
# }

### evaluation the above model on hard ruletaker 
###
RULETAKER_MODEL="" ##<--- put pointer to wdir above containing trained model 
CHALLENGE_DATA=""  # point to ruletaker data "../../etc/data/hard_rule_taker/"

##
#python  -m  transformer_tools T5Classifier \
#         --output_dir /output \
#         --data_dir  ${CHALLENGE_DATA} \
#         --model_name_or_path t5-large \
#         --tokenizer_name_or_path  t5-large \
#         --max_seq_len "512" \ ## increased input length just in case
#         --max_answer  "3" \
#         --early_stopping \
#         --wdir  /output \
#         --num_beams  "2" \
#         --no_repeat_ngram_size "0" \
#         --T5_type  T5ClassificationMultiQA \
#         --data_builder  multi_qa \
#         --remove_checkpoints \
#         --eval_name  ruletaker_3sat_sampling \
#         --model_name  ruletaker_t5_3ext \
#         --target_model  ${RULETAKER_MODEL} \ ### use model from above
#         --no_training \ ## important: only do evaluation 
#         --dev_eval \
#         --eval_subdir / \
#         --print_output \
#         --print_json ### print output in json format

        
### expected results
# {
#   "best_dev_score": 0.5770135983263598,
#   "dev_eval": 0.5770135983263598
# }
