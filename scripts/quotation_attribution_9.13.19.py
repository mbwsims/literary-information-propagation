import sys, re, argparse
from collections import Counter

PINK = '\033[95m'
ENDC = '\033[0m'
BIYellow="\033[1;93m"     # Yellow

def read_tokens(path):

	children={}

	tokens=[]

	with open(path) as file:
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



validpos={"NN":1, "NNP":1, "NNS":1, "NNPS":1, "DT":1, "PRP$":1, "PRP":1, "JJ":1, "JJR":1, "JJS":1, "POS":1}

# MENTION VERB QUOTE
def trigram_matching_before(tokens, tokenStart, maxLength):
	firstWord=tokens[tokenStart-1]
	word=firstWord[7]
	if word == ",":
		idd=None

		# find the rightmost token in a mention by starting from the quote and working backwords
		for n in range(2,maxLength):

			secondWord=tokens[tokenStart-n]
			word=secondWord[7]
			pos=secondWord[10]
			if pos.startswith("V") == False and pos.startswith("RB") == False and pos != "MD":
				idd=n
				break

		# keep backing up until you find the start of the mention
		if idd != None:
			mention=[]
			for j in range(maxLength):
				jid=tokenStart-idd-j
				word=tokens[jid][7]
				pos=tokens[jid][10]
				inQuote=tokens[jid][13]
				if inQuote != "O":
					break
				if pos in validpos:
					mention.append(jid)
				else:
					break
			if (len(mention)) > 0:
				return list(reversed(mention))

	return None

target_verbs={"say":1, "cry":1, "reply":1, "add":1, "think":1, "observe":1, "call":1, "answer":1, "continue":1}

def get_string(rep, tokens):
	name=[]
	for i in rep:
		name.append(tokens[i][8])
	return ' '.join(name)

def get_descendents(tid, children, tokens):
	left=tid
	right=tid
	if tid in children:
		for child in children[tid]:
			rel=tokens[child][12]
			if rel == "det" or rel == "amod" or rel == "nn":
				if child < left:
					left=child
				if child > right:
					child=right
	rep=[]
	for i in range(left, right+1):
		rep.append(i)
	return rep

def get_dep_parse(tokens, tokenStart, tokenEnd, children):
	num_sents=2
	cur=tokenStart-1
	startSID=int(tokens[cur][1])
	sid=startSID
	startPID=int(tokens[tokenStart][0])
	pid=int(tokens[cur][0])

	while(startSID-sid <= num_sents and cur >= 0 and startPID == pid):
		sid=int(tokens[cur][1])
		ss=tokens[cur][15]
		lemma=tokens[cur][9]
		tid=int(tokens[cur][2])
		inQuote=tokens[cur][13]
		pid=int(tokens[cur][0])

		cur-=1

		# don't cross quotes
		if inQuote != "O":
			break

		if lemma in target_verbs or ss == "B-verb.communication":
			if tid in children:
				for child in children[tid]:
					if tokens[child][13] == "O" and tokens[child][12]== "nsubj":
						rep=get_descendents(child, children, tokens)
						return rep
	
	cur=tokenEnd+1
	if cur >= len(tokens):
		return

	startSID=int(tokens[cur][1])
	sid=startSID
	pid=int(tokens[cur][0])

	while(sid-startSID <= num_sents and cur < len(tokens) and startPID == pid):
		sid=int(tokens[cur][1])
		ss=tokens[cur][15]
		lemma=tokens[cur][9]
		tid=int(tokens[cur][2])
		inQuote=tokens[cur][13]
		pid=int(tokens[cur][0])
	
		cur+=1
		if inQuote != "O":
			break

		if lemma in target_verbs or ss == "B-verb.communication":
			if tid in children:
				for child in children[tid]:
					if tokens[child][13] == "O" and tokens[child][12]== "nsubj":
						rep=get_descendents(child, children, tokens)
						return rep

	return None

