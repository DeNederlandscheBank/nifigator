# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict, defaultdict, deque
from typing import Union, List, Optional

import regex as re
from iribaker import to_iri
from rdflib import Graph, Namespace
from rdflib.store import Store
from rdflib.term import IdentifiedNode, URIRef, Literal
from rdflib.plugins.stores import sparqlstore, memory
from rdflib.namespace import NamespaceManager
from .const import (
    RDF,
    XSD,
    NIF,
    NIFVEC,
)
from .utils import tokenizer
from .nifgraph import NifGraph

DEFAULT_URI = "https://mangosaurus.eu/rdf-data/"
DEFAULT_PREFIX = "mangosaurus"

MIN_PHRASE_COUNT = "min_phrase_count"
MIN_CONTEXT_COUNT = "min_context_count"
MIN_PHRASECONTEXT_COUNT = "min_phrasecontext_count"
MAX_PHRASE_LENGTH = "max_phrase_length"
MAX_LEFT_LENGTH = "max_left_length"
MAX_RIGHT_LENGTH = "max_right_length"
MIN_LEFT_LENGTH = "min_left_length"
MIN_RIGHT_LENGTH = "min_right_length"
CONTEXT_SEPARATOR = "context_separator"
PHRASE_SEPARATOR = "phrase_separator"
WORDS_FILTER = "words_filter"


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


