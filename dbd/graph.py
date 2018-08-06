#!/usr/bin/env python3

"""
This module contains a DAG class that can store and manupulate Directed Acyclic Graphs.

"""

from typing import Dict, List

class DAG:
    """
    A class that stores DAGs (Directed Acyclic Graphs). The nodes are identified by their names, which are strings.
    The implementation guarantees that there are no cycles in the graph.

    """

    def __init__(self) -> None:
        self._nodes: List[str] = []
        self._edges: Dict[str, List[str]] = {}
        self._parentless_nodes: List[str] = []

    @property
    def nodes(self) -> List[str]:
        """
        Returns the nodes of this DAG.

        """

        return self._nodes[:]

    def add_node(self, name: str, parents: List[str]) -> None:
        """
        Adds a node to this DAG.

        Args:
            name: The name of the node to be added.
            parents: The parents of the node to be added. All parents have to be existing nodes in the DAG.

        Raises:
            ValueError: If `name` is already in the DAG or if any parent is not an existing node in the DAG.

        """

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
        """
        Checks whether the DAG contains the given node.

        Args:
            node: The node to check.

        Returns:
            True if the DAG contains `node` as a node; False otherwise.

        """

        return node in self._nodes

    def contains_edge(self, parent: str, child: str) -> bool:
        """
        Checks whether the DAG contains an edge from `parent` to `child`.

        Args:
            parent: The starting node of the edge to be checked.
            child: The end node of the edge to be checked.

        Returns:
            True if an edge exists from `parent` to `child` in the DAG; False otherwise.

        """

        if parent not in self._edges:
            return False

        return child in self._edges[parent]

    def get_children(self, node: str) -> List[str]:
        """
        Returns the children of the given node.

        Args:
            node: The node whose children will be returned.

        Returns:
            The children of `node` in the DAG, i.e all nodes N for which there is an edge from `node` to N.

        """

        if node not in self._edges:
            return []

        return self._edges[node][:]

    def get_parentless_nodes(self) -> List[str]:
        """
        Returns the parentless nodes in the DAG, i.e. the nodes that are not the end node of any edge.

        Returns:
            The parentless nodes in the DAG.

        """

        return self._parentless_nodes[:]

    def get_topologically_sorted_nodes(self) -> List[str]:
        """
        Returns the nodes in the DAG in topologically sorted order, i.e. for every pair of nodes (A, B),
        if there exists an edge A -> B, A comes before B in the order.

        Returns:
            The nodes in the DAG in topologically sorted order.

        """

        # The algorithm is a modified version of https://en.wikipedia.org/wiki/Topological_sorting#Depth-first_search.
        # As it is guaranteed that we are a DAG, no need to check it.

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
    """Builds a DAG instance from a set of acyclic dependencies.

    Args: dependencies: A dictionary where the keys are the dependent nodes and the corresponding values are the nodes
        the keys depend on.

    Returns:
        A DAG instance built from `dependencies`.

    Raises:
        ValueError: If there is a cycle in the dependencies.

    """

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
