"""Tests for dependency_graph.py — directed dependency analysis."""
import pytest

from dependency_graph import (
    load_problems,
    build_dependency_graph,
    strongly_connected_components,
    topological_layers,
    keystone_problems,
    critical_paths,
    orphan_problems,
    influence_flow,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def graph(problems):
    return build_dependency_graph(problems)


class TestBuildGraph:
    """Test directed graph construction."""

    def test_returns_dict(self, graph):
        assert isinstance(graph, dict)

    def test_has_nodes(self, graph, problems):
        assert len(graph["nodes"]) == len(problems)

    def test_has_edges(self, graph):
        assert graph["n_edges"] > 0

    def test_has_edge_types(self, graph):
        assert "oeis_bridge" in graph["edge_type_counts"]
        assert "oeis_cooccurrence" in graph["edge_type_counts"]
        assert "tag_containment" in graph["edge_type_counts"]

    def test_adjacency_structure(self, graph):
        for src, edges in graph["adjacency"].items():
            assert isinstance(edges, list)
            for tgt, weight, etype in edges:
                assert isinstance(tgt, int)
                assert weight > 0
                assert isinstance(etype, str)

    def test_oeis_bridge_most_common(self, graph):
        # OEIS bridges should be the most common edge type
        counts = graph["edge_type_counts"]
        assert counts["oeis_bridge"] > counts["oeis_cooccurrence"]

    def test_edge_count_consistency(self, graph):
        total_from_adj = sum(len(edges) for edges in graph["adjacency"].values())
        assert total_from_adj == graph["n_edges"]


class TestSCC:
    """Test strongly connected component detection."""

    def test_returns_list(self, graph):
        sccs = strongly_connected_components(graph)
        assert isinstance(sccs, list)

    def test_covers_all_nodes(self, graph):
        sccs = strongly_connected_components(graph)
        all_nodes = set()
        for scc in sccs:
            all_nodes.update(scc)
        assert all_nodes == graph["nodes"]

    def test_no_overlaps(self, graph):
        sccs = strongly_connected_components(graph)
        all_nodes = []
        for scc in sccs:
            all_nodes.extend(scc)
        assert len(all_nodes) == len(set(all_nodes))

    def test_sorted_by_size(self, graph):
        sccs = strongly_connected_components(graph)
        for i in range(len(sccs) - 1):
            assert len(sccs[i]) >= len(sccs[i + 1])

    def test_has_large_component(self, graph):
        sccs = strongly_connected_components(graph)
        assert len(sccs[0]) > 100  # expect a large SCC


class TestTopologicalLayers:
    """Test topological layering."""

    def test_returns_dict(self, graph):
        result = topological_layers(graph)
        assert isinstance(result, dict)

    def test_has_layers(self, graph):
        result = topological_layers(graph)
        assert len(result["layers"]) > 0

    def test_depth_nonneg(self, graph):
        result = topological_layers(graph)
        for num, d in result["depth"].items():
            assert d >= 0

    def test_max_depth_positive(self, graph):
        result = topological_layers(graph)
        assert result["max_depth"] > 0

    def test_layer_0_has_sources(self, graph):
        result = topological_layers(graph)
        assert len(result["layers"][0]) > 0


class TestKeystoneProblems:
    """Test keystone problem identification."""

    def test_returns_list(self, problems, graph):
        result = keystone_problems(problems, graph)
        assert isinstance(result, list)

    def test_has_keystones(self, problems, graph):
        result = keystone_problems(problems, graph)
        assert len(result) > 0

    def test_keystone_fields(self, problems, graph):
        result = keystone_problems(problems, graph)
        for k in result:
            assert "number" in k
            assert "downstream_open" in k
            assert "tags" in k

    def test_sorted_by_downstream(self, problems, graph):
        result = keystone_problems(problems, graph)
        for i in range(len(result) - 1):
            assert result[i]["downstream_open"] >= result[i + 1]["downstream_open"]

    def test_downstream_positive(self, problems, graph):
        result = keystone_problems(problems, graph)
        for k in result:
            assert k["downstream_open"] > 0

    def test_top_k_respected(self, problems, graph):
        result = keystone_problems(problems, graph, top_k=5)
        assert len(result) <= 5


class TestCriticalPaths:
    """Test critical path detection."""

    def test_returns_list(self, problems, graph):
        result = critical_paths(problems, graph)
        assert isinstance(result, list)

    def test_path_fields(self, problems, graph):
        result = critical_paths(problems, graph)
        for p in result:
            assert "path" in p
            assert "length" in p
            assert "tags" in p

    def test_paths_sorted_by_length(self, problems, graph):
        result = critical_paths(problems, graph)
        for i in range(len(result) - 1):
            assert result[i]["length"] >= result[i + 1]["length"]

    def test_minimum_path_length(self, problems, graph):
        result = critical_paths(problems, graph)
        for p in result:
            assert p["length"] >= 3

    def test_path_length_consistent(self, problems, graph):
        result = critical_paths(problems, graph)
        for p in result:
            assert len(p["path"]) == p["length"]


class TestOrphanProblems:
    """Test orphan problem detection."""

    def test_returns_list(self, problems, graph):
        result = orphan_problems(problems, graph)
        assert isinstance(result, list)

    def test_orphan_fields(self, problems, graph):
        result = orphan_problems(problems, graph)
        for o in result:
            assert "number" in o
            assert "tags" in o
            assert "out_degree" in o

    def test_sorted_by_out_degree(self, problems, graph):
        result = orphan_problems(problems, graph)
        for i in range(len(result) - 1):
            assert result[i]["out_degree"] >= result[i + 1]["out_degree"]


class TestInfluenceFlow:
    """Test influence cascade simulation."""

    def test_returns_dict(self, problems, graph):
        result = influence_flow(problems, graph)
        assert isinstance(result, dict)

    def test_has_waves(self, problems, graph):
        result = influence_flow(problems, graph)
        assert "waves" in result
        assert "total_influenced" in result

    def test_total_positive(self, problems, graph):
        result = influence_flow(problems, graph)
        assert result["total_influenced"] > 0

    def test_custom_seeds(self, problems, graph):
        open_probs = [p for p in problems if p.get("status", {}).get("state") == "open"]
        if open_probs:
            seed = int(open_probs[0].get("number", 0))
            if seed > 0:
                result = influence_flow(problems, graph, seed_problems=[seed])
                assert isinstance(result, dict)

    def test_wave_count_nonneg(self, problems, graph):
        result = influence_flow(problems, graph)
        for w in result["waves"]:
            assert w["count"] > 0

    def test_waves_sequential(self, problems, graph):
        result = influence_flow(problems, graph)
        for i, w in enumerate(result["waves"]):
            assert w["wave"] == i + 1
