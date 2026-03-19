import pytest
from shared.lorem_lab import LoremLabManager

def test_generate_words():
    manager = LoremLabManager()

    # test default start
    text = manager.generate_words(5)
    assert text.lower() == "lorem ipsum dolor sit amet"

    # test more than 5
    text = manager.generate_words(10)
    words = text.split(" ")
    assert len(words) == 10
    assert text.lower().startswith("lorem ipsum dolor sit amet")

    # test no start
    text = manager.generate_words(5, start_with_lorem=False)
    words = text.split(" ")
    assert len(words) == 5

    # test 0 count
    assert manager.generate_words(0) == ""

def test_generate_sentences():
    manager = LoremLabManager()

    # test default start
    text = manager.generate_sentences(3)
    sentences = text.split(". ")
    assert len(sentences) == 3
    assert sentences[0].lower().startswith("lorem ipsum dolor sit amet")

    # test no start
    text = manager.generate_sentences(3, start_with_lorem=False)
    sentences = text.split(". ")
    assert len(sentences) == 3
    assert not sentences[0].lower().startswith("lorem ipsum dolor sit amet")

    # test 0 count
    assert manager.generate_sentences(0) == ""

def test_generate_paragraphs():
    manager = LoremLabManager()

    # test default start
    text = manager.generate_paragraphs(2)
    paragraphs = text.split("\n\n")
    assert len(paragraphs) == 2
    assert paragraphs[0].lower().startswith("lorem ipsum dolor sit amet")

    # test no start
    text = manager.generate_paragraphs(2, start_with_lorem=False)
    paragraphs = text.split("\n\n")
    assert len(paragraphs) == 2
    assert not paragraphs[0].lower().startswith("lorem ipsum dolor sit amet")

    # test 0 count
    assert manager.generate_paragraphs(0) == ""