class NifVectorGraph(Graph):
    """
    A NIF Vector graph

    :param nif_graph: the graph from which to construct the NIF Vector graph (optional)

    :param context_uris: the context uris of the contexts used with the nif_graph to construct the NIF Vector graph

    :param documents: the documents from which to construct the NIF Vector graph (optional)

    :param lexicon: the namespace of the lexicon (words and phrases in the text)

    :param window: the namespace of the windows (context-phrase combinations in the text)

    :param context: the namespace of the contexts

    :param params: dictionary with parameters for constructing the NIF Vector graph

    """

    def __init__(
        self,
        nif_graph: NifGraph = None,
        context_uris: list = None,
        documents: list = None,
        lexicon: Namespace = None,
        window: Namespace = None,
        context: Namespace = None,
        params: dict = {},
        store: Union[Store, str] = "default",
        identifier: Optional[Union[IdentifiedNode, str]] = None,
        namespace_manager: Optional[NamespaceManager] = None,
        base: Optional[str] = None,
        bind_namespaces: str = "core",
    ):
        super(NifVectorGraph, self).__init__(
            store=store,
            identifier=identifier,
            namespace_manager=namespace_manager,
            base=base,
            bind_namespaces=bind_namespaces,
        )
        self.params = params

        {
            "max_phrase_length": params.get(MAX_PHRASE_LENGTH, 4),
            "max_left_length": params.get(MAX_LEFT_LENGTH, 2),
            "max_right_length": params.get(MAX_RIGHT_LENGTH, 2),
            "min_left_length": params.get(MIN_LEFT_LENGTH, 1),
            "min_right_length": params.get(MIN_RIGHT_LENGTH, 1),
        }
        self.context_separator = params.get(CONTEXT_SEPARATOR, "_")
        self.phrase_separator = params.get(PHRASE_SEPARATOR, "+")

        words_filter = params.get(WORDS_FILTER, None)
        if words_filter is not None:
            self.words_filter = words_filter
            # reformulate to dict for efficiency
            self.words_filter["data"] = {
                phrase: True for phrase in words_filter["data"]
            }
        else:
            self.words_filter = None

        self.bind("nifvec", NIFVEC)
        self.bind("nif", NIF)

        if lexicon is None:
            self.lexicon_ns = Namespace(DEFAULT_URI + "lexicon/")
        self.bind("lexicon", self.lexicon_ns)
        if window is None:
            self.window_ns = Namespace(DEFAULT_URI + "window/")
        self.bind("window", self.window_ns)
        if context is None:
            self.context_ns = Namespace(DEFAULT_URI + "context/")
        self.bind("context", self.context_ns)

        if documents is None and nif_graph is not None:
            logging.info(".. Extracting text from graph")
            if context_uris is None or context_uris == []:
                context_uris = [
                    c[0] for c in list(nif_graph.triples([None, RDF.type, NIF.Context]))
                ]
            for context_uri in context_uris:
                documents = [
                    d[2]
                    for d in nif_graph.triples([context_uri, NIF.isString, None])
                    if len(d) > 0
                ]

        if documents is not None:
            logging.info(".. Creating windows dict")
            windows = self.generate_windows(documents=documents)
            logging.info(".. Creating phrase and context dicts")
            phrase_count, context_count = self.create_window_phrase_count_dicts(
                windows=windows
            )
            logging.info(".. Adding triples to graph")
            for triple in self.generate_triples(
                windows=windows, phrase_count=phrase_count, context_count=context_count
            ):
                self.add(triple)

    def generate_triples(
        self, windows: dict = {}, phrase_count: dict = {}, context_count: dict = {}
    ):
        """ """
        for phrase in phrase_count.keys():
            phrase_uri = URIRef(self.lexicon_ns + to_iri(phrase))
            yield ((phrase_uri, RDF.type, NIF.Phrase))
            yield (
                (
                    phrase_uri,
                    NIFVEC.hasCount,
                    Literal(phrase_count[phrase], datatype=XSD.nonNegativeInteger),
                )
            )
        for context in context_count.keys():
            context_uri = URIRef(
                self.context_ns
                + to_iri(context[0])
                + self.context_separator
                + to_iri(context[1])
            )
            yield ((context_uri, RDF.type, NIFVEC.Context))
            yield (
                (
                    context_uri,
                    NIFVEC.hasCount,
                    Literal(context_count[context], datatype=XSD.nonNegativeInteger),
                )
            )
        for phrase in windows.keys():
            for window in windows[phrase]:
                count = windows[phrase][window]
                p = to_iri(window[0])
                n = to_iri(window[1])
                phrase_uri = URIRef(self.lexicon_ns + to_iri(phrase))
                context_uri = URIRef(self.context_ns + p + self.context_separator + n)
                window_uri = URIRef(
                    self.window_ns
                    + p
                    + self.context_separator
                    + to_iri(phrase)
                    + self.context_separator
                    + n
                )
                yield ((phrase_uri, NIFVEC.isPhraseOf, window_uri))
                yield ((context_uri, NIFVEC.isContextOf, window_uri))
                yield ((window_uri, RDF.type, NIFVEC.Window))
                yield ((window_uri, NIFVEC.hasContext, context_uri))
                yield ((window_uri, NIFVEC.hasPhrase, phrase_uri))
                yield (
                    (
                        window_uri,
                        NIFVEC.hasCount,
                        Literal(count, datatype=XSD.nonNegativeInteger),
                    )
                )
                if self.words_filter is not None:
                    yield (
                        (
                            window_uri,
                            NIFVEC.hasFilter,
                            Literal(self.words_filter["name"], datatype=XSD.string),
                        )
                    )

    def create_window_phrase_count_dicts(self, windows: dict = {}):
        """ """
        min_phrasecontext_count = self.params.get("min_phrasecontext_count", 5)
        min_phrase_count = self.params.get("min_phrase_count", 5)
        min_context_count = self.params.get("min_context_count", 5)

        # delete phrasewindow with number of occurrence < MIN_PHRASECONTEXT_COUNT
        to_delete = []
        for d_phrase in windows.keys():
            for d_window in windows[d_phrase].keys():
                if windows[d_phrase][d_window] < min_phrasecontext_count:
                    to_delete.append((d_phrase, d_window))
        for item in to_delete:
            del windows[item[0]][item[1]]

        # create context_count and phrase_count
        context_count = defaultdict(int)
        phrase_count = defaultdict(int)
        for d_phrase in windows.keys():
            for d_window in windows[d_phrase].keys():
                c = windows[d_phrase][d_window]
                context_count[d_window] += c
                phrase_count[d_phrase] += c

        # delete phrases with number of occurrence < MIN_PHRASE_COUNT
        to_delete = [
            p for p in phrase_count.keys() if phrase_count[p] < min_phrase_count
        ]
        for item in to_delete:
            del phrase_count[item]

        # delete windows with number of occurrence < MIN_CONTEXT_COUNT
        to_delete = [
            c for c in context_count.keys() if context_count[c] < min_context_count
        ]
        for item in to_delete:
            del context_count[item]

        return phrase_count, context_count

    def generate_windows(self, documents: list = None):
        """ """
        windows = {}
        for document in documents:
            sentences = [
                [word["text"] for word in sentence] for sentence in tokenizer(document)
            ]
            for phrase, context in generate_phrase_context(
                sentences=sentences,
                words_filter=self.words_filter,
                phrase_separator=self.phrase_separator,
                params=self.params,
            ):
                if windows.get(phrase, None) is None:
                    windows[phrase] = defaultdict(int)
                windows[phrase][context] += 1
        return windows

    def phrase_contexts(self, phrase: str = "", topn: int = 15):
        """ """
        phrase_uri = (
            "<" + self.lexicon_ns + self.phrase_separator.join(phrase.split(" ")) + ">"
        )
        q = """
    SELECT DISTINCT ?c (sum(?count) as ?n)
    WHERE
    {\n"""
        if not isinstance(self.store, memory.Memory):
            q += "SERVICE <" + self.store.query_endpoint + "> "
        q += (
            """
        {
            """
            + phrase_uri
            + """ nifvec:isPhraseOf ?w .
            ?w nifvec:hasContext ?c .
            ?w nifvec:hasCount ?count .
        }
    }
    GROUP BY ?c
    ORDER BY DESC(?n)
    """
        )
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = {
            tuple(r[0].split("/")[-1].split(self.context_separator)): r[1].value
            for r in self.query(q)
        }
        return results

    def most_similar(self, phrase: str = "", topn: int = 15, topcontexts: int = 25):
        """ """
        phrase_uri = (
            "<" + self.lexicon_ns + self.phrase_separator.join(phrase.split(" ")) + ">"
        )
        q = """
    SELECT distinct ?word (count(?c) as ?num)
    WHERE
    {\n"""
        if not isinstance(self.store, memory.Memory):
            q += "SERVICE <" + self.store.query_endpoint + "> "
        q += (
            """
        {
            {
                SELECT DISTINCT ?c (sum(?count) as ?n)
                WHERE
                {
                    """
            + phrase_uri
            + """ nifvec:isPhraseOf ?w .
                    ?w nifvec:hasContext ?c .
                    ?w nifvec:hasCount ?count .
                }
                GROUP BY ?c
                ORDER BY DESC(?n)
                LIMIT """
            + str(topcontexts)
            + """
            }
            ?c nifvec:isContextOf ?w1 .
            ?word nifvec:isPhraseOf ?w1 .
        }
    }
    GROUP BY ?word
    ORDER BY DESC (?num)
    """
        )
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = [item for item in self.query(q)]
        norm = results[0][1].value
        results = {
            r[0].split("/")[-1].replace(self.phrase_separator, " "): 1
            - r[1].value / norm
            for r in results
        }
        return results

    def dict_phrases_contexts(
        g, word: str = None, topn: int = 7, topcontexts: int = 10
    ):
        """ """
        contexts = g.phrase_contexts(word, topn=topcontexts)
        phrases = g.most_similar(word, topn=topn)
        d = {
            "index": phrases.keys(),
            "columns": contexts.keys(),
            "data": [],
            "index_names": ["phrase"],
            "column_names": ["left context phrase", "right context phrase"],
        }
        for phrase in phrases:
            phrase_contexts = g.phrase_contexts(phrase, topn=None)
            d["data"].append([phrase_contexts.get(c, 0) for c in contexts.keys()])
        return d

    def context_phrases(self, context: list = None, topn: int = 15):
        """ """
        context = (
            self.phrase_separator.join(context[0].split(" ")),
            self.phrase_separator.join(context[1].split(" ")),
        )
        context_uri = "<" + self.context_ns + self.context_separator.join(context) + ">"
        q = """
    SELECT distinct ?phrase (sum(?s) as ?num)
    WHERE
    {\n"""
        if not isinstance(self.store, memory.Memory):
            q += "SERVICE <" + self.store.query_endpoint + "> "
        q += (
            """
        {
            """
            + context_uri
            + """ nifvec:isContextOf ?window .
            ?window nifvec:hasCount ?s .
            ?phrase nifvec:isPhraseOf ?window .
        }
    }
    GROUP BY ?phrase
    ORDER BY DESC(?num)
    """
        )
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = {
            r[0].split("/")[-1].replace(self.phrase_separator, " "): r[1].value
            for r in self.query(q)
        }
        return results


