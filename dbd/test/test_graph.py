#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

from typing import Dict, List

from graph import build_graph_from_dependencies, DAG

class TestDAG(unittest.TestCase):
    def test_nodes(self) -> None:
        dag = self._get_normal_dag()

        expected_nodes = {"A", "B", "C"}
        nodes = set(dag.nodes)
        self.assertEqual(expected_nodes, nodes)

    def test_contains_node(self) -> None:
        dag = self._get_normal_dag()

        self.assertTrue(dag.contains_node("A"))
        self.assertTrue(dag.contains_node("B"))
        self.assertTrue(dag.contains_node("C"))

        self.assertFalse(dag.contains_node("D"))

    def test_contains_edge(self) -> None:
        dag = self._get_normal_dag()

        self.assertTrue(dag.contains_edge("A", "C"))
        self.assertTrue(dag.contains_edge("B", "C"))

        self.assertFalse(dag.contains_edge("A", "B"))
        self.assertFalse(dag.contains_edge("B", "A"))
        self.assertFalse(dag.contains_edge("C", "A"))
        self.assertFalse(dag.contains_edge("C", "B"))
        self.assertFalse(dag.contains_edge("A", "A"))
        self.assertFalse(dag.contains_edge("B", "B"))
        self.assertFalse(dag.contains_edge("C", "C"))

    def test_get_children(self) -> None:
        dag = self._get_normal_dag()

        self.assertEqual(["C"], dag.get_children("A"))
        self.assertEqual(["C"], dag.get_children("B"))
        self.assertEqual([], dag.get_children("C"))

    def test_get_parentless_nodes(self) -> None:
        dag = self._get_normal_dag()

        self.assertEqual({"A", "B"}, set(dag.get_parentless_nodes()))

    def test_add_node_ok(self) -> None:
        dag = self._get_normal_dag()

        dag.add_node("D", ["A"])

        self.assertTrue(dag.contains_node("D"))
        self.assertTrue("D" in dag.get_children("A"))

    def test_add_node_fails_already_in_dag(self) -> None:
        dag = self._get_normal_dag()

        with self.assertRaises(ValueError):
            dag.add_node("A", [])

    def test_add_node_fails_parent_not_in_dag(self) -> None:
        dag = self._get_normal_dag()

        with self.assertRaises(ValueError):
            dag.add_node("D", ["E"])

    def test_topological_sorting_normal_dag(self) -> None:
        dag = self._get_normal_dag()

        sorted_nodes = dag.get_topologically_sorted_nodes()

        self._validate_topological_order(dag, sorted_nodes)

    def test_topological_sorting_complicated_dag(self) -> None:
        dag = self._get_complicated_dag()

        sorted_nodes = dag.get_topologically_sorted_nodes()

        self._validate_topological_order(dag, sorted_nodes)

    def test_build_graph_from_dependencies_ok(self) -> None:
        dependencies = self._get_normal_dependencies()

        build_graph_from_dependencies(dependencies)

    def test_build_graph_from_dependencies_fails_cyclic_dependencies(self) -> None:
        cyclic_dependencies = self._get_cyclic_dependencies()

        with self.assertRaises(ValueError):
            build_graph_from_dependencies(cyclic_dependencies)

    @staticmethod
    def _get_normal_dag() -> DAG:
        dag = DAG()

        dag.add_node("A", [])
        dag.add_node("B", [])
        dag.add_node("C", ["A", "B"])

        return dag

    @staticmethod
    def _get_complicated_dag() -> DAG:
        dag = DAG()

        dag.add_node("A", [])
        dag.add_node("B", [])

        dag.add_node("C", ["A", "B"])
        dag.add_node("D", ["A", "B"])

        dag.add_node("E", ["C"])
        dag.add_node("F", ["C"])

        return dag

    @staticmethod
    def _get_normal_dependencies() -> Dict[str, List[str]]:
        dependencies = dict()

        dependencies["E"] = ["C"]
        dependencies["F"] = ["D"]

        dependencies["C"] = ["A", "B"]
        dependencies["D"] = ["A", "B"]

        dependencies["A"] = []
        dependencies["B"] = []

        return dependencies

    @staticmethod
    def _get_cyclic_dependencies() -> Dict[str, List[str]]:
        dependencies = dict()

        dependencies["A"] = ["B"]
        dependencies["B"] = ["C"]
        dependencies["C"] = ["D"]
        dependencies["D"] = ["A"]

        return dependencies

    def _validate_topological_order(self, dag: DAG, sorted_nodes: List) -> None:
        dag_nodes = dag.nodes

        if set(dag_nodes) != set(sorted_nodes):
            raise ValueError("The nodes of the dag and the sorted nodes are not the same.")

        if len(dag_nodes) != len(sorted_nodes):
            raise ValueError("The number of sorted nodes differ from the number of nodes in the dag.")

        for node in dag_nodes:
            index = sorted_nodes.index(node)

            children = dag.get_children(node)

            for child in children:
                child_index = sorted_nodes.index(child)

                msg = "Child {} comes before its parent {} in the topologically sorted list.".format(child, node)
                self.assertTrue(index < child_index, msg=msg)