def single_mention(tokens, tokenStart, tokenEnd, children):
	parid=tokens[tokenStart][0]
	mentions={}
	cur=tokenStart-1
	if cur > 0:
		curParid=tokens[cur][0]

		while parid == curParid:
			charid=tokens[cur][14]
			if tokens[cur][13] == "O":

				if charid != "-1":

					if charid not in mentions:
						mentions[charid]=cur
				
			cur-=1
			curParid=tokens[cur][0]

	cur=tokenEnd+1
	if cur < len(tokens):
		curParid=tokens[cur][0]

		while parid == curParid and cur < len(tokens):
			charid=tokens[cur][14]
			if tokens[cur][13] == "O":

				if charid != "-1":

					if charid not in mentions:
						mentions[charid]=cur
				
			cur+=1
			if cur < len(tokens):
				curParid=tokens[cur][0]


	if len(mentions) == 1:
		idd=[int(x) for x in mentions.values()][0]
		rep=get_descendents(idd, children, tokens)
		return rep



def trigram_matching_after(tokens, tokenStart, maxLength, lastChar):
	if lastChar == ".":
		return None
	if lastChar != ",":
		firstWord=tokens[tokenStart]
		word=firstWord[7]
		pos=firstWord[10]

		if word.lower() != word:
			return None
	mention=None

	# QUOTE MENTION VERB
	for i in range(tokenStart, tokenStart+maxLength):

		if i >= len(tokens):
			break

		word=tokens[i][7]
		pos=tokens[i][10]
		lemma=tokens[i][9]
		inQuote=tokens[i][13]
		ss=tokens[i][15]

		if inQuote != "O":
			break
		
		# find verb after quotation
		# if pos.startswith("V") or pos == "MD":
		if lemma in target_verbs or ss == "B-verb.communication":
			mention=[]

			# find mention between quote and found verb
			for j in range(tokenStart, i):
				pos=tokens[j][10]
				if pos in validpos:
					mention.append(j)
				else:
					break
			
			if len(mention) > 0:
				return mention

	# QUOTE VERB MENTION

	for vidx in range(3):
	
		pos=tokens[tokenStart+vidx][10]
		lemma=tokens[tokenStart+vidx][9]
		ss=tokens[tokenStart+vidx][15]
		# find verb, skipping adverbs and modals
		if pos == "RB" or pos == "RBR" or pos == "MD":
			continue

		# if pos.startswith("V"):
		if lemma in target_verbs or ss == "B-verb.communication":
			mention=[]

			for i in range(tokenStart+vidx+1, tokenStart+1+vidx+maxLength):

				word=tokens[i][7]
				pos=tokens[i][10]
				inQuote=tokens[i][13]
				if inQuote != "O" or pos not in validpos:
					break
				
				mention.append(i)

			if len(mention) > 0:		
				return mention


	return None

def getQuotes(tokens):
	quotes=[]
	start=None
	for idx,cols in enumerate(tokens):
		inQuote=cols[13]

		if (inQuote == "B-QUOTE" or inQuote == "O") and start != None:
			quotes.append((start, idx-1))
			start=None

		if inQuote == "B-QUOTE":
			start=idx

	if start != None:
		quotes.append((start, len(tokens)))

	return quotes

def attribute(tokens, start, end, lastChar):
	mention=None
	fin=end+1
	if fin < len(tokens):
		mention=trigram_matching_after(tokens, fin, 5, lastChar)

	if mention== None:
		mention=trigram_matching_before(tokens, start, 5)
	return mention

def get_turns(quotes):

	""" Get sets of quotations separated by some minimum window of non-quotations (here, 100) """

	window=100 # words
	lastEnd=None
	turns=[]
	current=[]
	for (start,end) in quotes:
		if lastEnd != None:
			if start-lastEnd > window:
				turns.append(current)
				current=[]
		current.append((start,end))
		lastEnd=end
	if len(current) > 0:
		turns.append(current)
	return turns

