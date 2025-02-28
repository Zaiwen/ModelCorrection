import random
import sys
import time

sys.path.append("")

import utils
import os
import json
from itertools import product
from itertools import combinations
import networkx as nx
import pandas as pd
import joblib


def remove_incorrect_edge(kg, model, node_dict, edge_dict):
    kg_edges = set()
    for edge in kg.edges.data():
        s = edge[0]
        t = edge[1]
        s_node = kg.nodes[s]['label']
        t_node = kg.nodes[t]['label']
        kg_edges.add((s_node, t_node, edge[2]['label']))

    for edge in model.copy().edges.data():
        s_node = edge[0][:-1]
        t_node = edge[1][:-1]
        edge_label = edge[2]['label']
        if (node_dict.get(s_node, -1), node_dict.get(t_node, -1), edge_dict.get(edge_label, -1)) not in kg_edges:
            model.remove_edge(edge[0], edge[1])

    graph = nx.Graph(model)
    components = nx.connected_components(graph)
    largest_component = max(components, key=len)
    return nx.induced_subgraph(model, largest_component)


def largest_components_subgraph(m):
    components = nx.weakly_connected_components(m)
    largest_component = max(components, key=len)
    return nx.DiGraph(nx.induced_subgraph(m, largest_component))


def find_isolate_columns(kg, model: nx.DiGraph, node_dict, edge_dict):

    kg_edges = set()
    for edge in kg.edges.data():
        s = edge[0]
        t = edge[1]
        s_node = kg.nodes[s]['label']
        t_node = kg.nodes[t]['label']
        kg_edges.add((s_node, t_node, edge[2]['label']))

    for edge in model.copy().edges.data():
        s_node = edge[0]
        t_node = edge[1]
        edge_label = edge[2]['label']
        if model.nodes[t_node]["nodeType"] == "InternalNode" and \
                (node_dict.get(s_node[:-1], -1), node_dict.get(t_node[:-1], -1),
                 edge_dict.get(edge_label, -1)) not in kg_edges:
            model.remove_edge(edge[0], edge[1])

    for node in model.copy().nodes:
        if model.nodes[node]["nodeType"] == "InternalNode":
            flag = True
            for succ in model.successors(node):
                if model.nodes[succ]["nodeType"] == "columnNode":
                    flag = False
            if flag:
                model.remove_node(node)

    isolate_columns_dic = {}
    incomplete_model = largest_components_subgraph(model)

    nm = nx.algorithms.isomorphism.categorical_node_match("label", None)
    em = nx.algorithms.isomorphism.categorical_node_match("label", None)
    g = nx.DiGraph()
    cNodes = [node for node in incomplete_model if incomplete_model.nodes[node]["nodeType"] == "columnNode"]
    dgm = nx.isomorphism.DiGraphMatcher(kg, utils.csv_to_lg(incomplete_model.copy()), nm, em)
    if not dgm.subgraph_is_monomorphic():

        for e in nx.edge_bfs(incomplete_model):
            if g.nodes and e[0] not in g.nodes and e[1] not in g.nodes:
                continue
            new_node = e[1] if e[1] not in g.nodes else e[0]
            g.add_node(e[0], label=e[0][:-1])
            g.add_node(e[1], label=e[1][:-1])
            g.add_edge(*e, label=model.edges[e]["label"])
            dgm = nx.isomorphism.DiGraphMatcher(kg, utils.csv_to_lg(g), nm, em)
            if not dgm.subgraph_is_monomorphic():
                g.remove_node(new_node)
        im_nodes = cNodes[:]
        im_nodes.extend(g.nodes)
        incomplete_model = nx.DiGraph(nx.induced_subgraph(incomplete_model, im_nodes))
        incomplete_model = largest_components_subgraph(incomplete_model)

    for cNode in [node for node in model.nodes if model.nodes[node]["nodeType"] == "columnNode"]:
        eNode = list(model.predecessors(cNode))[0]
        if eNode not in incomplete_model:
            learn_types = utils.parse_learned_types(model, cNode)
            isolate_columns_dic[cNode] = learn_types

    return isolate_columns_dic, incomplete_model


