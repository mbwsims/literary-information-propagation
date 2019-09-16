import os
import pickle
import re
from collections import OrderedDict
import pandas as pd


def get_char_co_occur(token_file):

	char_dict = {}
	tokens_df = pd.read_csv(token_file,sep=r'\t',engine='python')

	dialogue_block_dict = {}
	curr_dict = OrderedDict()
	start_sent = 0
	end_sent =  1
	no_quotes_count = 0
	skip_start_check = False
	block_count  = 0
	for sent_idx,_ in tokens_df.groupby('sentenceID'):
		quote_check = tokens_df[tokens_df.sentenceID==sent_idx].inQuotation.values
		if 'B-QUOTE' in quote_check or 'I-QUOTE' in quote_check:
			if not skip_start_check:
				start_sent = sent_idx
				end_sent = start_sent + 1
				skip_start_check = True
			else:
				no_quotes_count=0
				end_sent+=1
		else:
			if not skip_start_check: 
				continue
			else: 
				no_quotes_count+=1
				end_sent+=1

			if no_quotes_count == 3:
				start_sent = max(start_sent - 1, 0)
				end_sent = end_sent - 2 
				curr_dict['bookId'] = book_id
				curr_dict['startSentId'] = start_sent
				curr_dict['endSentId'] = end_sent
				curr_dict['startTokenId'] = tokens_df[tokens_df.sentenceID==start_sent].tokenId.values[0]
				sents = tokens_df[(tokens_df.sentenceID>=start_sent) & (tokens_df.sentenceID<=end_sent)]
				present_characters = sents[sents.inQuotation=='O'].characterId
				mention_characters = sents[sents.inQuotation!='O'].characterId
				pres_char_set = set([char for char in present_characters if char !=-1])
				curr_dict['charPresentList'] = list(pres_char_set)
				mention_char_set = set([char for char in mention_characters if char !=-1])
				curr_dict['charMentionList'] = list(mention_char_set)
			
				dialogue_block_dict[block_count] = curr_dict
				
				for char in pres_char_set:
					if char not in char_dict:
						char_dict[char] = {}
					for char2 in pres_char_set:
						if char2 != char:
							if char2 not in char_dict[char]:
								char_dict[char][char2] = 1
							else:
								char_dict[char][char2] += 1
					

				curr_dict = {}
				no_quotes_count=0
				skip_start_check = False  
				block_count+=1

	 
	curr_df = pd.DataFrame.from_dict(dialogue_block_dict,orient='index')
	
	return char_dict, curr_df


if __name__ == "__main__":

	char_book_dict = {}

	TOKENS_DIR = "/data0/dbamman/gutenberg/booknlp"
	QUOTES_DIR = "/data0/dbamman/gutenberg/booknlp/quotes_9.13.19"

	for tokens_folder in os.listdir(TOKENS_DIR):
		if tokens_folder[0].isdigit():
			for filename in os.listdir(os.path.join(TOKENS_DIR,tokens_folder)):
				if filename.endswith('.tokens'):
					token_file = os.path.join(TOKENS_DIR,tokens_folder,filename)

					book_id =re.sub(".tokens$", "", token_file.split("/")[-1])

					char_dict, char_df = get_char_co_occur(token_file)
					char_book_dict[book_id] = char_dict
					
					char_df.to_csv('/data0/project/lit_prop/co_occur_dfs/{}.csv'.format(book_id))

	with open('/data0/project/lit_prop/char_book_dict.pkl', 'wb') as handle:
		pickle.dump(char_book_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

	
