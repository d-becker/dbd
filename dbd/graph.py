#!/usr/bin/env python3

from typing import Dict, List

class DAG:
    def __init__(self) -> None:
        self._nodes: List[str] = []
        self._edges: Dict[str, List[str]] = {}
        self._parentless_nodes: List[str] = []

    @property
    def nodes(self) -> List[str]:
        return self._nodes[:]

    def add_node(self, name: str, parents: List[str]) -> None:
        if name in self.nodes:
            raise ValueError("The node with name {} is already in the DAG.".format(name))

        for parent in parents:
            if parent not in self.nodes:
                raise ValueError("The parent node with name {} is not in the DAG.".format(parent))

        for parent in parents:
            if parent not in self._edges:
                self._edges[parent] = []

            self._edges[parent].append(name)

        if len(parents) == 0:
            self._parentless_nodes.append(name)

        self._nodes.append(name)

    def contains_node(self, node: str) -> bool:
        return node in self._nodes

    def contains_edge(self, parent: str, child: str) -> bool:
        if parent not in self._edges:
            return False

        return child in self._edges[parent]

    def get_children(self, name: str) -> List[str]:
        if name not in self._edges:
            return []

        return self._edges[name][:]

    def get_parentless_nodes(self) -> List[str]:
        return self._parentless_nodes[:]

    def get_topologically_sorted_nodes(self) -> List[str]:
        """
        A modified version of https://en.wikipedia.org/wiki/Topological_sorting#Depth-first_search.
        As it is guaranteed that we are a DAG, no need to check it.
        """

        topological_order: List[str] = []

        for node in self.get_parentless_nodes():
            self._visit_node(node, topological_order)

        return topological_order

    def _visit_node(self, node: str, topological_order: List[str]) -> None:
        if node in topological_order:
            return

        for child in self.get_children(node):
            self._visit_node(child, topological_order)

        topological_order.insert(0, node)

def build_graph_from_dependencies(dependencies: Dict[str, List[str]]) -> DAG:
    dag = DAG()

    for node in dependencies:
        _add_node_to_dag_recursively(dependencies, node, dag, [])

    return dag

def _add_node_to_dag_recursively(dependencies_by_node: Dict[str, List[str]],
                                 node_to_add: str,
                                 dag: DAG,
                                 pending: List[str]) -> None:
    if dag.contains_node(node_to_add):
        return

    if node_to_add in pending:
        elements = pending[:]
        elements.append(node_to_add)
        raise ValueError("Cycle detected in the graph containing the following elements: {}.".format(str(elements)))

    deps = dependencies_by_node[node_to_add]

    new_pending = pending[:]
    new_pending.append(node_to_add)

    for dependency in deps:
        _add_node_to_dag_recursively(dependencies_by_node, dependency, dag, new_pending)

    dag.add_node(node_to_add, deps)