def find_isolate_columns1(kg, model: nx.DiGraph):

    kg_edges = set()
    for edge in kg.edges.data():
        s = edge[0]
        t = edge[1]
        s_node = kg.nodes[s]['label']
        t_node = kg.nodes[t]['label']
        kg_edges.add((s_node, t_node, edge[2]['label']))

    # for edge in model.copy().edges.data():
    #     s_node = edge[0]
    #     t_node = edge[1]
    #     edge_label = edge[2]['label']
    #     if model.nodes[t_node]["nodeType"] == "InternalNode" and \
    #             (node_dict.get(s_node[:-1], -1), node_dict.get(t_node[:-1], -1),
    #              edge_dict.get(edge_label, -1)) not in kg_edges:
    #         model.remove_edge(edge[0], edge[1])

    # for node in model.copy().nodes:
    #     if model.nodes[node]["nodeType"] == "InternalNode":
    #         flag = True
    #         for succ in model.successors(node):
    #             if model.nodes[succ]["nodeType"] == "columnNode":
    #                 flag = False
    #         if flag:
    #             model.remove_node(node)

    def largest_components_subgraph(m):
        components = nx.weakly_connected_components(m)
        largest_component = max(components, key=len)
        return nx.DiGraph(nx.induced_subgraph(m, largest_component))

    isolate_columns_dic = {}
    incomplete_model = largest_components_subgraph(model)
    nm = nx.algorithms.isomorphism.categorical_node_match("label", None)
    em = nx.algorithms.isomorphism.categorical_node_match("label", None)
    g = nx.DiGraph()
    cNodes = [node for node in incomplete_model if incomplete_model.nodes[node]["nodeType"] == "columnNode"]
    dgm = nx.isomorphism.DiGraphMatcher(kg, utils.csv_to_lg1(incomplete_model.copy()), nm, em)
    if not dgm.subgraph_is_monomorphic():

        for e in nx.edge_bfs(incomplete_model):
            print(e)
            if g.nodes and e[0] not in g.nodes and e[1] not in g.nodes:
                continue
            new_node = e[1] if e[1] not in g.nodes else e[0]
            g.add_node(e[0], label=e[0][:-1])
            g.add_node(e[1], label=e[1][:-1])
            g.add_edge(*e, label=model.edges[e]["label"])
            dgm = nx.isomorphism.DiGraphMatcher(kg, utils.csv_to_lg1(g), nm, em)
            if not dgm.subgraph_is_monomorphic():
                g.remove_node(new_node)
        im_nodes = cNodes[:]
        im_nodes.extend(g.nodes)
        incomplete_model = nx.DiGraph(nx.induced_subgraph(incomplete_model, im_nodes))
        incomplete_model = largest_components_subgraph(incomplete_model)

    for cNode in [node for node in model.nodes if model.nodes[node]["nodeType"] == "columnNode"]:
        eNode = list(model.predecessors(cNode))[0]
        if eNode not in incomplete_model:
            learn_types = utils.parse_learned_types(model, cNode)
            isolate_columns_dic[cNode] = learn_types

    return isolate_columns_dic, incomplete_model


def func(kg, graph:nx.DiGraph):
    column_nodes = [node for node in graph.nodes if graph.nodes[node]["nodeType"] == "columnNode"]
    # print(column_nodes)
    candidate_nodes = []
    flag = False
    best_score = float("inf")
    for j in range(len(column_nodes)):
        for com in combinations(column_nodes, j):
            # print(com)
            # continue
            # subgraph = nx.DiGraph()
            subgraph = nx.induced_subgraph(graph, [node for node in graph.nodes if node not in com])
            subgraph_lg = utils.csv_to_lg1(subgraph)
            subgraph_isomorphic = check_subgraph_isomorphic(kg, subgraph_lg)
            if subgraph_isomorphic:
                score = 0
                for node in com:
                    learnedTypes = graph.nodes[node]["learnedTypes"]
                    if type(learnedTypes) == float:
                        top_1_type_score = 1
                    else:
                        top_1_type_score = float(learnedTypes.split("\t")[0].split()[2])
                    score += top_1_type_score
                if score < best_score:
                    candidate_nodes = list(com)
                    best_score = score
                flag = True
        if flag:
            break

    return candidate_nodes


def gen_candidate_nodes_combination(iso_col_dic: dict, node_dic: dict):
    ls = []
    for k, v in iso_col_dic.items():
        tmp = []
        for cType in v:
            tmp.append((node_dic[cType[0]], k, cType[0], cType[1]))
        if tmp:
            ls.append(tmp)

    pros = product(*ls)

    return list(pros)


