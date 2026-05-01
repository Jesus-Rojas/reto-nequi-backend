import pytest

from app.services.content_filter import ContentFilterService


@pytest.fixture
def svc():
    return ContentFilterService()


class TestContainsInappropriateContent:
    def test_clean_content_returns_false(self, svc):
        assert svc.contains_inappropriate_content("Hola, ¿cómo estás?") is False

    def test_exact_forbidden_word_returns_true(self, svc):
        assert svc.contains_inappropriate_content("esto es spam") is True

    def test_case_insensitive_detection(self, svc):
        assert svc.contains_inappropriate_content("SPAM en el mensaje") is True

    def test_forbidden_word_embedded_in_sentence(self, svc):
        assert svc.contains_inappropriate_content("Es un idiota total") is True

    def test_empty_string_returns_false(self, svc):
        assert svc.contains_inappropriate_content("") is False


class TestFilterContent:
    def test_clean_content_unchanged(self, svc):
        content = "Mensaje limpio y seguro."
        result, was_filtered = svc.filter_content(content)
        assert result == content
        assert was_filtered is False

    def test_forbidden_word_is_censored(self, svc):
        result, was_filtered = svc.filter_content("Es puro spam esto")
        assert "spam" not in result.lower()
        assert was_filtered is True

    def test_censored_word_replaced_with_asterisks(self, svc):
        result, _ = svc.filter_content("Es spam del malo")
        assert "****" in result  # "spam" → "****"

    def test_multiple_forbidden_words_all_censored(self, svc):
        result, was_filtered = svc.filter_content("spam y scam en el mensaje")
        assert "spam" not in result.lower()
        assert "scam" not in result.lower()
        assert was_filtered is True

    def test_case_insensitive_replacement(self, svc):
        result, was_filtered = svc.filter_content("Es un IDIOTA")
        assert "idiota" not in result.lower()
        assert was_filtered is True

    def test_custom_forbidden_words(self):
        svc_custom = ContentFilterService(forbidden_words=["banana"])
        result, was_filtered = svc_custom.filter_content("I like banana smoothies")
        assert "banana" not in result.lower()
        assert was_filtered is True

    def test_custom_forbidden_words_dont_trigger_on_default(self):
        svc_custom = ContentFilterService(forbidden_words=["banana"])
        result, was_filtered = svc_custom.filter_content("Este es spam")
        # "spam" is NOT in the custom list, so it must pass through
        assert result == "Este es spam"
        assert was_filtered is False
