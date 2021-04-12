import os, pickle, json, time, random
import numpy as np
import pandas as pd
import networkx as nx


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

def get_network_measures(G,btw_centrality):
		try:
			curr_dict = {}

			curr_dict['betweenness_centrality'] = btw_centrality[curr_node]
			curr_dict['closeness_centrality'] = nx.closeness_centrality(G,u=curr_node)
			curr_dict['average_neighbor_degree'] = nx.average_neighbor_degree(G,nodes=[curr_node])[curr_node]
			curr_dict['effective_size'] = esize = nx.effective_size(G,nodes=[curr_node])[curr_node]
			curr_dict['efficiency'] = esize/G.degree(curr_node)
			curr_dict['triangles'] = nx.triangles(G,nodes=[curr_node])[curr_node]

			return curr_dict

		except:
			print('error:')
			print(book_id)
			print(curr_node)
			print()
			return


if __name__ == "__main__":

	outputDIR = '../output/node_measures'
	if not os.path.exists(outputDIR):
		os.mkdir(outputDIR)

	with open('../output/speaker_b_nodes/connector_dict_speakers_only.pkl', "rb") as input_file:
		b_nodes_dict = pickle.load(input_file)

	with open('../output/char_book_dict/char_book_dict.pkl', "rb") as input_file:
		combined_edge_dict = pickle.load(input_file)

	prop_node_measures_dict = {}
	non_prop_node_measures_dict = {}

	for book_id,nodes in list(b_nodes_dict.items()):
		
		prop_node_measures_dict[book_id] = {}
		non_prop_node_measures_dict[book_id] = {}

		G = get_graph(str(book_id),combined_edge_dict)
		
		btw_centrality = nx.betweenness_centrality(G)

		for curr_node in nodes['connectors']:
			curr_node = str(curr_node)
			measures = get_network_measures(G,btw_centrality)
			if measures:
				prop_node_measures_dict[book_id][curr_node] = measures

		for curr_node in nodes['non_connectors']:
			curr_node = str(curr_node)
			measures = get_network_measures(G,btw_centrality)
			if measures:
				non_prop_node_measures_dict[book_id][curr_node] = measures


	with open(os.path.join(outputDIR,'prop_node_measures_dict.pkl'), 'wb') as handle:
		pickle.dump(prop_node_measures_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

	with open(os.path.join(outputDIR,'non_prop_node_measures_dict.pkl'), 'wb') as handle:
		pickle.dump(non_prop_node_measures_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
			