def get_vocatives(tokens, start, end):
	family={"father":1, "mother":1, "mamma":1, "papa":1, "sister":1}
	vocs=[]
	cols=tokens[start]
	voc=[]
	idd=None
	for j in range(start, end):
		jcols=tokens[j]
		idd=j
		if jcols[10] != "NNP" and jcols[7] not in family:
			break
		voc.append(j)
	if idd != None:
		jcols=tokens[idd]
		if idd == end or jcols[7] == "," or jcols[7] == "!" or jcols[7] == "?":
			# vtext=' '.join(voc)
			if len(voc) > 0:
				vocs.append(voc)

	for i in range(start, end):
		cols=tokens[i]
		if cols[7] == ",":
			voc=[]
			idd=None
			for j in range(i+1, end):
				jcols=tokens[j]
				idd=j
				if jcols[10] != "NNP" and jcols[7] not in family:
					break
				voc.append(j)
			if idd != None:
				jcols=tokens[idd]
			if idd == end or jcols[7] == "," or jcols[7] == "!" or jcols[7] == "?":
					# vtext=' '.join(voc)
					if len(voc) > 0:
						vocs.append(voc)

	return vocs

def get_top_entities(tokens, quoteStart, quoteEnd):
	ents=Counter()
	start=quoteStart-2000
	if start < 0:
		start=0
	end=quoteEnd+500
	if end >= len(tokens):
		end=len(tokens)

	for i in range(start, end):
		if tokens[i][13] == "O":
			if tokens[i][14] != "-1":
				ents[tokens[i][14]]+=1

	return ents

def get_previous_in_diff_par(mentions, quotes, idx, tokens):
	cand=idx-1
	par=int(tokens[quotes[idx]][0])
	cand_par=int(tokens[quotes[cand]][0])
	while par-cand_par <= 2 and cand >= 0:
		if par-cand_par == 2:
			return mentions[cand]

		cand-=1
		cand_par=int(tokens[quotes[cand]][0])


	return None

def attribute_quotes(filename, tokens, children):

	attributed=[]

	# get raw quotes
	quotes=getQuotes(tokens)

	# aggregate quotes into quotation segments
	turns=get_turns(quotes)

	lastMention=None
	lastParid=None
	lastlastChar=None
	noneCount=0.
	total=0
	vocs=[]

	new_ent_id=0
	seen_ents={}

	all_char_mentions=[]
	quote_starts=[]

	for quotes in turns:
		all_mentions=[]
		mentions=Counter()
		for (start, end) in quotes:
			quote_starts.append(start)

			quote=[]
			parid=None
			for j in range(start,end+1):
				if j < len(tokens):
					quote.append(tokens[j][8])
					parid=tokens[j][0]

			lastChar=tokens[end-1][7]

			# attribute using trigram matching (QUOTE-MENTION-VERB etc.)
			mention=attribute(tokens, start, end, lastChar)

			if mention is None:
				mention=get_dep_parse(tokens, start, end, children)

			if mention is None:
				mention=single_mention(tokens, start, end, children)

			# if that fails and we're within the same paragraph as the last quote, then the mention is the last mention
			if parid == lastParid and mention is None:
				mention=lastMention

			# if that fails, infer speaker from vocative within quote
			#if len(vocs) > 0 and mention != None and parid != lastParid:
		
			# if the quote ends in a question and there is a vocative, make the last vocative the speaker
			if mention == None and lastlastChar == "?" and len(vocs) > 0:
				mention=vocs[-1]

			# if that fails, make the last vocative the speaker
			if mention == None and len(vocs) > 0:
				mention=vocs[-1]


			# if mention is not None:
			# 	print(get_string(mention, tokens))
			if lastParid != parid:
				vocs=[]

			lastMention=mention
			lastParid=parid
			lastlastChar=lastChar
			all_mentions.append(mention)

			# get the vocatives for the current quote to help attribute for the next quote
			for voc in get_vocatives(tokens, start, end):
				vocs.append(voc)

			total+=1
			if mention == None:
				noneCount+=1

			# if mention is not None:
			# 	sys.stderr.write("%s %s\n" % (start, get_string(mention, tokens)))
			# else:
			# 	sys.stderr.write("%s --None\n" % start)
			if mention is not None:
				name=' '.join([tokens[j][8] for j in mention])
				charid=get_char_id(mention[0], mention[-1], tokens)

				# if there isn't an ID'd character but there is a mention, then create a new entity from that string
				if charid is None:

					if name != "he" and name != "she" and name != "his" and name != "her" and name != "they" and name != "it":
						# print("NAME\t%s" % name)
						if name not in seen_ents:
							seen_ents[name]=new_ent_id
							new_ent_id+=1

						charid=seen_ents[name]
				# print(charid)

					if charid is None:
						ents=get_top_entities(tokens, start, end)
						if len(ents) > 0:
							top=ents.most_common()[0][0]
							charid=top

				attributed.append([start, end, mention[0], mention[-1], name, charid])
			else:

				charid=None

				# if there is no mention, try to assign the label of the quote 2 quotes back
				if len(all_char_mentions) >= 2:
					cand=get_previous_in_diff_par(all_char_mentions, quote_starts, len(quote_starts)-1, tokens)
					if cand is not None:
						charid=cand

				
				# if that doesn't work, assign the majority entity in the context
				if charid is None:
					ents=get_top_entities(tokens, start, end)
					if len(ents) > 0:
						top=ents.most_common()[0][0]
						charid=top
				attributed.append([start, end, None, None, None, charid])


			all_char_mentions.append(charid)
			# print(charid)
		# if len(mentions) == 2:
		# 	for idx, (start, end) in enumerate(quotes):
		# 		tmp=[]
		# 		for i in range(start, end):
		# 			tmp.append(tokens[i][7])
				# print ("%s\t%s" % (all_mentions[idx], ' '.join(tmp)))
				# print (' '.join("%s" % x[7] for x in tokens[start,end]))
		#print()
		lastMention=None
		lastParid=None
		lastlastChar=None
		vocs=[]
	
	ratio=0
	if total > 0:
		ratio=noneCount/total
	sys.stderr.write ("%s, None: %.3f (%s/%s)\n" % (filename, ratio, noneCount, total))

	return attributed

