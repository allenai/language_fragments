###
### CHANGE DIRECTORY UP TO `transformer_tools`
## cd ../../transformers_tools
### conda activate transformer_tools (assumes installation detailed there)

SEED=919   ### experimented with 42,919 and a few other
BATCH=8    ### expeimented with 8, 12, limited due to memory overhead 
LR=0.00005 ## experimented 2e-5 to 1e-6 
EPOCH=8    ### experimented with 8, 10 , 12
TWOSAT_MODEL=""  ### IMPORTANT, started checkpoint used for warmup, model can be downloaded at `../../etc/models/2sat_t5`
DATA_DIR=""      #### e.g., `../../etc/data/3sat/grounded_rule_lang/5var` for 5 variable problems

### other hyper-parameters in the model: adam optimizer, 

### grounded rule language, full dataset 
python -m  transformer_tools  T5Classifier \
       --output_dir /output \
       --wdir  /output \
       --data_dir ${DATA_DIR}  #<----- target dataset, containing (minimally) `{train,dev}.jsonl`
       --num_train_epochs  ${EPOCH} \
       --model_name_or_path  t5-large \      ##t5 model 
       --tokenizer_name_or_path  t5-large \  ### tokenzer
       --learning_rate  ${LR} \
       --train_batch_size  ${BATCH} \
       --seed  ${SEED} \
       --max_seq_len, "512" \
       --max_answer  "3" \
       --early_stopping \
       --patience  "10" \
       --num_beams  "2" \
       --no_repeat_ngram_size  "0" \
       --T5_type  T5ClassificationMultiQA \
       --data_builder  multi_qa \
       --remove_checkpoints \
       --eval_name iid \
       --model_name  t5_l_varcombined_big__2sat_pre_comb \
       --target_model ${TWOSAT_MODEL} #<---- 2SAT pre-trained model

### relative clause fragment
python  -m  transformer_tools  T5Classifier \
        --output_dir  /output \
        --data_dir  /inputs \
        --num_train_epochs ${EPOCH} \
        --model_name_or_path  t5-large \
        --tokenizer_name_or_path t5-large \
        --learning_rate  ${LR} \
        --train_batch_size  ${BATCH} \
        --seed "919" \
        --max_seq_len "512" \
        --max_answer  "20" \
        --early_stopping \
        --wdir  /output \
        --patience  "10" \
        --num_beams  "2" \
        --no_repeat_ngram_size "0" \
        --T5_type  T5ClassificationMultiQA \
        --data_builder  multi_qa \
        --remove_checkpoints \
        --eval_name  iid \
        --wandb_entity nlsat \
        --target_model ${TWOSAT_MODEL}

### other important settings: `--{dev,test}_eval` (for testing dev and test after training), `--print_output` (print model output when doing evaluation), `--no_training`

### EXAMPLE EVALUATION: below shows an example of how to run the code in evaluation mode, evaluation a 5_12 variable model from the paper on, e.g., 5var dev problems

EVAL_DATA_DIR= "" # ../../etc/data/3sat/grounded_rule_lang/5var
TRAINED_MODEL="" #../../etc/models/3sat_rule_lang_combined

python -m  transformer_tools  T5Classifier \
       --output_dir /output \
       --wdir  /output \
       --data_dir ${DATA_DIR}  #<----- target dataset, containing (minimally) `{train,dev}.jsonl`
       --num_train_epochs  ${EPOCH} \
       --model_name_or_path  t5-large \      ##t5 model 
       --tokenizer_name_or_path  t5-large \  ### tokenzer
       --learning_rate  ${LR} \
       --train_batch_size  ${BATCH} \
       --seed  ${SEED} \
       --max_seq_len, "512" \
       --max_answer  "3" \
       --early_stopping \
       --patience  "10" \
       --num_beams  "2" \
       --no_repeat_ngram_size  "0" \
       --T5_type  T5ClassificationMultiQA \
       --data_builder  multi_qa \
       --remove_checkpoints \
       --eval_name iid \
       --no_training \ ##<--------- turns off training
       --dev_eval \    ##<---------- says to run dev evaluation
       --print_output \ ###<------- print output
       --print_json \
       --model_name  t5_l_varcombined_big__eval_5var \
       --target_model ${TRAINED_MODEL} #<---- 2SAT pre-trained model