def check_candidate_types(iso_columns_dic, node_dic, kg, im):

    im_lg = utils.csv_to_lg(im)
    nodes = [im_lg.nodes[node]["label"] for node in im_lg.nodes]
    kg_edges = set()
    for edge in kg.edges.data():
        s = edge[0]
        t = edge[1]
        s_node = kg.nodes[s]['label']
        t_node = kg.nodes[t]['label']
        kg_edges.add((s_node, t_node, edge[2]['label']))
    dic = {}
    for col, cTypes in iso_columns_dic.items():
        for ct in cTypes.copy():
            entity = ct[0]
            newNode = node_dic[entity]
            edge_paths = search_edge_paths(newNode, kg_edges, nodes)
            if not check_edge_paths(edge_paths, im_lg, kg):
                if len(cTypes) == 1:
                    dic[col] = [ct[0], ct[1], newNode]
                    pass
                cTypes.remove(ct)
    return dic


def search_edge_paths(newNode, kg_edges, nodes):
    res = []

    def search_adj_nodes(newNode, kg_edges):
        return [edge for edge in kg_edges if edge[1] == newNode], [edge for edge in kg_edges if edge[0] == newNode]

    def dfs(newNode, kg_edges, nodes, visited_nodes, path, res):
        if newNode in nodes:
            res.append(path[:])
            return
        in_edges, out_edges = search_adj_nodes(newNode, kg_edges)
        for in_edge in in_edges:
            adj_node = in_edge[0]
            if adj_node in visited_nodes:
                continue
            path.append(in_edge)
            visited_nodes.append(adj_node)
            dfs(adj_node, kg_edges, nodes, visited_nodes[:], path[:], res)
            path.pop(-1)
        for out_edge in out_edges:
            adj_node = out_edge[1]
            if adj_node in visited_nodes:
                continue
            path.append(out_edge)
            visited_nodes.append(adj_node)
            dfs(adj_node, kg_edges, nodes, visited_nodes[:], path[:], res)
            path.pop(-1)

    dfs(newNode, kg_edges, nodes, [], [], res)
    return res


def check_subgraph_isomorphic(kg, graph, by_monomorphic=False):
    nm = nx.algorithms.isomorphism.categorical_node_match("label", None)
    em = nx.algorithms.isomorphism.categorical_edge_match("label", None)
    dgm = nx.isomorphism.DiGraphMatcher(kg, graph, nm, em)

    if by_monomorphic:
        return dgm.subgraph_is_monomorphic()

    return dgm.subgraph_is_isomorphic()


def check_edge_paths(edge_paths, model, kg):
    by_monomorphic = not check_subgraph_isomorphic(kg, model)
    for edge_path in edge_paths:
        new_model = model.copy()
        new_model_nodes = [new_model.nodes[node]["label"] for node in sorted(new_model.nodes)]
        i = new_model.number_of_nodes()
        for edge in edge_path[::-1]:
            in_node, out_node, edge_label = edge[0], edge[1], edge[2]
            if in_node in new_model_nodes:
                new_model.add_node(i, label=out_node)
                new_model.add_edge(new_model_nodes.index(in_node), i, label=edge_label)
                new_model_nodes.append(out_node)
                i += 1
            elif out_node in new_model_nodes:
                new_model.add_node(i, label=in_node)
                idx = new_model_nodes.index(out_node)
                new_model.add_edge(i, idx, label=edge_label)
                new_model_nodes.append(in_node)
                i += 1
            if not check_subgraph_isomorphic(kg, new_model, by_monomorphic):
                break
        else:
            return True

    return False


