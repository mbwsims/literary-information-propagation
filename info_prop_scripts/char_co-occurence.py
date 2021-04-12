import os
import pickle
import re
from collections import OrderedDict
import pandas as pd


def read_ents(path):
	entities={}
	with open(path, encoding="utf-8") as file:
		for line in file:
			cols=line.rstrip().split("\t")
			cid=int(cols[0])
			name=cols[1]
			start=int(cols[2])
			end=int(cols[3])
			# print(start, end)
			if start not in entities:
				entities[start]={}
			entities[start][end]=cid, name

	return entities

def read_tokens(path):

	children={}

	tokens=[]

	with open(path, encoding="utf-8") as file:
		file.readline()
		for line in file:
			cols=line.rstrip().split("\t")
			tokens.append(cols)
			tid=int(cols[2])
			head=int(cols[6])
			if head not in children:
				children[head]=[]
			children[head].append(tid)
	return tokens, children

def find_entities_in_range(start, end, entities, tokens):
	cands=[]
	for i in range(start, end):
		if i in entities:
			for e_end in entities[i]:
				if e_end < end:
					if tokens[i][13] == "O":
						cands.append(entities[i][e_end][0])

	

	return list(set(cands))


def get_char_co_occur(book_id,tokens_file,ents_file):

	char_dict = {}
	tokens_df = pd.read_csv(tokens_file,sep=r'\t',engine='python')
	
	tokens, children=read_tokens(tokens_file)
	entities=read_ents(ents_file)

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

			if no_quotes_count == 3 or end_sent==tokens_df.tail(1).sentenceID.values[0]:
				start_sent = max(start_sent - 1, 0)
				if no_quotes_count == 3:
					end_sent = end_sent - 2 
				else:
					end_sent = end_sent - 1
				start_char = tokens_df[tokens_df.sentenceID==start_sent].tokenId.values[0]
				try:
					end_char = tokens_df[tokens_df.sentenceID==end_sent].tokenId.values[-1]
				except:
					continue
				curr_dict['book_id'] = book_id
				curr_dict['start_char'] = start_char
				curr_dict['end_char'] = end_char
				curr_dict['start_sent'] = start_sent
				curr_dict['end_sent'] = end_sent

				listeners=find_entities_in_range(start_char, end_char, entities, tokens)
				curr_dict['participants'] = listeners
				
				dialogue_block_dict[block_count] = curr_dict

				for char in listeners:
					if char not in char_dict:
						char_dict[char] = {}
					for char2 in listeners:
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

	if not os.path.exists('../output/char_co_occurrence'):
		os.mkdir('../output/char_co_occurrence')
	if not os.path.exists('../output/char_book_dict'):
		os.mkdir('../output/char_book_dict')

	char_book_dict = {}

	DIR = "../output/tagger/"

	for folder in os.listdir(DIR):
		if folder != '.DS_Store':
			tokens_file = os.path.join(DIR,folder,folder + '.tokens')
			ents_file  = os.path.join(DIR,folder,folder + '.predicted.conll.ents')
			book_id = folder

			char_dict, char_df = get_char_co_occur(book_id, tokens_file, ents_file)
			char_book_dict[book_id] = char_dict

			char_df.to_csv('../output/char_co_occurrence/{}.csv'.format(book_id))

	with open('../output/char_book_dict/char_book_dict.pkl', 'wb') as handle:
		pickle.dump(char_book_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


