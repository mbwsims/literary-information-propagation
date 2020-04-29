import sys, json
import os
from collections import Counter

t_sent_idx=1
t_deprel_idx=12
t_head_idx=6
t_token_idx=2
t_word_idx=8 
t_lemma_idx=9 
t_char_idx=-1

validRelations={"nsubj":1, "nsubjpass":1, "dobj":1}

def proc_quote(quote):
	
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
				curr_char_id = ents_dict[curr_start]['char_id']
				cols.append(curr_char_id)
			elif int(cols[2]) < int(curr_end):
				cols.append(curr_char_id)
			else:
				cols.append('-1')
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


if __name__ == "__main__":

	folder = '/data0/dbamman/acl2020_infoprop/data_savio/'
	token_file = '/data0/dbamman/acl2020_infoprop/data_savio/{}/{}.tokens'
	ents_file = '/data0/dbamman/acl2020_infoprop/data_savio/{}/{}.predicted.conll.ents'
	for bookid in os.listdir(folder):
		bookpath=token_file.format(bookid,bookid)
		entspath=ents_file.format(bookid,bookid)
		counts=Counter()
		witnesses={}
		
		ents_dict = get_ents(entspath)
		quotes=read_booknlp(bookpath,ents_dict)

		for quote in quotes:
			proc_quote(quote)

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
					result = "%s\t%s\t%s\t%s\n" % (bookid, '_'.join(str(k2) for k2 in k), v, json.dumps(wits))
					with open('/data0/project/lit_prop/tuples/new_coref_props15k_updated_new', 'a+') as f:
						f.write(result)