def move_incorrect_relation(new_source_idx, im):
    E52_df = pd.read_csv(r"C:\D_Drive\ASM\experiment\exp_20220530\trains_df\E52.csv", header=[0, 1], index_col=0)
    E55_df = pd.read_csv(r"C:\D_Drive\ASM\experiment\exp_20220530\trains_df\E55.csv", header=[0, 1], index_col=0)
    E52_model = joblib.load(r"C:\D_Drive\ASM\experiment\exp_20220530\tree_model\E52.model")
    E55_model = joblib.load(r"C:\D_Drive\ASM\experiment\exp_20220530\tree_model\E55.model")
    E52_features = joblib.load(r"C:\D_Drive\ASM\experiment\exp_20220530\tree_model\E52.features")
    E55_features = joblib.load(r"C:\D_Drive\ASM\experiment\exp_20220530\tree_model\E55.features")
    E52_df = E52_df.loc[[idx for idx in E52_df.index if idx.startswith(f"s{new_source_idx}")]]
    E55_df = E55_df.loc[[idx for idx in E55_df.index if idx.startswith(f"s{new_source_idx}")]]
    E52_df = E52_df.loc[[idx for idx in E52_df.index if idx.split(":")[1] in im.nodes]]
    E55_df = E55_df.loc[[idx for idx in E55_df.index if idx.split(":")[1] in im.nodes]]
    im.remove_nodes_from([node for node in im.nodes if im.nodes[node]["nodeType"] == "columnNode"])

    cols = {}
    if len(E52_df):
        for col, pred in zip(E52_df.index, E52_model.predict(E52_df["features"][E52_features])):
            col = col.split(":")[1]
            if pred == 0:
                im.add_node("E52_Time-Span1", label="E52_Time-Span", nodeType="InternalNode")
                im.add_edge("E67_Birth1", "E52_Time-Span1", label="P4_has_time-span")
                cols[col] = ["E52_Time-Span1", "P82_at_some_time_within"]
            if pred == 1:
                im.add_node("E52_Time-Span2", label="E52_Time-Span", nodeType="InternalNode")
                im.add_edge("E69_Death1", "E52_Time-Span2", label="P4_has_time-span")
                cols[col] = ["E52_Time-Span2", "P82_at_some_time_within"]
            if pred == 2:
                im.add_node("E52_Time-Span3", label="E52_Time-Span", nodeType="InternalNode")
                im.add_edge("E12_Production1", "E52_Time-Span3", label="P4_has_time-span")
                cols[col] = ["E52_Time-Span3", "P82_at_some_time_within"]
            if pred == 3:
                im.add_node("E52_Time-Span4", label="E52_Time-Span", nodeType="InternalNode")
                if "E8_Acquisition1" not in im.nodes:
                    im.add_node("E8_Acquisition1", label="E8_Acquisition")
                    im.add_edge("E22_Man-Made_Object1", "E8_Acquisition1", label="P24i_changed_ownership_through")
                im.add_edge("E8_Acquisition1", "E52_Time-Span4", label="P4_has_time-span")
                cols[col] = ["E52_Time-Span4", "P82_at_some_time_within"]

    if len(E55_df):
        for col, pred in zip(E55_df.index, E55_model.predict(E55_df["features"][E55_features])):
            col = col.split(":")[1]
            if pred == 0:
                im.add_node("E55_Type1", label="E55_Type", nodeType="InternalNode")
                im.add_edge("E12_Production1", "E55_Type1", label="P32_used_general_technique")
                cols[col] = ["E55_Type1", "label"]
            if pred == 1:
                im.add_node("E55_Type2", label="E55_Type", nodeType="InternalNode")
                im.add_edge("E22_Man-Made_Object1", "E55_Type2", label="P2_has_type")
                cols[col] = ["E55_Type2", "label"]
    return cols


