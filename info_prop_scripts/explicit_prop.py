import ast
import os
import json
import pickle
import pandas as pd


if __name__=="__main__":

	if not os.path.exists('../output/prop_results'):
		os.mkdir('../output/prop_results')

	propsFilePath = '../output/explicit_prop_tuples/explicit_tuples'

	with open(propsFilePath, "rb") as input_file:
		prop_tuples = pickle.load(input_file)

	prop_dict =  {}
	for book_id,explicit_prop in prop_tuples.items():
			
		quotes_df = pd.read_csv('../output/tagger/{}/{}.predicted.qa'.format(book_id,book_id), sep=r'\t',engine='python')
		co_occur_df  = pd.read_csv('../output/char_co_occurrence/{}.csv'.format(book_id))

		curr_book_dict = {}
		listeners_list =  []
		for a_node,prop_instances in explicit_prop.items():
			a_node = str(a_node)
			curr_book_dict[a_node] = []
			for instance in prop_instances:
				try:
					quote_start = instance['s']
					speaker = str(quotes_df[quotes_df.quote_start==quote_start].char_id.values[0])
					if speaker==a_node:
						continue
					listeners = co_occur_df[(co_occur_df.start_char<=quote_start) & (co_occur_df.end_char>quote_start)].participants.values[0]
					listeners = ast.literal_eval(listeners)
					listeners = [str(listener) for listener in listeners if str(listener) != a_node and str(listener) != speaker]
					if listeners:
						curr_book_dict[a_node].append({'b_node':speaker,'c_nodes':listeners})
				except:
					continue
			
		
	prop_dict[book_id] = curr_book_dict


	with open('../output/prop_results/explicit_prop_dict.pkl', 'wb') as handle:
		pickle.dump(prop_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)




