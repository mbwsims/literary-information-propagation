import sys, re, argparse
from collections import Counter

PINK = '\033[95m'
ENDC = '\033[0m'
BIYellow="\033[1;93m"     # Yellow

def read_tokens(path):

	tokens=[]

	with open(path) as file:
		file.readline()
		for line in file:
			tokens.append(line.rstrip().split("\t"))
	return tokens



validpos={"NN":1, "NNP":1, "NNS":1, "NNPS":1, "DT":1, "PRP$":1, "PRP":1, "JJ":1, "JJR":1, "JJS":1}

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

		word=tokens[i][7]
		pos=tokens[i][10]
		inQuote=tokens[i][13]
		
		if inQuote != "O":
			break
		
		# find verb after quotation
		if pos.startswith("V") or pos == "MD":
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

		# find verb, skipping adverbs and modals
		if pos == "RB" or pos == "RBR" or pos == "MD":
			continue

		if pos.startswith("V"):
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
		# print (inQuote)

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
	mention=trigram_matching_after(tokens, end+1, 5, lastChar)
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

def attribute_quotes(tokens):

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
	for quotes in turns:
		all_mentions=[]
		mentions=Counter()
		for (start, end) in quotes:
			quote=[]
			parid=None
			for j in range(start,end+1):
				quote.append(tokens[j][8])
				parid=tokens[j][0]

			# allt=[]
			# for j in range(start-20,end+20):
			# 	allt.append(tokens[j][8])

			# print("%s\t%s\t%s" % ("---", tokens[start][0], ' '.join(quote)))
			lastChar=tokens[end-1][7]

			# attribute using trigram matching (QUOTE-MENTION-VERB etc.)
			mention=attribute(tokens, start, end, lastChar)

			# if that fails and we're within the same paragraph as the last quote, then the mention is the last mention
			if parid == lastParid and mention == None:
				mention=lastMention

			# if that fails, infer speaker from vocative within quote
			#if len(vocs) > 0 and mention != None and parid != lastParid:
			#	print ("VOC\t%s\t%s" % (vocs[-1], mention))
		
			# if the quote ends in a question and there is a vocative, make the last vocative the speaker
			if mention == None and lastlastChar == "?" and len(vocs) > 0:
				mention=vocs[-1]

			# if that fails, make the last vocative the speaker
			if mention == None and len(vocs) > 0:
				mention=vocs[-1]

			if lastParid != parid:
				vocs=[]

			lastMention=mention
			lastParid=parid
			lastlastChar=lastChar
			all_mentions.append(mention)

			# get the vocatives for the current quote to help attribute for the next quote
			for voc in get_vocatives(tokens, start, end):
				vocs.append(voc)

			# if mention != "he" and mention != "she" and mention != None:
			# 	mentions[mention]+=1
			
			total+=1
			if mention == None:
				noneCount+=1

			if mention is not None:
				name=' '.join([tokens[j][8] for j in mention])
				# print(BIYellow + name + ENDC)
				charid=get_char_id(mention[0], mention[-1])

				attributed.append([start, end, mention[0], mention[-1], name, charid])
			else:
				attributed.append([start, end, None, None, None, None])

		# print("\n\n=======================\n\n")
		#print (mentions.most_common())

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

	print ("None: %.3f (%s/%s)" % (noneCount/total, noneCount, total))

	return attributed

def get_char_id(start, end):

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

if __name__ == "__main__":

	ap = argparse.ArgumentParser()
	ap.add_argument("--tokens", required=True)

	args = vars(ap.parse_args())

	tokensFile=args["tokens"]
	
	print(tokensFile)
	tokens=read_tokens(tokensFile)
	attributed=attribute_quotes(tokens)
	outfile="%s.quote" % tokensFile
	write_attributed(outfile, attributed)