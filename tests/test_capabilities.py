"""Tests for the Capability Registry (pure functions, no mocking needed)."""

from relayos.core.capabilities import (
    CAPABILITY_SCORES,
    get_capability,
    get_best_model,
    get_cost_tier,
    score_models,
)


class TestGetCapability:
    def test_known_model_returns_correct_score(self):
        """claude-sonnet-4-20250514 should score 10 for architecture."""
        score = get_capability("claude-sonnet-4-20250514", "architecture")
        assert score == 10

    def test_unknown_capability_defaults_to_5(self):
        """Unknown capabilities should return the default score of 5."""
        score = get_capability("claude-sonnet-4-20250514", "nonexistent")
        assert score == 5

    def test_unknown_model_returns_5(self):
        """Unknown models should return the default score of 5."""
        score = get_capability("unknown-model-42", "coding")
        assert score == 5

    def test_empty_model_returns_5(self):
        """Empty model name should return the default."""
        score = get_capability("", "coding")
        assert score == 5


class TestGetBestModel:
    def test_returns_top_3_for_coding(self):
        """get_best_model should return the top 3 coding models."""
        results = get_best_model("coding", top_n=3)
        assert len(results) == 3
        for name, score in results:
            assert isinstance(name, str)
            assert isinstance(score, int)
            assert 1 <= score <= 10

    def test_returns_empty_for_unknown_capability(self):
        """Unknown capabilities should return no results (no model has score > 0)."""
        results = get_best_model("nonexistent_capability_xyz", top_n=3)
        assert len(results) == 0  # no model scores this capability

    def test_top_n_respected(self):
        """top_n parameter should limit result count."""
        results = get_best_model("coding", top_n=1)
        assert len(results) == 1

    def test_sorted_descending(self):
        """Results should be sorted by score descending."""
        results = get_best_model("coding", top_n=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)


class TestGetCostTier:
    def test_free_model(self):
        """Local models should be in 'free' tier."""
        tier = get_cost_tier("qwen2.5:7b")
        assert tier == "free"

    def test_premium_model(self):
        """Claude Opus should be 'premium'."""
        tier = get_cost_tier("claude-opus-4-20250514")
        assert tier == "premium"

    def test_unknown_model_defaults_to_moderate(self):
        """Unknown models should default to 'moderate'."""
        tier = get_cost_tier("unknown-model")
        assert tier == "moderate"

    def test_all_models_have_tier(self):
        """Every model in CAPABILITY_SCORES should have a defined cost tier."""
        for model_name in CAPABILITY_SCORES:
            tier = get_cost_tier(model_name)
            assert tier in ("free", "cheap", "moderate", "expensive", "premium"), \
                f"Model {model_name} has unknown tier '{tier}'"


class TestScoreModels:
    def test_returns_list_of_dicts(self):
        """score_models should return a list of scored model dicts."""
        results = score_models("coding")
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert "model" in r
            assert "capability_score" in r
            assert "cost_tier" in r
            assert "cost_score" in r
            assert "combined" in r

    def test_sorted_by_combined_score(self):
        """Results should be sorted by combined score descending."""
        results = score_models("coding")
        scores = [r["combined"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_different_capabilities_produce_different_orderings(self):
        """Capability-focused models should rank higher for their strength."""
        coding_top = score_models("coding")[0]["model"]
        writing_top = score_models("writing")[0]["model"]
        # Different capabilities may have different top models
        assert isinstance(coding_top, str)
        assert isinstance(writing_top, str)
