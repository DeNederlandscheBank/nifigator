# -*- coding: utf-8 -*-

import datetime
import logging
import re
import uuid
from io import StringIO

import unidecode
from lxml import etree
from rdflib.namespace import XSD
from rdflib.term import Literal
import syntok.segmenter as segmenter

def to_iri(s: str = ""):
    return (
        s.replace('"', "%22")
        .replace("µ", "mu")
        .replace("ª", "_")
        .replace("º", "_")
        .replace("'", "%27")
        .replace(">", "")
        .replace("<", "")
    )
    
def tokenize_text(
    text: list=None,
    forced_sentence_split_characters: list=[]
    ):
    """ """
    tokenized_text = tokenizer(text)
    tokenized_new = []
    for sentence in tokenized_text:
        tok_sent = []
        for token in sentence:
            if token['text'] in forced_sentence_split_characters:
                if tok_sent != []:
                    tokenized_new.append(tok_sent)
                tok_sent = []
            tok_sent.append(token)
        tokenized_new.append(tok_sent)
    tokenized_text = tokenized_new
    # delete empty tokens
    if tokenized_text != []:
        tokenized_text = [sentence if sentence[-1]['text']!="" else sentence[:-1] for sentence in tokenized_text]
    return tokenized_text


def replace_escape_characters(text: str = None):
    """
    Function to replace espace characters by spaces (maintaining exact character locations)

    :param text: the text where escape characters should be replaces

    """
    escape_characters = [
        "\a",  # bell
        "\b",  # back space
        "\t",  # tab
        "\n",  # new line
        "\v",  # vertical tab
        "\f",  # form feed
        "\r",  # carriage return
    ]
    escape_character_table = {
        ord(escape_character): " " for escape_character in escape_characters
    }
    return text.translate(escape_character_table)


def tokenizer(text: str = None):
    """
    Function to create list of sentences with list of words
    with text and start_char and end_char of each word

    :param text: the text to be tokenized

    """
    sentences = list()
    for paragraph in segmenter.analyze(text):
        for sentence in paragraph:
            words = list()
            for token in sentence:
                value = text[token.offset : token.offset + len(token.value)]
                if value != token.value:
                    logging.error("Error: incorrect offsets in syntok.segmenter.")
                else:
                    words.append(
                        {
                            "text": token.value,
                            "start_char": token.offset,
                            "end_char": token.offset + len(token.value),
                        }
                    )
            sentences.append(words)
    return sentences


def align_stanza_dict_offsets(stanza_dict: list = None, sentences: list = None):
    """
    Function to align the stanza dict offsets with the offsets from the tokenizer

    :param stanza_dict: the output dict from the Stanza pipeline

    :param sentences: the output of the tokenizer

    """
    # check alignment of stanza_dict and tokenized_document
    assert len(stanza_dict) == len(sentences)
    for sent_idx, sent in enumerate(stanza_dict):
        assert len(stanza_dict[sent_idx]) == len(sentences[sent_idx])

    # correct stanza_dict start_char and end_char
    for sent_idx, sent in enumerate(stanza_dict):
        for word_idx, word in enumerate(sent):
            word["start_char"] = sentences[sent_idx][word_idx]["start_char"]
            word["end_char"] = sentences[sent_idx][word_idx]["end_char"]

    return stanza_dict


def generate_uuid(uri: str = None, prefix: str = "nif-"):
    """
    Function to generate the uuid for nif

    :param uri: the uri from which the uuid should be generated

    :param prefix: the prefix of the uuid, default = "nif-"

    """
    return prefix + uuid.uuid3(uuid.NAMESPACE_DNS, uri).hex


def natural_sort(elements: list = None):
    """
    Function to sort a list of strings with numbers

    :param elements: the list to be sorted

    """

    def convert_to_int(text):
        return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key):
        return [convert_to_int(c) for c in re.split("([0-9]+)", key)]

    return sorted(elements, key=alphanum_key)