def experiments_museum_crm(path):
    res_df = pd.read_csv(rf"{path}\result.csv")
    res_df["running time(s)"] = 0.0
    ofile = open(rf"{path}\isoColumns.txt", "w", encoding="utf-8")

    for i in range(1, 30):
        try:
            # if i != 12:
            #     continue
            kg = utils.load_lg_graph(rf"C:\D_Drive\ASM\DataSets\museum-crm\tmp\lg\museum_kg_s{i}.lg")
            freq_dic = {}.fromkeys(range(24), 0)
            k_model = utils.load_graph_from_csv1\
                (rf"{path}\newSource_{i}\cytoscape\candidate_model.csv")
            start = time.time()
            dic, im = find_isolate_columns(kg, k_model, node_dict, edge_dict)
            cNodes = {e[1]: [e[0], e[2]["label"]] for e in im.edges.data() if im.nodes[e[1]]["nodeType"] == "columnNode"}
            if "E52_Time-Span1" in im.nodes:
                im.remove_node("E52_Time-Span1")
            if "E52_Time-Span2" in im.nodes:
                im.remove_node("E52_Time-Span2")
            if "E52_Time-Span3" in im.nodes:
                im.remove_node("E52_Time-Span3")
            if "E52_Time-Span4" in im.nodes:
                im.remove_node("E52_Time-Span4")
            if "E55_Type1" in im.nodes:
                im.remove_node("E55_Type1")
            if "E55_Type2" in im.nodes:
                im.remove_node("E55_Type2")
            ambiguous_cols = move_incorrect_relation(i, im)
            cNodes.update(ambiguous_cols)
            im_lg = utils.csv_to_lg(im)
            dic1 = check_candidate_types(dic, node_dict, kg, im)
            end = time.time()
            run_time = round((end - start), 3)
            idx = list(res_df["data source"]).index(rf"s{i}.csv")
            res_df["running time(s)"][idx] = run_time
            utils.save_csv_graph(im,
                                 rf"{path}\newSource_{i}\seed.csv")
            utils.save_lg_graph(im_lg,
                                rf"{path}\newSource_{i}\seed.lg")
            print(f"ds: s{i}", file=ofile)
            for k, v in dic.items():
                print(f"isolate column: {k}\n", file=ofile)
                print(f"candidate types: {v}\n", file=ofile)
            isoCols = gen_candidate_nodes_combination(dic, node_dict)
            with open(rf"{path}\newSource_{i}\cNode.json", "w") as jf:
                json.dump(cNodes, jf, indent=2)
            with open(rf"{path}\newSource_{i}\errorCols.json", "w") as jf:
                json.dump(dic1, jf, indent=2)
            with open(rf"{path}\newSource_{i}\isoCols.json", "w") as jf:
                json.dump(isoCols, jf, indent=2)
        except Exception:
            pass
    ofile.close()
    res_df.to_csv(rf"{path}\result.csv", index=False)


