import os
import pickle
import json
import time
import random
import numpy as np
import pandas as pd
import networkx as nx


with open('/data0/project/lit_prop/acl/connectors/connector_dict_speakers_only_fixed.pkl', "rb") as input_file:
	connectors_dict = pickle.load(input_file)


folder = '/data0/project/lit_prop/acl/new_char_book_dicts/'
combined_edge_dict = {}
for filename in os.listdir(folder):
	with open(folder + '/' + filename, "rb") as input_file:
		curr_dict = pickle.load(input_file)
		combined_edge_dict.update(curr_dict)


def get_graph(book_id,book_edge_dict):
	elist = []
	for node1,node_dict in book_edge_dict[book_id].items():
		for node2,count in node_dict.items():
			if [str(node2),str(node1)] in elist:
				idx = elist.index([str(node2),str(node1)])
				elist[idx].append(count)
			else:
				elist.append([str(node1),str(node2)])

	G = nx.Graph()
	for edge in elist:
		G.add_edge(edge[0],edge[1],weight=edge[2])
		
	return G


non_connector_node_measures_dict = {}
count = 0

for book_id,nodes in list(connectors_dict.items())[920:1380]:
	
	count+=1
	non_connector_node_measures_dict[book_id] = {}

	G = get_graph(str(book_id),combined_edge_dict)
	
	betweenness_centrality = nx.betweenness_centrality(G)


	for curr_node in nodes['non_connectors']:
		curr_node = str(curr_node)
		try:
			curr_dict = {}

			curr_dict['betweenness_centrality'] = betweenness_centrality[curr_node]
			curr_dict['closeness_centrality'] = nx.closeness_centrality(G,u=curr_node)
			curr_dict['average_neighbor_degree'] = nx.average_neighbor_degree(G,nodes=[curr_node])[curr_node]
			curr_dict['effective_size'] = esize = nx.effective_size(G,nodes=[curr_node])[curr_node]
			curr_dict['efficiency'] = esize/G.degree(curr_node)
			curr_dict['triangles'] = nx.triangles(G,nodes=[curr_node])[curr_node]

			non_connector_node_measures_dict[book_id][curr_node] = curr_dict

		except:
			print('error:')
			print(book_id)
			print(curr_node)
			print()
			continue

with open('/data0/project/lit_prop/acl/non_connector_speaker_node_measures/non_connector_node_measures_dict3.pkl', 'wb') as handle:
	pickle.dump(non_connector_node_measures_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
			
