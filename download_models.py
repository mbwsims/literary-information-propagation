import gdown


coref_url = 'https://drive.google.com/uc?export=download&id=14w9nLDFVMeU9N43OPWbR3HjrgtJUyM5d'
coref_model_loc = 'coref/coref.model'

entities_url = 'https://drive.google.com/uc?export=download&id=1CHMtmiQI37a1LTSYmzdFdQo9fio4iphi'
entities_model_loc = 'mention_tagger/prop.mentions.model'


gdown.download(coref_url, coref_model_loc, quiet=False)
gdown.download(entities_url, entities_model_loc, quiet=False)