#### how to call random sat sampler for different variable amounts

### general form
# python -m language_fragments random_sat_sampler \
#        --n 5 \ # number of variables to sample from
#        --m "17;18;19;20;21;22;23;24;25;26;27;28;29;30;32;34;36" \ ## cluase sizes to consider (search limited to this)
#        --num_examples "14000" \
#        --min_examples "9000" \ ## for plotting purpose, number to compute from
#        --sample_name "v=5_non" \
#        --synthesize_to_non_nl \
#        --print_data \
#        --no_repeats ## important parameter for standard sampling, excludes clauses with repeated variables

### other settings: `--interpolate_param p`, for interpolating with 2SAT, set `p=0.0` to generate 2SAT. 

#########################################################################################
# BELOW ARE THE EXACT CALLS USES TO GENERATE THE RAW RANODM 3SAT DATA FOR OUR DATASETS  #
#########################################################################################

### 5
python -m language_fragments random_sat_sampler --n 5  --m "17;18;19;20;21;22;23;24;25;26;27;28;29;30;32;34;36" --num_examples "14000" --min_examples "9000" --sample_name "v=5_non" --synthesize_to_non_nl --print_data --no_repeats
### 7
python -m language_fragments random_sat_sampler --n 7  --m "22;23;25;26;27;28;29;30;31;32;33;34;35;36;37;39;42;43;45;47"  --num_examples "12000" --min_examples "9000" --sample_name "v=7_non" --synthesize_to_non_nl --print_data --no_repeats
### 8
python -m language_fragments random_sat_sampler --n 8 --m "25;29;30;32;33;34;35;36;38;39;40;41;42;46;49;53" --num_examples "15000" --min_examples "9000" --sample_name "v=8_non" --synthesize_to_non_nl --print_data --no_repeats
### 10
python -m language_fragments random_sat_sampler --n 10 --m "38;40;41;42;44;45;46;47;49;50;51;52;53;54;55;57;58;59"  --num_examples "18000" --min_examples "9000"  --sample_name "v=10_non" --synthesize_to_non_nl --print_data --no_repeats
### 12
python -m language_fragments random_sat_sampler --n 12 --m "44;46;50;52;57;58;59;60;62;65;68;72;76"  --num_examples "18000" --min_examples "9000"  --sample_name "v=12_non" --synthesize_to_non_nl --print_data --no_repeats
