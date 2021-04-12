import sys, re

def read_gold(filename):
	# print(filename)
	coref={}
	ent_map={}
	max_id=0
	ent_ids={}

	data={}
	clusters={}

	meta={}

	chain_size={}

	with open(filename) as file:
		for line in file:
			cols=line.rstrip().split("\t")
			if cols[0] == "COREF":
				if cols[2] not in ent_map:
					ent_map[cols[2]]=max_id
					max_id+=1
				eid=ent_map[cols[2]]
				ent_ids[cols[1]]=eid
				if eid not in chain_size:
					chain_size[eid]=0
				chain_size[eid]+=1


	all_ents=[]

	with open(filename) as file:
		for line in file:
			cols=line.rstrip().split("\t")
			if cols[0] == "ENTITY":
				tid=cols[1]
				start_sid=int(cols[2])
				start_wid=int(cols[3])
				end_sid=int(cols[4])
				end_wid=int(cols[5])
					
				text=cols[6]
				cat=cols[7]
				ner=cols[8]

				is_named=False

				if ner == "PROP":
					is_named=True


				if tid in ent_ids:
					eid=ent_ids[tid]

				# this happens for cop/appos (treat as separate entity)
				else:
					continue
					eid=max_id
					max_id+=1

				meta[(start_sid, start_wid, end_wid)]=cat, ner, text, filename

				all_ents.append((start_sid, start_wid, end_wid))

				# print(start_sid, start_wid, end_wid, eid)
				data[(start_sid, start_wid, end_wid)]=eid
				if eid not in clusters:
					clusters[eid]=[]
				clusters[eid].append((start_sid, start_wid, end_wid))

	for eid in clusters:
		clusters[eid].sort(key=lambda tup: (tup[0], tup[1], tup[2]))

	all_ents.sort(key=lambda tup: (tup[0], tup[1], tup[2]))
	index={}
	for idx,ent in enumerate(all_ents):
		index[ent]=idx

	for key in meta:
		cat, ner, text, f=meta[key]
		ind=index[key]
		# print("ind", ind)
		eid=data[key]

		cluster=clusters[eid]
		iof=cluster.index(key)
		distance=0
		if iof > 0:
			prev=index[cluster[iof-1]]
			distance=ind-prev
			# print(distance)
		meta[key]=cat, ner, text, distance, f, chain_size[eid]

	# print(all_ents)

	return data, clusters, meta




def read_conll(filename):

	docid=None
	partID=None

	# collection
	all_sents=[]
	all_ents=[]
	all_antecedent_labels=[]
	all_max_words=[]
	all_max_ents=[]
	all_doc_names=[]

	all_named_ents=[]


	# for one doc
	all_doc_sents=[]
	all_doc_ents=[]
	all_doc_named_ents=[]

	all_data={}
	# for one sentence
	sent=[]
	ents=[]
	sid=0

	named_ents=[]
	cur_tid=0
	open_count=0

	with open(filename, encoding="utf-8") as file:
		for line in file:
			if line.startswith("#begin document"):

				all_doc_ents=[]
				all_doc_sents=[]

				all_doc_named_ents=[]

				open_ents={}
				open_named_ents={}

				sid=0
				docid=None

				matcher=re.match("#begin document \((.*)\); part (.*)$", line.rstrip())
				if matcher != None:
					docid=matcher.group(1)
					partID=matcher.group(2)

				# print(docid)

			elif line.startswith("#end document"):


				data={}
				clusters={}

				for sent_e in all_doc_ents:
					for sid, start_tid, end_tid, eid in sent_e:
						data[(sid, start_tid, end_tid)]=eid
						if eid not in clusters:
							clusters[eid]=[]
						clusters[eid].append((sid, start_tid, end_tid))

				all_data[docid]=data, clusters

				all_sents.append(all_doc_sents)
				
				all_named_ents.append(all_doc_named_ents)
				
				all_doc_names.append((docid,partID))

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

					cur_tid=0

					if len(parts) < 2:
						continue

				tid=cur_tid
				token=parts[3]
				coref=parts[-1].split("|")
				cur_tid+=1

				for c in coref:
					if c.startswith("(") and c.endswith(")"):
						c=re.sub("\(", "", c)
						c=int(re.sub("\)", "", c))

						ents.append((sid, tid, tid, c))

					elif c.startswith("("):
						c=int(re.sub("\(", "", c))

						if c not in open_ents:
							open_ents[c]=[]
						open_ents[c].append(tid)
						open_count+=1

					elif c.endswith(")"):
						c=int(re.sub("\)", "", c))

						assert c in open_ents

						start_tid=open_ents[c].pop()
						open_count-=1

						ents.append((sid, start_tid, tid, c))

			

				sent.append(token)


	return all_data


