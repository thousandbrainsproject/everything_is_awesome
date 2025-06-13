from glob import glob

import torch

files = glob("*.pt")
graph_memory = {}
graph_id_to_target = {}
target_to_graph_id = {}

for file in files:
    pretrained_graphs = torch.load(file)
    graph = pretrained_graphs["lm_dict"][0]["graph_memory"]
    key = list(graph.keys())[0]
    graph_memory[key] = graph[key]

    graph_id_to_target[key] = {key}
    target_to_graph_id[key] = {key}

combined_graphs = {
    "lm_dict": {
        0: {
            "graph_memory": graph_memory,
            "graph_id_to_target": graph_id_to_target,
            "target_to_graph_id": target_to_graph_id,
        }
    }
}
torch.save(combined_graphs, "model.pt")
