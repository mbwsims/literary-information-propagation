import os, pickle, json, time, random, ast, sys
import numpy as np
import pandas as pd

def get_b_node_connectors(prop_df,quotesFilePath):
	
	connector_class_dict = {}
	propagator_count = 0 
	non_propagator_count = 0
	deficit = 0 
	grouped = prop_df.groupby('bookId')
	
	for book_id, group in grouped:
	    
	    quotes_df = pd.read_csv(quotesFilePath.format(book_id,book_id), sep=r'\t',engine='python')
	    speaking_nodes = quotes_df.char_id.unique()
	    
	    propagator_set = set()
	    found_propagators_set = set()
	    non_propagator_set = set()
	    
	    for propagator in prop_df[prop_df.bookId==book_id].connectors.values:
	        propagator_set = propagator_set | propagator
	        
	    if len(propagator_set) >= 1:
	        for prop in prop_df[prop_df.bookId==book_id].prop_list.values[0]:
	            if prop['b'] not in found_propagators_set:
	                found_propagators_set.add(prop['b'])
	                Bs = prop['possible_Bs'].copy()
	                random.shuffle(Bs)
	                found_b_prime = False
	                b_prime_count = 0
	                for b in Bs:
	                    if b not in non_propagator_set and b not in propagator_set:
	                        if b in speaking_nodes:
	                            non_propagator_set.add(b)
	                            found_b_prime = True
	                            b_prime_count += 1
	                            if deficit <= -1 or b_prime_count > 1:
	                                break
                    
        	connector_class_dict[book_id] = {'connectors':propagator_set,'non_connectors':non_propagator_set}
        
	    propagator_count += len(propagator_set)
	    non_propagator_count +=len(non_propagator_set)
	    deficit = propagator_count - non_propagator_count

	return connector_class_dict

if __name__ == "__main__":

	outputDIR = '../output/speaker_b_nodes'
	if not os.path.exists(outputDIR):
		os.mkdir(outputDIR)

	with open('../output/prop_results/implicit_prop_dict.pkl', "rb") as input_file:
		prop_dict = pickle.load(input_file)

	# remove tuples that contain same entity
	for key in list(prop_dict):
		tup = prop_dict[key]['prop_tuple']
		split = tup.split('_')
		if split[0] == split[-1]:
			del prop_dict[key]

	prop_df = pd.DataFrame.from_dict(prop_dict,orient='index')
	try:
		prop_df = prop_df[prop_df['prop_success']==True]
	except:
		print("No instances of succesful propagation found.")
		sys.exit()


	quotesFilePath = '../output/tagger/{}/{}.predicted.qa'

	connector_class_dict = get_b_node_connectors(prop_df,quotesFilePath)

	with open('../output/speaker_b_nodes/connector_dict_speakers_only.pkl', 'wb') as handle:
		pickle.dump(connector_class_dict, handle, protocol=pickle.HIGHEST_PROTOCOL) 

			 