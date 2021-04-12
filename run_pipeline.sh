
###
#
# Demonstration of running full pipeline (minus analysis) on a single book
# Usage: ./run_pipeline.sh 1586
# Where 1586 refers to name of the tokens/1586.tokens file
# 1586.tokens is the tokens file output from running this book through BookNLP
#
# Dependencies for running the pipeline are: python3, pytorch, pytorch_pretrained_bert, numpy, pandas, networkX
###

base=$1

curDir=`pwd`
coref_dir=$curDir/coref
litbank_tagger=$curDir/mention_tagger
script_dir=$curDir/general_pipeline_scripts

base_dir=$curDir/output/tagger
mkdir -p $base_dir
mkdir $base_dir/$base

tokensFile=$curDir/tokens/$base.tokens

tagFile_layered=$litbank_tagger/prop.entity.tagset
entity_model_file=$litbank_tagger/prop.mentions.model
coref_model=$coref_dir/coref.model

output_prediction_file=$base_dir/$base/$base.ents
conllFile=$base_dir/$base/$base.to_predict.conll
coref_out=$base_dir/$base/$base.predicted.conll
coref_ent_file=$base_dir/$base/$base.predicted.conll.ents
qa_out=$base_dir/$base/$base.predicted.qa

cp $tokensFile $base_dir/$base

cd $litbank_tagger

python run_tagger.py --mode predict --tagFile_layered $tagFile_layered --modelFile $entity_model_file --input_prediction_file $tokensFile --output_prediction_file $output_prediction_file --ignoreEvents

# ent to conll

python $script_dir/ent2conll11.py $output_prediction_file $tokensFile $base > $conllFile

# coref

cd $coref_dir

python bert_coref.py --mode predict --model $coref_model --valData $conllFile --outFile $coref_out

# QA

python $script_dir/extractCharsFromConll.py $coref_out > $coref_ent_file

python $script_dir/quotation_attribution_conll.py $tokensFile $coref_ent_file $qa_out


# Info Prop pipeline

cd $curDir/info_prop_scripts

python char_co-occurence.py
python prop_results.py
python implicit_prop.py
python non_prop_b_nodes.py
python node_measures.py

