"""Tests for Team Templates (pure data, minimal mocking)."""

from relayos.core.team import TEAM_TEMPLATES, create_team, list_templates


class TestTeamTemplates:
    def test_team_templates_defined(self):
        """TEAM_TEMPLATES should have at least 3 template types."""
        assert len(TEAM_TEMPLATES) >= 3

    def test_each_template_has_required_fields(self):
        """Each team template should have name, description, and workers."""
        for name, template in TEAM_TEMPLATES.items():
            assert template.name
            assert template.description
            assert template.workers
            assert len(template.workers) > 0

    def test_each_worker_has_required_fields(self):
        """Each worker in every template should have required fields."""
        for name, template in TEAM_TEMPLATES.items():
            for w in template.workers:
                assert "name" in w
                assert "role" in w
                assert "provider" in w
                assert "model" in w

    def test_list_templates_returns_dicts_with_correct_keys(self):
        """list_templates should return formatted template info."""
        templates = list_templates()
        for t in templates:
            assert "name" in t
            assert "worker_count" in t
            assert "description" in t
            assert t["worker_count"] > 0

    def test_list_templates_counts_match(self):
        """Worker counts in list_templates should match TEAM_TEMPLATES."""
        templates = list_templates()
        for t in templates:
            expected = len(TEAM_TEMPLATES[t["name"]].workers)
            assert t["worker_count"] == expected


class TestSchemas:
    """Tests for step schemas (pure dict lookups)."""

    def test_step_schemas_defined(self):
        """All step schemas should be importable and defined."""
        from relayos.core.schemas import STEP_SCHEMAS
        assert len(STEP_SCHEMAS) >= 5  # coding, architecture, research, review, writing

    def test_each_schema_has_output_and_prompt(self):
        """Each step schema should define output and prompt_template."""
        from relayos.core.schemas import STEP_SCHEMAS
        for step_type, schema in STEP_SCHEMAS.items():
            assert "output" in schema
            assert "prompt_template" in schema

    def test_get_schema_returns_default_for_unknown(self):
        """get_schema should return product schema for unknown step types."""
        from relayos.core.schemas import get_schema
        schema = get_schema("nonexistent")
        # Returns a default schema, not empty dict
        assert isinstance(schema, dict)
        assert "output" in schema

    def test_get_consumed_fields(self):
        """get_consumed_fields should return a list of field names."""
        from relayos.core.schemas import get_consumed_fields
        fields = get_consumed_fields("coding")
        assert isinstance(fields, list)
