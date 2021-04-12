from collections import Counter

class NameCoref:

	def __init__(self):
		self.honorifics={"mr":1, "mr.":1, "mrs":1, "mrs.":1, "miss":1, "uncle":1, "aunt":1}

	def get_variants(self, name):
		variants={}
		parts=name.split(" ")
		for i in range(len(parts)):
			if parts[i].lower() not in self.honorifics:
				variants[parts[i]]=1

			for j in range(i+1, len(parts)):
				variants["%s %s" % (parts[i], parts[j])]=1

				for k in range(j+1, len(parts)):
					variants["%s %s %s" % (parts[i], parts[j], parts[k])]=1

					for l in range(k+1, len(parts)):
						variants["%s %s %s %s" % (parts[i], parts[j], parts[k], parts[l])]=1

						for m in range(l+1, len(parts)):
							variants["%s %s %s %s %s" % (parts[i], parts[j], parts[k], parts[l], parts[m])]=1

		return variants



	def name_cluster(self, entities, is_named):
		cands=[]
		for i, val in enumerate(is_named):
			if val == 1:
				cands.append((' '.join(entities[i]), i))

		uniq=Counter()

		for name, i in cands:
			uniq[name]+=1

		# remove names that are complete subsets of others
		subsets={}
		for name1 in uniq:
			name1set=set(name1.split(" "))
			for name2 in uniq:

				if name1 == name2:
					continue

				name2set=set(name2.split(" "))

				if name1set.issuperset(name2set):

					subsets[name2]=1

		name_subpart_index={}


		# map variants of names to their possible referents (e.g., "Tom" -> "Tom Sawyer", "Tom Waits")
		for name in uniq:
			if name in subsets:
				continue

			variants=self.get_variants(name)

			for v in variants:
				if v not in name_subpart_index:
					name_subpart_index[v]={}

				name_subpart_index[v][name]=1

		charids={}
		max_id=0

		lastSeen={}
		refs=[]
		for i, val in enumerate(is_named):
			if val == 1:
				name=' '.join(entities[i])
				if name in name_subpart_index:

					top=None
					max_score=0

					for entity in name_subpart_index[name]:
						score=uniq[entity]
						if entity in lastSeen:
							score+=lastSeen[entity]
						if score > max_score:
							max_score=score
							top=entity

					lastSeen[top]=i

				if top not in charids:
					charids[top]=max_id
					max_id+=1
				refs.append(charids[top])
			else:
				refs.append(-1)
		return refs

