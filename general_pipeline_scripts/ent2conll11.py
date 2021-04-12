import sys
import os

def read_ents(filename):
	ents={}
	with open(filename, encoding="utf-8") as file:

		for line in file:
			cols=line.rstrip().split("\t")
			start=int(cols[0])
			end=int(cols[1])
			lab=cols[2]
			if not lab.endswith("PER"):
				continue

			text=cols[3]

			if text.lower() in honorifics:
				continue

			name=False
			if lab.startswith("PROP"):
				name=True

			# print(text, name)
			ents[(start, end, text, name)]=1

	return ents

pronouns={"he":1, "she":1, "him":1, "her":1, "his":1, "mine":1, "herself":1, "himself":1, "you":1, "i":1, "me":1, "my":1, "your":1}
honorifics={"mr.":1, "mrs.":1, "mr":1, "mrs":1, "miss":1}

def read_txt(filename, ents):
	cur=0
	starts={}
	ends={}
	sents=[]

	mapper={}
	sent_ents={}

	with open(filename, encoding="utf-8") as file:
		file.readline()
		lastSid=None
		counter=0
		words=[]

		for line in file:
			cols=line.rstrip().split("\t")
			sid=int(cols[1])

			if sid != lastSid:
				counter=0
				sent_ents[sid]=[]
				if lastSid is not None:
					sents.append(words)
				words=[]

			tid=int(cols[2])
			word=cols[8]

			if word.lower() in pronouns:
				ents[tid, tid, word, False]=1

			words.append(word)
			mapper[tid]=(sid,counter)

			lastSid=sid
			counter+=1

		sents.append(words)

	i=0
	for (start, end, text, name) in ents:
		start_sidx, start_w_idx=mapper[start]
		end_sidx, end_w_idx=mapper[end]
		sent_ents[start_sidx].append((start_w_idx, end_w_idx, i, text, name))
		i+=1


	big_ents={}
	ent_id=0

	all_sent_ents=[]
	all_antecedent_labels=[]

	max_words=0
	max_ents=0

	for idx, sent in enumerate(sents):
		if len(sent) > max_words:
			max_words=len(sent)
		this_sent_ents=[]

		if idx in sent_ents:
			all_ents=sorted(sent_ents[idx], key=lambda x: (x[0], x[1]))
			if len(all_ents) > max_ents:
				max_ents=len(all_ents)

			for (w_idx_start, w_idx_end, eid, text, is_named) in all_ents:

				this_sent_ents.append((w_idx_start, w_idx_end, eid, is_named))

				coref={}
				if eid in big_ents:
					coref=big_ents[eid]
				else:
					coref={ent_id:1}

				vals=sorted(coref.keys())
				# print(text, vals)


				if eid not in big_ents:
					big_ents[eid]={}
				big_ents[eid][ent_id]=1
				ent_id+=1

				all_antecedent_labels.append(vals)

		all_sent_ents.append(this_sent_ents)

	return sents, all_sent_ents, all_antecedent_labels, max_words, max_ents

def print_conll(doc_id, sents, all_ents):
	print("#begin document (%s); part 0" % (doc_id))
	for s_idx, sent in enumerate(sents):
		ents=all_ents[s_idx]
		for w_idx, word in enumerate(sent):
			label=[]
			ner_label=[]
			for start, end, eid, is_named in ents:
				if start == w_idx and end == w_idx:
					label.append("(%s)" % eid)
					if is_named:
						ner_label.append("(%s)" % eid)
				elif start == w_idx:
					label.append("(%s" % eid)
					if is_named:
						ner_label.append("(%s" % eid)
				elif end == w_idx:
					label.append("%s)" % eid)
					if is_named:
						ner_label.append("%s)" % eid)
			print("%s\t0\t%s\t%s\t_\t_\t_\t_\t_\t_\t%s\t_\t%s" % (doc_id, w_idx, word, '|'.join(ner_label), '|'.join(label)))
		print()
	print("#end document")

entFile=sys.argv[1]
tokensFile=sys.argv[2]
base=sys.argv[3]


ents=read_ents(entFile)
doc, ents, truth, max_words, max_ents=read_txt(tokensFile, ents)
print_conll(base, doc, ents)