def experiments_weapon_lod():

    kg_files = os.listdir("C:\D_Drive\ASM\DataSets\weapon-lod\kg_20220720\lg_20220919")
    print(kg_files)
    for i in range(1, 16):
        if i == 1 or i == 6 or i == 12:
            continue

        start = time.time()
        kg = utils.load_lg_graph(rf"C:\D_Drive\ASM\DataSets\weapon-lod\kg_20220720\lg_20220919\{kg_files[i-1]}")
        # kg = utils.load_lg_graph(rf"C:\D_Drive\ASM\DataSets\museum-edm\kg_20220802\lg_20220914\museum_edm_kg_s{i}.lg")
        kg_edges = set()
        for edge in kg.edges.data():
            s = edge[0]
            t = edge[1]
            s_node = kg.nodes[s]['label']
            t_node = kg.nodes[t]['label']
            kg_edges.add((s_node, t_node, edge[2]['label']))

        c_model = utils.load_graph_from_csv1(rf"C:\D_Drive\ASM\experiment\exp_20220920\newSource_{i}\cytoscape\correct_model.csv")
        # c_model.remove_nodes_from(["Address2324", "Model2378", "Manf2363", "PersonOrOrganization2"])
        # c_model.remove_nodes_from(["Name0846", "For0031"])
        c_model_lg = utils.csv_to_lg1(c_model)
        # entity_subgraph = nx.induced_subgraph(c_model, [node for node in c_model.nodes if c_model.nodes[node]["nodeType"] == "InternalNode"])
        # error_column_nodes = []
        # for edge in entity_subgraph.copy().edges.data():
        #     s_node = edge[0][:-1]
        #     t_node = edge[1][:-1]
        #     edge_label = edge[2]['label']
        #     if (node_dict.get(s_node, -1), node_dict.get(t_node, -1), edge_dict.get(edge_label, -1)) not in kg_edges:
        #         c_model.remove_edge(edge[0], edge[1])
        #
        # for node in entity_subgraph.copy().nodes:
        #     if c_model.copy().nodes[node]["nodeType"] == "InternalNode":
        #         flag = True
        #         for succ in c_model.copy().successors(node):
        #             if c_model.copy().nodes[succ]["nodeType"] == "columnNode":
        #                 flag = False
        #         if flag:
        #             c_model.remove_node(node)
        #
        # seed_model = largest_components_subgraph(c_model)
        # error_column_nodes.extend([node for node in c_model.nodes if
        #                            c_model.nodes[node]["nodeType"] == "columnNode" and node not in seed_model.nodes])
        # subgraphs = utils.split_graph(c_model)
        # for subgraph in subgraphs:
        #     error_column_nodes.extend(func(kg, subgraph))
        #     # print(subgraph.nodes.data())
        # seed_model.remove_nodes_from(error_column_nodes)
        # error_column_nodes.extend(func(kg, seed_model))
        # seed_model.remove_nodes_from(error_column_nodes)
        # print(error_column_nodes)
        # seed_lg = utils.csv_to_lg1(seed_model)

        # lg = nx.DiGraph()
        # lg.add_node(0, label=2)
        # lg.add_node(1, label=0)
        # lg.add_node(2, label=0)
        # lg.add_edge(0, 1, label=2)
        # lg.add_edge(0, 2, label=2)
        # print(i, kg_files[i-1], check_subgraph_isomorphic(kg, lg, by_monomorphic=True))

        # continue


        print(i, kg_files[i-1], check_subgraph_isomorphic(kg, c_model_lg, by_monomorphic=False))

        # print(i, kg_files[i-1], check_subgraph_isomorphic(kg, seed_lg, by_monomorphic=False))

        # print(i, check_subgraph_isomorphic(kg, c_model_lg, by_monomorphic=False))



        # c_model.remove_node("Updated1527")
        # c_model.remove_nodes_from(["Accepted4257", "Name4205", "Name4209", "Fax4229", "Zip4218", "State4214", "PostalAddress1"])


        k_model = utils.load_graph_from_csv1\
            (rf"C:\D_Drive\ASM\experiment\exp_20220920\train_1_6_12___1\newSource_{i}\cytoscape\candidate_model.csv")
        error_column_nodes = []
        entity_subgraph = nx.induced_subgraph(k_model, [node for node in k_model.nodes if k_model.nodes[node]["nodeType"] == "InternalNode"])

        for edge in entity_subgraph.copy().edges.data():
            s_node = edge[0][:-1]
            t_node = edge[1][:-1]
            edge_label = edge[2]['label']
            if (node_dict.get(s_node, -1), node_dict.get(t_node, -1), edge_dict.get(edge_label, -1)) not in kg_edges:
                k_model.remove_edge(edge[0], edge[1])

        for node in entity_subgraph.copy().nodes:
            if k_model.copy().nodes[node]["nodeType"] == "InternalNode":
                flag = True
                for succ in k_model.copy().successors(node):
                    if k_model.copy().nodes[succ]["nodeType"] == "columnNode":
                        flag = False
                if flag:
                    k_model.remove_node(node)

        seed_model = largest_components_subgraph(k_model)
        error_column_nodes.extend([node for node in k_model.nodes if
                                   k_model.nodes[node]["nodeType"] == "columnNode" and node not in seed_model.nodes])

        subgraphs = utils.split_graph(k_model)
        for subgraph in subgraphs:
            error_column_nodes.extend(func(kg, subgraph))
            # print(subgraph.nodes.data())
        seed_model.remove_nodes_from(error_column_nodes)
        error_column_nodes.extend(func(kg, seed_model))
        seed_model.remove_nodes_from(error_column_nodes)
        print(error_column_nodes)
        error_column_nodes_dic = {}.fromkeys(error_column_nodes)
        for n in error_column_nodes:
            cTypes = utils.parse_learned_types(k_model, n)
            print(cTypes)
            error_column_nodes_dic[n] = cTypes

        isoCols = gen_candidate_nodes_combination(error_column_nodes_dic, node_dict)
        with open(rf"C:\D_Drive\ASM\experiment\exp_20220920\train_1_6_12___1\newSource_{i}\isoCols.json", "w") as jf:
            json.dump(isoCols, jf, indent=2)
        k_model_lg = utils.csv_to_lg1(k_model)
        seed_lg = utils.csv_to_lg1(seed_model)
        utils.save_lg_graph(seed_lg, rf"C:\D_Drive\ASM\experiment\exp_20220920\train_1_6_12___1\newSource_{i}\seed.lg")
        #
        nm = nx.algorithms.isomorphism.categorical_node_match("label", None)
        em = nx.algorithms.isomorphism.categorical_edge_match("label", None)
        dgm = nx.isomorphism.DiGraphMatcher(kg, seed_lg, nm, em)
        print(i, check_subgraph_isomorphic(kg, seed_lg, by_monomorphic=False))
        # for node in c_model_lg.nodes.data():
        #     print(node)
        # for edge in c_model_lg.edges.data():
        #     print(edge)
        # c_model_lg.add_node(11, label=0)
        # c_model_lg.add_edge(0, 11, label=15)
        # dgm = nx.isomorphism.DiGraphMatcher(kg, c_model_lg, nm, em)
        # print(i, check_subgraph_isomorphic(kg, k_model_lg))
        # flag = False
        print(i, time.time() - start)