def b3(gold, goldClusters, system, systemClusters, meta, target_cat=None, target_ner=None, target_text=None, dist_min=None, dist_max=None, excludeSingletons=True):
	# P_total=0.
	# R_total=0.

	total_system=0.
	total_gold=0.
	total_correct=0.

	P=0.
	R=0.
	n=0.

	for mention in gold:

		cat, ner, text, distance, f, chain_size=meta[mention]
		# if ner == "PRON" and distance == 0:
		# 	print(mention, meta[mention])

		text=text.lower()
		if target_cat is not None and cat != target_cat:
			continue
		if target_ner is not None and ner != target_ner:
			continue
		if target_text is not None and text != target_text:
			continue
		if dist_min is not None and (distance < dist_min or distance >= dist_max):
			continue
		if chain_size < 2 and excludeSingletons:
			# print("SINGLE\t%s" % ner)
			continue

		goldCluster=set(goldClusters[gold[mention]])
		systemCluster=set(systemClusters[system[mention]])
		intersection=float(len(goldCluster.intersection(systemCluster)))

		total_correct+=intersection
		total_system+=len(systemCluster)
		total_gold+=len(goldCluster)

		P+=intersection/len(systemCluster)
		R+=intersection/len(goldCluster)
		n+=1


	return P, R, n

def analyze(filename, cat=None, ner=None, text=None, dist_min=None, dist_max=None, excludeSingletons=False):

	top="/mnt/data0/dbamman/coref/final_coref_combined"

	all_data=read_conll(filename)

	tot_P = tot_R = tot_n = 0
	for filename in all_data:
		goldPath="%s/%s.ann" % (top, filename)
		gold, goldClusters, meta=read_gold(goldPath)
		# print(filename)
		system, systemClusters=all_data[filename]
		doc_P, doc_R, doc_n=b3(gold, goldClusters, system, systemClusters, meta, target_cat=cat, target_ner=ner, target_text=text, dist_min=dist_min, dist_max=dist_max, excludeSingletons=excludeSingletons)

		tot_P+=doc_P
		tot_R+=doc_R
		tot_n+=doc_n


	P=(tot_P/tot_n)#/tot_n
	R=(tot_R/tot_n)#/tot_n
	F=(2*P*R)/(P+R)
	print("ES: %s\t%s\t%s\t%s\t%s\t%s\tP: %.1f\tR: %.1f\tF: %.1f\t%s" % (excludeSingletons, cat, ner, text, dist_min, dist_max, 100*P, 100*R, 100*F, tot_n))

filename=sys.argv[1]
# analyze(filename)
analyze(filename, excludeSingletons=True)
sys.exit(1)

print()

# for ner in ["NOM", "PROP", "PRON"]:
# 	analyze(filename, cat="PER", ner=ner)
# print()

# for ner in ["NOM", "PROP", "PRON"]:
# 	analyze(filename, dist_min=0, dist_max=1, ner=ner)
# 	analyze(filename, dist_min=1, dist_max=2, ner=ner)
# 	analyze(filename, dist_min=2, dist_max=3, ner=ner)
# 	analyze(filename, dist_min=3, dist_max=4, ner=ner)
# 	analyze(filename, dist_min=4, dist_max=5, ner=ner)
# 	analyze(filename, dist_min=5, dist_max=10, ner=ner)
# 	analyze(filename, dist_min=10, dist_max=15, ner=ner)
# 	analyze(filename, dist_min=15, dist_max=20, ner=ner)
# 	analyze(filename, dist_min=20, dist_max=25, ner=ner)
# 	analyze(filename, dist_min=25, dist_max=30, ner=ner)
# 	analyze(filename, dist_min=30, dist_max=35, ner=ner)
# 	analyze(filename, dist_min=35, dist_max=40, ner=ner)
# 	analyze(filename, dist_min=40, dist_max=45, ner=ner)
# 	analyze(filename, dist_min=45, dist_max=50, ner=ner)

# analyze(filename, dist_min=50, dist_max=100)
# analyze(filename, dist_min=100, dist_max=250)
# analyze(filename, dist_min=250, dist_max=500)

print()


for cat in ["PER", "FAC", "LOC", "GPE", "ORG", "VEH"]:
	analyze(filename, cat=cat)
print()
for ner in ["NOM", "PROP", "PRON"]:
	analyze(filename, ner=ner)
print()
for text in ["it", "he", "she"]:
	analyze(filename, text=text)
