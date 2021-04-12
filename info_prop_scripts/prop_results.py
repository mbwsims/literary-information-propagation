import sys, os, json, ast
from collections import Counter, defaultdict
import pickle
import pandas as pd

t_sent_idx=1
t_deprel_idx=12
t_head_idx=6
t_token_idx=2
t_word_idx=8 
t_lemma_idx=9 
t_char_idx=-1

validRelations={"nsubj":1, "nsubjpass":1, "dobj":1}


def proc_quote_implicit(quote):
	
	sent_dict = {}
	for row in quote:
		sent_idx = row[t_sent_idx]
		if sent_idx in sent_dict:
			sent_dict[sent_idx].append(row[t_word_idx])
		else:
			sent_dict[sent_idx] = [row[t_word_idx]]

	words=[token[t_word_idx] for token in quote]
	quoteStart=int(quote[0][t_token_idx])
	quoteEnd=int(quote[-1][t_token_idx])
	heads={}
	children={}
	tokensById={}
	for i, token in enumerate(quote):
		idx=token[t_token_idx]
		word=token[t_lemma_idx]
		head=token[t_head_idx]
		heads[idx]=(i, word)
		tokensById[idx]=token

		if head not in children:
			children[head]=[]
		children[head].append(idx)

	for token in quote:
		charid=token[t_char_idx]
		lemma=token[t_lemma_idx]
		if charid != '-1' and lemma.lower() not in ['i','you','we']:
			deprel=token[t_deprel_idx]
			head=token[t_head_idx]
			headWord=None
			if deprel not in validRelations:
				continue
			if head != '-1' and head in heads:
				_, headWord=heads[head]

				if head in children:
					for child in children[head]:
						if tokensById[child][t_deprel_idx] == "neg":
							headWord="NEG+" + headWord
						if tokensById[child][t_deprel_idx] == "cop":
							headWord="COP+" + headWord
			#print(charid, deprel, headWord)
			signature=(charid, deprel, headWord)

			if deprel == "nsubjpass":
				signature=(None, headWord, charid)

			dobj_lemma = None
			if deprel == "nsubj":
				signature=(charid, headWord, None)
				if head in children:
					for child in children[head]:
						if tokensById[child][t_deprel_idx] == "dobj":
							dobj_lemma = dobj = tokensById[child][t_lemma_idx]
							if tokensById[child][t_char_idx] != '-1':
								dobj=tokensById[child][t_char_idx]
							signature=(charid, headWord, dobj)
							# print(signature)
				if dobj_lemma:
					if dobj_lemma.lower() in ['i','you','we']:
						continue
				
			nsubj_lemma = None
			if deprel == "dobj":
				signature=(None, headWord, charid)
				if head in children:
					for child in children[head]:
						if tokensById[child][t_deprel_idx] == "nsubj":
							nsubj_lemma = nsubj =tokensById[child][t_lemma_idx]
							if tokensById[child][t_char_idx] != '-1':
								nsubj=tokensById[child][t_char_idx]

							signature=(nsubj, headWord, charid)
				if nsubj_lemma:
					if nsubj_lemma.lower() in ['i','you','we']:
						continue
				

			if headWord is not None:
				sent_id = token[t_sent_idx]
				if '?' not in sent_dict[sent_id][-4:]:
					sentence = ' '.join(sent_dict[sent_id])
					counts[signature]+=1
					if signature not in witnesses:
						witnesses[signature]=[]

					witnesses[signature].append({"sent_id":sent_id, "sentence":sentence, "s":quoteStart, "e":quoteEnd})