def delete_accents(text: str = None, lang: str = "en"):
    """
    Function to delete accents from a string

    :param text: the string from which the accents should be deleted

    :param lang: the language of the text in the string

    """
    if lang == Literal("grc", datatype=XSD.string):
        replacements = {
            "ἒ": "ἐ",
            "ἓ": "ἑ",
            "ἔ": "ἐ",
            "ἕ": "ἑ",
            "έ": "ε",
            "ὲ": "ε",
            "έ": "ε",
            "ἂ": "ἀ",
            "ἃ": "ἁ",
            "ἄ": "ἀ",
            "ἅ": "ἁ",
            "ά": "α",
            "ὰ": "α",
            "ά": "α",
            "ᾂ": "ᾀ",
            "ᾄ": "ᾀ",
            "ᾃ": "ᾁ",
            "ᾅ": "ᾁ",
            "ᾲ": "ᾳ",
            "ᾴ": "ᾳ",
            "ί": "ι",
            "ἲ": "ἰ",
            "ἳ": "ἱ",
            "ἴ": "ἰ",
            "ἵ": "ἱ",
            "ῒ": "ϊ",
            "ΐ": "ϊ",
            "ὶ": "ι",
            "ί": "ι",
            "ή": "η",
            "ἢ": "ἠ",
            "ἣ": "ἡ",
            "ἤ": "ἠ",
            "ἥ": "ἡ",
            "ὴ": "η",
            "ή": "η",
            "ΰ": "ϋ",
            "ύ": "υ",
            "ὒ": "ὐ",
            "ὓ": "ὑ",
            "ὔ": "ὐ",
            "ὕ": "ὑ",
            "ὺ": "υ",
            "ύ": "υ",
            "ῢ": "ϋ",
            "ΰ": "ϋ",
            "ὢ": "ὠ",
            "ὣ": "ὡ",
            "ὤ": "ὠ",
            "ὥ": "ὡ",
            "ὼ": "ω",
            "ώ": "ω",
            "ό": "ο",
            "ὂ": "ὀ",
            "ὃ": "ὁ",
            "ὄ": "ὀ",
            "ὅ": "ὁ",
            "ὸ": "ο",
            "ό": "ο",
            "ᾢ": "ᾠ",
            "ᾣ": "ᾡ",
            "ᾤ": "ᾠ",
            "ᾥ": "ᾡ",
            "ῲ": "ῳ",
            "ῴ": "ῳ",
        }
        for replacement in replacements.keys():
            text = text.replace(replacement, replacements[replacement])
    else:
        text = unidecode.unidecode(text)
    return text


