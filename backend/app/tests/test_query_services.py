from app.services.hybrid_search_service import fuse_scores
from app.services.optimization_service import optimize_query
from app.services.sparse_search_service import sparse_score


def test_sparse_score_rewards_query_term_overlap() -> None:
    matching = sparse_score("leave policy", {"leave": 2, "policy": 1})
    unrelated = sparse_score("leave policy", {"invoice": 3})

    assert matching > 0.7
    assert unrelated == 0.0


def test_hybrid_fusion_normalizes_dense_and_sparse_weights() -> None:
    fused = fuse_scores(dense_score=0.8, sparse_score=0.5, dense_weight=0.7, sparse_weight=0.3)

    assert fused.dense_score == 0.9
    assert fused.sparse_score == 0.5
    assert fused.hybrid_score == 0.78


def test_query_optimization_adds_domain_terms_for_short_hr_query() -> None:
    response = optimize_query("leave", "HR policy assistant")

    assert response.original_query == "leave"
    assert response.optimized_queries
    assert "eligibility" in response.optimized_queries[0].query
    assert "pto" in response.optimized_queries[0].query