def experiments_museum_edm():

    for i in range(1, 30):
        # if i != 28:
        #     continue
        if i == 1 or i == 6 or i == 12:
            continue

        dir_path = rf"C:\D_Drive\ASM\experiment\exp_20220916\train_1_6_12___1"

        start = time.time()
        kg = utils.load_lg_graph(rf"C:\D_Drive\ASM\DataSets\museum-edm\kg_20220802\lg_20220914\museum_edm_kg_s{i}.lg")
        kg_edges = set()
        for edge in kg.edges.data():
            s = edge[0]
            t = edge[1]
            s_node = kg.nodes[s]['label']
            t_node = kg.nodes[t]['label']
            kg_edges.add((s_node, t_node, edge[2]['label']))

        c_model = utils.load_graph_from_csv1(rf"C:\D_Drive\ASM\experiment\exp_20220825\newSource_{i}\cytoscape\correct_model.csv")

        k_model = utils.load_graph_from_csv1\
            (rf"{dir_path}\newSource_{i}\cytoscape\candidate_model.csv")
        error_column_nodes = []
        entity_subgraph = nx.induced_subgraph(k_model, [node for node in k_model.nodes if k_model.nodes[node]["nodeType"] == "InternalNode"])
        for edge in entity_subgraph.copy().edges.data():
            s_node = edge[0][:-1]
            t_node = edge[1][:-1]
            edge_label = edge[2]['label']
            if (node_dict.get(s_node, -1), node_dict.get(t_node, -1), edge_dict.get(edge_label, -1)) not in kg_edges:
                k_model.remove_edge(edge[0], edge[1])

        for node in entity_subgraph.copy().nodes:
            if k_model.copy().nodes[node]["nodeType"] == "InternalNode":
                flag = True
                for succ in k_model.copy().successors(node):
                    if k_model.copy().nodes[succ]["nodeType"] == "columnNode":
                        flag = False
                if flag:
                    k_model.remove_node(node)

        seed_model = largest_components_subgraph(k_model)
        error_column_nodes.extend([node for node in k_model.nodes if
                                   k_model.nodes[node]["nodeType"] == "columnNode" and node not in seed_model.nodes])

        subgraphs = utils.split_graph(k_model)
        for subgraph in subgraphs:
            error_column_nodes.extend(func(kg, subgraph))
            # print(subgraph.nodes.data())
        seed_model.remove_nodes_from(error_column_nodes)
        error_column_nodes.extend(func(kg, seed_model))
        seed_model.remove_nodes_from(error_column_nodes)
        print(error_column_nodes)
        error_column_nodes_dic = {}.fromkeys(error_column_nodes)
        for n in error_column_nodes:
            cTypes = utils.parse_learned_types(k_model, n)
            print(cTypes)
            error_column_nodes_dic[n] = cTypes

        isoCols = gen_candidate_nodes_combination(error_column_nodes_dic, node_dict)
        with open(rf"{dir_path}\newSource_{i}\isoCols.json", "w") as jf:
            json.dump(isoCols, jf, indent=2)
        k_model_lg = utils.csv_to_lg1(k_model)
        seed_lg = utils.csv_to_lg1(seed_model)
        utils.save_lg_graph(seed_lg, rf"{dir_path}\newSource_{i}\seed.lg")

        nm = nx.algorithms.isomorphism.categorical_node_match("label", None)
        em = nx.algorithms.isomorphism.categorical_edge_match("label", None)
        dgm = nx.isomorphism.DiGraphMatcher(kg, seed_lg, nm, em)
        print(i, check_subgraph_isomorphic(kg, seed_lg, by_monomorphic=False))
        # c_model_lg = utils.csv_to_lg1(c_model)
        # dgm = nx.isomorphism.DiGraphMatcher(kg, c_model_lg, nm, em)
        # print(i, check_subgraph_isomorphic(kg, c_model_lg, by_monomorphic=False))
        # print(i, check_subgraph_isomorphic(kg, k_model_lg))
        # flag = False
        print(i, time.time() - start)


