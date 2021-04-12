import sys, re

mapper={}

def read_conll(filename):

	big_tid=0
	docid=None
	partID=None

	# collection
	all_sents=[]
	all_ents=[]
	all_max_words=[]
	all_max_ents=[]
	all_doc_names=[]

	all_named_ents=[]


	# for one doc
	all_doc_sents=[]
	all_doc_ents=[]
	all_doc_named_ents=[]

	# for one sentence
	sent=[]
	ents=[]
	sid=0

	named_ents=[]

	with open(filename, encoding="utf-8") as file:
		for line in file:
			if line.startswith("#begin document"):

				all_doc_ents=[]
				all_doc_sents=[]

				open_ents={}
				open_named_ents={}

				sid=0
				docid=None

				matcher=re.match("#begin document \((.*)\); part (.*)$", line.rstrip())
				if matcher != None:
					docid=matcher.group(1)
					partID=matcher.group(2)

			elif line.startswith("#end document"):

				all_sents.append(all_doc_sents)
				
				all_ents.append(all_doc_ents)

				all_named_ents.append(all_doc_named_ents)

			else:

				parts=re.split("\s+", line.rstrip())

				if len(parts) < 2:
		
					all_doc_sents.append(sent)
					ents=sorted(ents, key=lambda x: (x[0], x[1]))

					all_doc_ents.append(ents)

					all_doc_named_ents.append(named_ents)

					ents=[]
					named_ents=[]
					sent=[]
					sid+=1

					continue

				# +1 to account for initial [SEP]
				tid=int(parts[2])
				token=parts[3]
				coref=parts[-1].split("|")


				for c in coref:
					if c.startswith("(") and c.endswith(")"):
						c=re.sub("\(", "", c)
						c=int(re.sub("\)", "", c))

						ents.append((tid, tid, c))

					elif c.startswith("("):
						c=int(re.sub("\(", "", c))

						if c not in open_ents:
							open_ents[c]=[]
						open_ents[c].append(tid)

					elif c.endswith(")"):
						c=int(re.sub("\)", "", c))

						assert c in open_ents

						start_tid=open_ents[c].pop()

						ents.append((start_tid, tid, c))

				sent.append(token)
				mapper[(len(all_doc_sents), tid)]=big_tid
				big_tid+=1


	return all_sents, all_ents

filename=sys.argv[1]
sents, ents=read_conll(filename)

for d_idx, doc_sents in enumerate(sents):
	for s_idx, sent in enumerate(doc_sents):
		s_ents=ents[d_idx][s_idx]
		for val in s_ents:
			s, e, c=val
			phrase=' '.join(sent[s:e+1])
			print("%s\t%s\t%s\t%s" % (c, phrase, mapper[s_idx, s], mapper[s_idx,e]))