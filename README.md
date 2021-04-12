# Measuring Information Propagation in Literary Social Networks

Code to support the paper ["Measuring Information Propagation in Literary Social Networks"](https://www.aclweb.org/anthology/2020.emnlp-main.47/)

The code included here can be used to run the full pipeline (minus analysis scripts - to be added soon) on a single book.
With minimal adaptation, this code can also be used to run the pipeline on a full corpus. 

To download the entity recognition and coref models fist run: 
> python download_models.py
The models will automatically be saved in the correct locations. 

Then to run the full pipeline on an included example novel, run the following script from the command line:
> ./run_pipeline.sh 1586

1586 refers to the 1586.tokens file that's been included in the tokens folder.
This file is the output of running the selected novel through BookNLP. Note a BookNLP tokens file input is a prerequisite for running the pipeline. Code and directions for using BookNLP can be found [here](https://github.com/dbamman/book-nlp).

Finally, all output from running the pipeline script can be found in the resulting **output** folder.