def experiments1(path):
    res_df = pd.read_csv(rf"{path}\result.csv")
    res_df["running time(s)"] = 0.0
    ofile = open(rf"{path}\isoColumns.txt", "w", encoding="utf-8")
    for i in range(1, 30):
        try:
            # if i != 28:
            #     continue
            kg = utils.load_lg_graph(rf"C:\D_Drive\ASM\DataSets\museum-crm\tmp\lg\museum_kg_s{i}.lg")
            freq_dic = {}.fromkeys(range(24), 0)
            node_set = set()
            for node in kg.nodes:
                freq_dic[kg.nodes[node]["label"]] += 1
                if kg.in_degree(node) == 0 or kg.out_degree(node) == 0:
                    node_set.add(kg.nodes[node]["label"])
            kg_edges = set()
            for edge in kg.edges.data():
                s = edge[0]
                t = edge[1]
                s_node = kg.nodes[s]['label']
                t_node = kg.nodes[t]['label']
                kg_edges.add((s_node, t_node, edge[2]['label']))

            k_model = utils.load_graph_from_csv1\
                (rf"{path}\newSource_{i}\cytoscape\candidate_model.csv")
            start = time.time()
            dic, im = find_isolate_columns(kg, k_model, node_dict, edge_dict)
            cNodes = {e[1]: [e[0], e[2]["label"]] for e in im.edges.data() if im.nodes[e[1]]["nodeType"] == "columnNode"}
            if "E52_Time-Span1" in im.nodes:
                im.remove_node("E52_Time-Span1")
            if "E52_Time-Span2" in im.nodes:
                im.remove_node("E52_Time-Span2")
            if "E52_Time-Span3" in im.nodes:
                im.remove_node("E52_Time-Span3")
            if "E52_Time-Span4" in im.nodes:
                im.remove_node("E52_Time-Span4")
            if "E55_Type1" in im.nodes:
                im.remove_node("E55_Type1")
            if "E55_Type2" in im.nodes:
                im.remove_node("E55_Type2")
            ambiguous_cols = move_incorrect_relation(i, im)
            cNodes.update(ambiguous_cols)
            im_lg = utils.csv_to_lg(im)
            dic1 = check_candidate_types(dic, node_dict, kg, im)
            end = time.time()
            run_time = round((end - start), 3)
            idx = list(res_df["data source"]).index(rf"s{i}.csv")
            res_df["running time(s)"][idx] = run_time
            utils.save_csv_graph(im,
                                 rf"{path}\newSource_{i}\seed.csv")
            utils.save_lg_graph(im_lg,
                                rf"{path}\newSource_{i}\seed.lg")
            print(f"ds: s{i}", file=ofile)
            # ofile.write(f"ds: s{i}")
            for k, v in dic.items():
                print(f"isolate column: {k}\n", file=ofile)
                print(f"candidate types: {v}\n", file=ofile)

            isoCols = gen_candidate_nodes_combination(dic, node_dict)
            with open(rf"{path}\newSource_{i}\cNode.json", "w") as jf:
                json.dump(cNodes, jf, indent=2)
            with open(rf"{path}\newSource_{i}\errorCols.json", "w") as jf:
                json.dump(dic1, jf, indent=2)
            with open(rf"{path}\newSource_{i}\isoCols.json", "w") as jf:
                json.dump(isoCols, jf, indent=2)
        except Exception:
            pass
    ofile.close()
    res_df.to_csv(rf"{path}\result.csv", index=False)


if __name__ == '__main__':
    node_dict, edge_dict = utils.load_dict()
    # experiments1(rf"C:\D_Drive\ASM\experiment\exp_20220712")
    # experiments_weapon_lod(rf"C:\D_Drive\ASM\experiment\exp_20220721")
    # experiments_museum_edm(rf"C:\D_Drive\ASM\experiment\exp_20220811")
    # dir_path = rf"C:\D_Drive\ASM\experiment\exp_20220705\train_1_15___1"
    # experiments_museum_crm(dir_path)
    # experiments_museum_edm()
    # experiments_weapon_lod()



    sys.exit(1)