def proc_quote_explicit(quote):

	quoteStart=int(quote[0][t_token_idx])
	quoteEnd=int(quote[-1][t_token_idx])

	sents = pd.DataFrame(quote).groupby(1)

	selected_ents = set()
	is_char_ent = False
	for sent_id,sent in sents:
		try:
			if sent.iloc[-1][t_word_idx] != '?' and sent.iloc[-2][t_word_idx] != '?':
				words=[str(token[t_word_idx]) for token in sent.values]
				sentence=' '.join(words)
				for i, token in enumerate(sent.values):
					prop=False
					charid=int(token[t_char_idx])
					word=token[t_lemma_idx]
					if charid != -1 and charid not in selected_ents:
						is_char_ent = True
						curr_ent = charid
						curr_ent_word = word
					if is_char_ent and charid == -1:
						prev_word = None
						next_word = None
						next_word_plus_one = None
						try:
							prev_word = sent[i-1][t_lemma_idx]
						except:
							pass
						try:
							next_word = sent[i+1][t_lemma_idx]
						except:
							pass
						try:
							next_word_plus_one = sent[i+2][t_lemma_idx]
						except:
							pass
						if prev_word in ['I','you','dare'] or curr_ent_word in ['I','you'] or next_word=='something' or next_word_plus_one == '.':
							continue
						if word == 'say' or word == 'declare':
							prop=True
						elif word == 'tell' and next_word  == 'I':
							prop=True
						elif word == 'claim' and next_word in ['to','that']:
							prop=True
						elif (word == 'suggest' or word == 'mention') and next_word == 'that':
							prop=True
						if prop:
							witnesses[curr_ent].append({"sentId":sent_id,"sent":sentence, "s":quoteStart, "e":quoteEnd})
							selected_ents.add(curr_ent)

						is_char_ent = False
		except:
			continue


def read_booknlp(filename,ents_dict):
	quotes=[]
	current=[]
	curr_end = 0
	with open(filename) as file:
		file.readline()
		for line in file:
			cols=line.rstrip().split("\t")
			if cols[2] in ents_dict:
				curr_start = cols[2]
				curr_end = ents_dict[curr_start]['end_idx']
				curr_char_id = int(ents_dict[curr_start]['char_id'])
				cols.append(curr_char_id)
			elif int(cols[2]) < int(curr_end):
				cols.append(curr_char_id)
			else:
				cols.append(-1)
			quote=cols[13]
			sent_id = cols[1]
			# print(quote)
			if quote == "B-QUOTE":
				if len(current) > 0:
					quotes.append(current)
					current=[]

			if quote != "O":
				current.append(cols)


	return quotes

def get_ents(filename):

	ents_dict = {}
	with open(filename) as file:
		file.readline()
		for line in file:
			cols=line.rstrip().split("\t")
			ents_dict[cols[2]] = {'end_idx':cols[3],'char_id':cols[0]} 

	return ents_dict


if __name__=="__main__":

	
	if not os.path.exists('../output/implicit_prop_tuples'):
		os.mkdir('../output/implicit_prop_tuples')
	if not os.path.exists('../output/explicit_prop_tuples'):
		os.mkdir('../output/explicit_prop_tuples')

	DIR = "../output/tagger/"
	explicit_prop_dict = {}

	for folder in os.listdir(DIR):
		if folder != '.DS_Store':

			tokens_file = os.path.join(DIR,folder,folder + '.tokens')
			ents_file  = os.path.join(DIR,folder,folder + '.predicted.conll.ents')
			book_id = folder

			# get implicit prop tuples
			counts=Counter()
			witnesses={}

			ents_dict = get_ents(ents_file)
			quotes=read_booknlp(tokens_file,ents_dict)

			for quote in quotes:
				proc_quote_implicit(quote)

			for k,v in counts.most_common():
				if v >= 2:
					wits=[]
					seen={}
					# only include a quotation once, even if it has multiple identical tuples
					for wit in witnesses[k]:
						sig=wit["s"], wit["e"]
						if sig not in seen:
							wits.append(wit)
						seen[sig]=1
					if len(wits) >= 2:
						result = "%s\t%s\t%s\t%s\n" % (book_id, '_'.join(str(k2) for k2 in k), v, json.dumps(wits))
						with open('../output/implicit_prop_tuples/implicit_tuples', 'a+') as f:
							f.write(result)

		# get explicit prop results
			witnesses = defaultdict(list)
			for quote in quotes:
				proc_quote_explicit(quote)
			if witnesses:
				explicit_prop_dict[book_id] = witnesses

		with open('../output/explicit_prop_tuples/explicit_tuples', 'wb') as handle:
			pickle.dump(explicit_prop_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)



	

	
