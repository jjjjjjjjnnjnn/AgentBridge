"""Tests for Context Compression strategies (pure functions, no mocking needed)."""

from relayos.core.compress import CompressedContext, ContextCompressor


class TestTruncateStrategy:
    def setup_method(self):
        self.compressor = ContextCompressor(strategy="truncate", max_tokens=25)

    def test_truncate_short_content(self):
        """Content under max_chars should not be truncated."""
        text = "Hello, world!"
        result = self.compressor.compress(text)
        assert result.content == text
        assert result.original_chars == len(text)

    def test_truncate_long_content(self):
        """Content over max_chars should be truncated."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. " * 20
        result = self.compressor.compress(text)
        assert result.compressed_chars < result.original_chars
        assert result.compressed_chars > 0

    def test_truncate_empty_string(self):
        """Empty strings should be handled gracefully."""
        self.compressor.max_chars = 100
        result = self.compressor.compress("")
        assert result.content == ""

    def test_truncate_exact_boundary(self):
        """Content exactly at max_chars should not be truncated."""
        text = "A" * 100
        self.compressor.max_chars = 100
        result = self.compressor.compress(text)
        assert len(result.content) >= 100


class TestExtractStrategy:
    def setup_method(self):
        self.compressor = ContextCompressor(strategy="extract", max_tokens=50)

    def test_extract_with_headings(self):
        """Content with headings should extract key sections."""
        text = "# Introduction\nHello\n## Details\nWorld\n# Conclusion\nDone"
        result = self.compressor.compress(text)
        assert len(result.content) > 0

    def test_extract_plain_text(self):
        """Plain text without structure may be truncated."""
        text = "Hello world " * 50
        result = self.compressor.compress(text)
        assert len(result.content) <= len(text)


class TestSummaryStrategy:
    def setup_method(self):
        self.compressor = ContextCompressor(strategy="summary", max_tokens=50)

    def test_summary_uses_intro_and_conclusion(self):
        """Summary should use the first and last parts of content."""
        lines = []
        lines.extend("Intro detail " + str(i) for i in range(20))
        lines.append("# Conclusion")
        lines.extend("Conclusion detail " + str(i) for i in range(10))
        text = "\n".join(lines)
        result = self.compressor.compress(text)
        assert result.compressed_chars < result.original_chars


class TestStructuredStrategy:
    def setup_method(self):
        self.compressor = ContextCompressor(strategy="structured", max_tokens=100)

    def test_structured_preserves_key_value_pairs(self):
        """Structured strategy should preserve key-value patterns."""
        text = "key1: value1\nkey2: value2\nsome random text here"
        result = self.compressor.compress(text)
        assert "key1" in result.content
        assert "key2" in result.content


class TestCompressMetrics:
    def test_ratio_calculation(self):
        """Compression ratio should be between 0 and 1."""
        compressor = ContextCompressor(strategy="truncate", max_tokens=10)
        text = "Hello, world! " * 100
        result = compressor.compress(text)
        assert 0 < result.ratio < 1.0

    def test_all_strategies_return_compressed_context(self):
        """All strategies should return a CompressedContext instance."""
        text = "Test content for compression. key: value"
        for strategy in ("truncate", "extract", "summary", "structured"):
            compressor = ContextCompressor(strategy=strategy, max_tokens=25)
            result = compressor.compress(text)
            assert isinstance(result, CompressedContext)
            assert result.content
            assert result.original_chars == len(text)

    def test_no_compression_when_under_limit(self):
        """Content under max_chars should not be compressed."""
        compressor = ContextCompressor(strategy="truncate", max_tokens=1000)
        text = "Short content."
        result = compressor.compress(text)
        assert result.content == text
        assert result.ratio == 1.0