def delete_diacritics(text: str = None, lang: str = "en"):
    """
    Function to delete diacritics from a string

    :param text: the string from which the diacritics should be deleted

    :param lang: the language of the text in the string

    """
    if lang == Literal("grc", datatype=XSD.string):
        replacements = {
            "Ά": "Α",
            "Ᾰ": "Α",
            "Ᾱ": "Α",
            "Ὰ": "Α",
            "Ά": "Α",
            "Έ": "Ε",
            "Ὲ": "Ε",
            "Έ": "Ε",
            "Ή": "Η",
            "Ὴ": "Η",
            "Ή": "Η",
            "Ί": "Ι",
            "Ϊ": "Ι",
            "Ό": "Ο",
            "Ὸ": "Ο",
            "Ό": "Ο",
            "Ύ": "Υ",
            "Ϋ": "Υ",
            "Ώ": "Ω",
            "ϓ": "ϒ",
            "ϔ": "ϒ",
            "Ὑ": "ϒ",
            "Ὓ": "ϒ",
            "Ὕ": "ϒ",
            "Ὗ": "ϒ",
            "Ῠ": "ϒ",
            "Ῡ": "ϒ",
            "Ὺ": "ϒ",
            "Ύ": "ϒ",
            "ἀ": "α",
            "ἁ": "α",
            "ἂ": "α",
            "ἃ": "α",
            "ἄ": "α",
            "ἅ": "α",
            "ἆ": "α",
            "ἇ": "α",
            "ά": "α",
            "ὰ": "α",
            "ά": "α",
            "ᾰ": "α",
            "ᾱ": "α",
            "ᾶ": "α",
            "Ἀ": "Α",
            "Ἁ": "Α",
            "Ἂ": "Α",
            "Ἃ": "Α",
            "Ἄ": "Α",
            "Ἅ": "Α",
            "Ἆ": "Α",
            "Ἇ": "Α",
            "ἐ": "ε",
            "ἑ": "ε",
            "ἒ": "ε",
            "ἓ": "ε",
            "ἔ": "ε",
            "ἕ": "ε",
            "έ": "ε",
            "ὲ": "ε",
            "έ": "ε",
            "Ἐ": "Ε",
            "Ἑ": "Ε",
            "Ἒ": "Ε",
            "Ἓ": "Ε",
            "Ἔ": "Ε",
            "Ἕ": "Ε",
            "ἠ": "η",
            "ἡ": "η",
            "ἢ": "η",
            "ἣ": "η",
            "ἤ": "η",
            "ἥ": "η",
            "ἦ": "η",
            "ἧ": "η",
            "ή": "η",
            "ὴ": "η",
            "ή": "η",
            "ῆ": "η",
            "Ἠ": "Η",
            "Ἡ": "Η",
            "Ἢ": "Η",
            "Ἣ": "Η",
            "Ἤ": "Η",
            "Ἥ": "Η",
            "Ἦ": "Η",
            "Ἧ": "Η",
            "ἰ": "ι",
            "ἱ": "ι",
            "ἲ": "ι",
            "ἳ": "ι",
            "ἴ": "ι",
            "ἵ": "ι",
            "ἶ": "ι",
            "ἷ": "ι",
            "ΐ": "ι",
            "ϊ": "ι",
            "ί": "ι",
            "ὶ": "ι",
            "ί": "ι",
            "ῐ": "ι",
            "ῑ": "ι",
            "ῒ": "ι",
            "ΐ": "ι",
            "ῖ": "ι",
            "ῗ": "ι",
            "ΰ": "υ",
            "ϋ": "υ",
            "ύ": "υ",
            "ὐ": "υ",
            "ὑ": "υ",
            "ὒ": "υ",
            "ὓ": "υ",
            "ὔ": "υ",
            "ὕ": "υ",
            "ὖ": "υ",
            "ὗ": "υ",
            "ὺ": "υ",
            "ύ": "υ",
            "ῠ": "υ",
            "ῡ": "υ",
            "ῢ": "υ",
            "ΰ": "υ",
            "ῦ": "υ",
            "ῧ": "υ",
            "ό": "ο",
            "ὀ": "ο",
            "ὁ": "ο",
            "ὂ": "ο",
            "ὃ": "ο",
            "ὄ": "ο",
            "ὅ": "ο",
            "ὸ": "ο",
            "ό": "ο",
            "ώ": "ω",
            "ὠ": "ω",
            "ὡ": "ω",
            "ὢ": "ω",
            "ὣ": "ω",
            "ὤ": "ω",
            "ὥ": "ω",
            "ὦ": "ω",
            "ὧ": "ω",
            "ὼ": "ω",
            "ώ": "ω",
            "ῶ": "ω",
            "Ἰ": "Ι",
            "Ἱ": "Ι",
            "Ἲ": "Ι",
            "Ἳ": "Ι",
            "Ἴ": "Ι",
            "Ἵ": "Ι",
            "Ἶ": "Ι",
            "Ἷ": "Ι",
            "Ῐ": "Ι",
            "Ῑ": "Ι",
            "Ὶ": "Ι",
            "Ί": "Ι",
            "Ὀ": "Ο",
            "Ὁ": "Ο",
            "Ὂ": "Ο",
            "Ὃ": "Ο",
            "Ὄ": "Ο",
            "Ὅ": "Ο",
            "Ὠ": "Ω",
            "Ὡ": "Ω",
            "Ὢ": "Ω",
            "Ὣ": "Ω",
            "Ὤ": "Ω",
            "Ὥ": "Ω",
            "Ὦ": "Ω",
            "Ὧ": "Ω",
            "ᾀ": "ᾳ",
            "ᾁ": "ᾳ",
            "ᾂ": "ᾳ",
            "ᾃ": "ᾳ",
            "ᾄ": "ᾳ",
            "ᾅ": "ᾳ",
            "ᾆ": "ᾳ",
            "ᾇ": "ᾳ",
            "ᾲ": "ᾳ",
            "ᾴ": "ᾳ",
            "ᾷ": "ᾳ",
            "ᾈ": "ᾼ",
            "ᾉ": "ᾼ",
            "ᾊ": "ᾼ",
            "ᾋ": "ᾼ",
            "ᾌ": "ᾼ",
            "ᾍ": "ᾼ",
            "ᾎ": "ᾼ",
            "ᾏ": "ᾼ",
            "ᾐ": "ῃ",
            "ᾑ": "ῃ",
            "ᾒ": "ῃ",
            "ᾓ": "ῃ",
            "ᾔ": "ῃ",
            "ᾕ": "ῃ",
            "ᾖ": "ῃ",
            "ᾗ": "ῃ",
            "ῂ": "ῃ",
            "ῄ": "ῃ",
            "ῇ": "ῃ",
            "ᾘ": "ῌ",
            "ᾙ": "ῌ",
            "ᾚ": "ῌ",
            "ᾛ": "ῌ",
            "ᾜ": "ῌ",
            "ᾝ": "ῌ",
            "ᾞ": "ῌ",
            "ᾟ": "ῌ",
            "ᾠ": "ῳ",
            "ᾡ": "ῳ",
            "ᾢ": "ῳ",
            "ᾣ": "ῳ",
            "ᾤ": "ῳ",
            "ᾥ": "ῳ",
            "ᾦ": "ῳ",
            "ᾧ": "ῳ",
            "ῲ": "ῳ",
            "ῴ": "ῳ",
            "ῷ": "ῳ",
            "ᾨ": "ῼ",
            "ᾩ": "ῼ",
            "ᾪ": "ῼ",
            "ᾫ": "ῼ",
            "ᾬ": "ῼ",
            "ᾭ": "ῼ",
            "ᾮ": "ῼ",
            "ᾯ": "ῼ",
            "ῤ": "ρ",
            "ῥ": "ρ",
            "Ῥ": "Ρ",
            "Ὼ": "Ω",
            "Ώ": "Ω",
            "ꭥ": "Ω",
        }
        for replacement in replacements.keys():
            text = text.replace(replacement, replacements[replacement])
    else:
        text = unidecode.unidecode(text)
    return text


def time_in_correct_format(datetime_obj: datetime.datetime) -> str:
    """
    Function that returns the current time (UTC)

    :param datetime_obj: the input to be converted

    Returns:
        str: the time in correct format

    """
    return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SUTC")


def load_dtd(dtd_url: str) -> etree.DTD:
    """Utility function to load the dtd

    :param dtd_url: the location of the dtd file

    Returns:
        etree.DTD: the dtd object to be used for validation

    """
    dtd = None
    r = open(dtd_url)
    if r:
        dtd_file_object = StringIO(r.read())
        dtd = etree.DTD(dtd_file_object)
    if dtd is None:
        logging.error("failed to load dtd from" + str(dtd_url))
    else:
        logging.info("Succesfully to load dtd from" + str(dtd_url))
    return dtd


def prepare_comment_text(text: str) -> str:
    """
    Function to prepare comment text for xml

    :param text: comment to be converted to xml comment

    Returns:
        str: converted comment text

    """
    text = text.replace("--", "DOUBLEDASH")
    if text.endswith("-"):
        text = text[:-1] + "SINGLEDASH"
    return text