class NifVector(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)
        self = {
            k: v
            for k, v in sorted(self.items(), reverse=True, key=lambda item: item[1])
        }

    def __sub__(self, other):
        for item in other.keys():
            if item in self.keys():
                del self[item]
        self = NifVector(self)
        return self

    def __add__(self, other):
        d = NifVector()
        for item in self.keys():
            if item in other.keys():
                d[item] = other[item] + self[item]
        self = NifVector(d)
        return self

    def __and__(self, other):
        return self + other

    def __or__(self, other):
        for item in other.keys():
            if item in self.keys():
                self[item] += other[item]
            else:
                self[item] = other[item]
        self = NifVector(self)
        return self

    def topn(self, n: int = 5):
        return NifVector(list(self.items())[0:n])


def generate_phrase_context(
    sentences: list = None,
    words_filter: dict = None,
    phrase_separator: str = "+",
    params: dict = {},
):
    """ """
    max_phrase_length = params.get("max_phrase_length", 4)
    min_left_length = params.get("min_left_length", 1)
    max_left_length = params.get("max_left_length", 2)
    min_right_length = params.get("min_right_length", 1)
    max_right_length = params.get("max_right_length", 2)

    # delete stopwords in sentence if enabled
    for sentence in sentences:
        if words_filter is not None:
            sentence = [
                word
                for word in sentence
                if words_filter["data"].get(word, None) is None
            ]
        else:
            sentence = ["SENTSTART"] + sentence + ["SENTEND"]
        # perform regex selection of sentence
        sentence = [word for word in sentence if re.match("^[0-9]*[a-zA-Z]*$", word)]
        for idx, word in enumerate(sentence):
            for phrase_length in range(1, max_phrase_length + 1):
                for left_length in range(min_left_length, max_left_length + 1):
                    for right_length in range(min_right_length, max_right_length + 1):
                        if (
                            idx
                            >= max(
                                1 if sentence[0] == "SENTSTART" else 0,
                                left_length,
                            )
                            and idx
                            <= len(sentence)
                            - phrase_length
                            - max(
                                1 if sentence[-1] == "SENTEND" else 0,
                                right_length,
                            )
                            and not (left_length == 0 and right_length == 0)
                        ):
                            left_phrase = phrase_separator.join(
                                sentence[idx - left_length + i]
                                for i in range(0, left_length)
                            )
                            phrase = phrase_separator.join(
                                sentence[idx + i] for i in range(0, phrase_length)
                            )
                            right_phrase = phrase_separator.join(
                                sentence[idx + phrase_length + i]
                                for i in range(0, right_length)
                            )
                            context = (left_phrase, right_phrase)
                            yield (phrase, context)