def get_char_id(start, end, tokens):

	name=[]
	for tok in range(start, end+1):
		name.append(tokens[tok][8])
	
	name=' '.join(name)

	for token in range(end+1, start-1, -1):
		if tokens[token][14] != "-1":
			if tokens[token][10] != "PRP$":
				return tokens[token][14]

	return None

def write_attributed(filename, attributed):
	with open(filename, "w", encoding="utf-8") as out:
		out.write('\t'.join(["quote_start", "quote_end", "mention_start", "mention_end", "mention_phrase", "char_id"]) + "\n")

		for line in attributed:
			out.write('\t'.join(str(x) for x in line) + "\n")
	
	out.close()

def proc_one(tokensFile, outFile):
	tokens, children=read_tokens(tokensFile)
	attributed=attribute_quotes(outFile, tokens, children)
	write_attributed(outFile, attributed)


if __name__ == "__main__":


	tokenFile=sys.argv[1]
	idd=re.sub(".tokens$", "", tokenFile.split("/")[-1])
	outFile="/data0/dbamman/gutenberg/booknlp/quotes_9.13.19/%s.quotes" % idd
	
	proc_one(tokenFile, outFile)



# if __name__ == "__main__":

# 	ap = argparse.ArgumentParser()
# 	ap.add_argument("--list", required=True)
# 	ap.add_argument("--tokenFolder", required=True)
# 	ap.add_argument("--outFolder", required=True)

# 	args = vars(ap.parse_args())

# 	listFile=args["list"]
# 	tokenFolder=args["tokenFolder"]
# 	outFolder=args["outFolder"]


# 	with open(listFile) as file:
# 		for line in file:
# 			idd=re.sub(".gold$", "", line.rstrip().split("/")[-1])

# 			tokenFile="%s/%s.txt" % (tokenFolder, re.sub("_brat", "", idd))
# 			outFile="%s/%s.preds" % (outFolder, re.sub("_brat", "", idd))
	
# 			proc_one(tokenFile, outFile)



