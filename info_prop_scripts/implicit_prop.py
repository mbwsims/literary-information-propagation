
import ast, os, json, pickle, time
import pandas as pd
import numpy as np


topic_dict = {'love':0,'marry':1,'hate':2,'hurt':3,'wound':3,'strike':4,'hit':4,'beat':4,
             'shoot':5,'kill':6,'murder':6,'slay':6,'capture':7,'arrest':7,'escape':8,
              'innocent':9,'guilty':10,'alive':11,'sick':12,'ill':12,'die':13,'dead':13}

reverse_topic_dict = {i:topic for topic,i in topic_dict.items()}

topic_list = [['love'],['marry'],['hate'],['hurt','wound'],['strike','hit','beat'],
             ['shoot'],['kill','murder','slay'],['capture','arrest'],['escape'],
             ['innocent'],['guilty'],['alive'],['sick','ill'],['die','dead']]

head_words = list(topic_dict.keys())


def get_target_book_ids(tuple_df):
    target_book_ids = []
    grouped_by_book = tuple_df.groupby('bookID')
    for book_id,tuples in grouped_by_book:
        found_match = False
        for row in tuples.iterrows():
            tup = row[1][1]
            words = [word.split('+')[-1] for word in tup.split('_')]
            for word in words:
                if word in head_words:
                    target_book_ids.append(book_id)
                    found_match = True
            if found_match:
                break
    return target_book_ids


def contains_topic(row):
    try:
        tup = row[1]
        words = [word.split('+')[-1] for word in tup.split('_')]
        for word in words:
            if word in topic_words:
                return True
        return False
    except:
        return False


if __name__=="__main__":

    if not os.path.exists('../output/prop_results'):
        os.mkdir('../output/prop_results')
    
    propsFilePath = '../output/implicit_prop_tuples/implicit_tuples'

    tuple_df = pd.read_csv(propsFilePath,sep='\t', names = ['bookID','prop_tuple','tuple_count','sents'])

    prop_dict = {}
    target_book_ids = get_target_book_ids(tuple_df)

    for topic in topic_list:
        topic_words = topic
        filtered = tuple_df.apply(contains_topic,axis=1)
        curr_topic_df = tuple_df[filtered]
        topic_id = topic_dict[topic[0]]
        
        groups = curr_topic_df.groupby('bookID')
        for book_id,group in groups:
            if book_id in target_book_ids:
            
                quotes_df = pd.read_csv('../output/tagger/{}/{}.predicted.qa'.format(book_id,book_id), sep=r'\t',engine='python')

                co_occur_df  = pd.read_csv('../output/char_co_occurrence/{}.csv'.format(book_id))

                for idx, row in group.iterrows():
                    
                    prop_tuple = row['prop_tuple']
                    prop_count = row['tuple_count']
                    tuples_list = json.loads(row['sents'])

                    curr_dict = {}
                    count = 0
                    speakers_list = []
                    listeners_list =  []
                    for tup in tuples_list:
                        curr_dict[count] = {}
                        speaker = quotes_df[quotes_df.quote_start==tup['s']].char_id.values[0]
                        speakers_list.append(speaker)
                        start_quote = tup['s']
                        listeners = co_occur_df[(co_occur_df.start_char<=start_quote) & (co_occur_df.end_char>start_quote)].participants.values[0]
                        listeners = ast.literal_eval(listeners)
                        try:
                            listeners.remove(speaker)
                        except:
                            pass

                        listeners_list.append(listeners)
                        curr_dict[count]['speaker'] = speaker
                        curr_dict[count]['listeners'] = listeners
                        curr_dict[count]['sent'] = tup['sentence']
                        curr_dict[count]['sent_id'] = tup['sent_id']

                        count+=1

                    connectors = set()
                    found_prop =  False
                    foundprop_list = []
                    prop_list_sent_idxs = []
                    possible_Bs = set()
                    for i in range(len(speakers_list)):
                        charA = speakers_list[i]
                        for charB in listeners_list[i]:
                            if charB in speakers_list[i+1:]:
                                charB_idx = speakers_list.index(charB)
                                charCs = listeners_list[charB_idx]
                                prop_charCs = [C for C in charCs if C not in listeners_list[i] and C !=  charA]
                                if prop_charCs:
                                    connectors.add(charB)
                                    found_prop = True
                                    possible_Bs = listeners_list[i].copy() # makes sure they're speakers somewhere in text
                                    possible_Bs.remove(charB)
                                    foundprop_list.append({"a":charA,"b":charB,'c':charCs, 'possible_Bs': possible_Bs})
                                    prop_list_sent_idxs.append({"a":i,"b":charB_idx,'c':charB_idx})

                    prop_dict[idx] = {}
                    prop_dict[idx]['bookId'] = book_id
                    prop_dict[idx]['prop_tuple'] = prop_tuple
                    prop_dict[idx]['prop_count'] = prop_count
                    prop_dict[idx]['topic'] = topic_id
                    prop_dict[idx]['tuple_sents_info'] = curr_dict
                    prop_dict[idx]['prop_success'] = found_prop
                    prop_dict[idx]['connectors'] = connectors
                    if found_prop:
                        prop_dict[idx]['prop_list'] = foundprop_list
                        prop_dict[idx]['prop_sent_idxs'] = prop_list_sent_idxs
                    else:
                        prop_dict[idx]['prop_list'] = []
                        prop_dict[idx]['prop_sent_idxs'] = []

    with open('../output/prop_results/implicit_prop_dict.pkl', 'wb') as handle:
        pickle.dump(prop_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


