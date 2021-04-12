
def read_coref(filename):
	ents={}
	with open(filename) as file:
		for line in file:
			cols=line.rstrip().split("\t")
			tid=cols[0]

			if tid == "REL":
				continue

			eid=int(cols[1])
			if eid != -1:
				ents[tid]=eid

	return ents

def read_anns(filename, coref_ents):
	ents={}
	with open(filename) as file:

		for line in file:
			cols=line.rstrip().split("\t")
			tid=cols[0]
			data=cols[1].split(" ")
			cat=data[0]
			if cat == "ADDED":
				continue

			if cat != "PER" and cat != "PRON":
				continue

			start=int(data[1])
			end=int(data[2])
			text=cols[2]

			if tid in coref_ents:
				ents[tid]=(coref_ents[tid], start, end, text)
	return ents

def read_txt(filename, ents):
	cur=0
	starts={}
	ends={}
	sents=[]

	with open(filename) as file:
		for s_idx, line in enumerate(file):
			words=line.rstrip().split(" ")
			sents.append(words)
			for w_idx, word in enumerate(words):
				# print("start", cur, word)
				starts[cur]=(s_idx, w_idx, word)
				ends[cur+len(word)]=(s_idx, w_idx, word)
				cur+=len(word)+1

	all_ents=[]
	sent_ents={}

	for tid in ents:
		eid, start, end, text=ents[tid]
		try:
			(s_idx_start, w_idx_start, _)=starts[start]
			(s_idx_end, w_idx_end, _)=ends[end]

			if s_idx_start not in sent_ents:
				sent_ents[s_idx_start]=[]

			sent_ents[s_idx_start].append((w_idx_start, w_idx_end, eid, text))
		except:
			print("Problem!", eid, start, end, text, filename)
			pass

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

			for (w_idx_start, w_idx_end, eid, text) in all_ents:

				this_sent_ents.append((w_idx_start, w_idx_end))

				coref={}
				if eid in big_ents:
					coref=big_ents[eid]
				else:
					coref={ent_id:1}

				vals=sorted(coref.keys())

				if eid not in big_ents:
					big_ents[eid]={}
				big_ents[eid][ent_id]=1
				ent_id+=1

				all_antecedent_labels.append(vals)

		all_sent_ents.append(this_sent_ents)

	print("Max words: %s, max ents: %s" % (max_words, max_ents))
	return sents, all_sent_ents, all_antecedent_labels, max_words, max_ents