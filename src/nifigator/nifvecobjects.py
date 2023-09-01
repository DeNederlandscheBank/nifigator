# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict, defaultdict, deque, Counter
from typing import Union, List, Optional
from itertools import combinations, product

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
    DEFAULT_URI,
    DEFAULT_PREFIX,
    MIN_PHRASE_COUNT,
    MIN_CONTEXT_COUNT,
    MIN_PHRASECONTEXT_COUNT,
    MAX_PHRASE_LENGTH,
    MAX_LEFT_LENGTH,
    MAX_RIGHT_LENGTH,
    MIN_LEFT_LENGTH,
    MIN_RIGHT_LENGTH,
    CONTEXT_SEPARATOR,
    PHRASE_SEPARATOR,
    WORDS_FILTER,
    FORCED_SENTENCE_SPLIT_CHARACTERS,
    DEFAULT_CONTEXT_SEPARATOR,
    DEFAULT_PHRASE_SEPARATOR,
)
from .utils import tokenizer, tokenize_text, to_iri
from .nifgraph import NifGraph

class NifVectorGraph(NifGraph):
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
        nif_graph: NifGraph=None,
        context_uris: list=None,
        sentences: list=None,
        lexicon: Namespace=Namespace(DEFAULT_URI + "lexicon/"),
        window: Namespace=Namespace(DEFAULT_URI + "window/"),
        context: Namespace=Namespace(DEFAULT_URI + "context/"),
        params: dict={},
        store: Union[Store, str]="default",
        identifier: Optional[Union[IdentifiedNode, str]]=None,
        namespace_manager: Optional[NamespaceManager]=None,
        base: Optional[str]=None,
        bind_namespaces: str="core",
    ):
        super(NifVectorGraph, self).__init__(
            store=store,
            identifier=identifier,
            namespace_manager=namespace_manager,
            base=base,
            bind_namespaces=bind_namespaces,
        )
        self.params = params

        words_filter = params.get(WORDS_FILTER, None)
        if words_filter is not None:
            # reformulate to dict for efficiency
            self.params[WORDS_FILTER]["data"] = {
                phrase: True for phrase in words_filter["data"]
            }
        else:
            self.params[WORDS_FILTER] = None

        self.bind("lexicon", lexicon)
        self.bind("window", window)
        self.bind("context", context)
        self.bind("nifvec", NIFVEC)
        self.bind("nif", NIF)

        if nif_graph is not None:
            logging.info(".. Extracting text from graph")
            sentences = dict()
            contexts = nif_graph.contexts
            for context in contexts:
                if context_uris is None or context.uri in context_uris:
                    if context.sentences is not None:
                        for sent in context.sentences:
                            sentences[sent.uri] = sent.anchorOf
                    else:
                        logging.warning("No sentences found for "+str(context.uri))

        if sentences is not None:
            logging.info(".. Creating windows dict")
            windows = generate_windows(documents=sentences, params=self.params)
            logging.info(".. Creating phrase and context dicts")
            phrase_count, context_count = self.create_window_phrase_count_dicts(
                windows=windows
            )
            # window_relations = self.generate_window_relations(
            #     windows=windows,
            #     documents=sentences,
            # )
            window_relations = {}
            logging.info(".. Collecting triples")
            for triple in self.generate_triples(
                windows=windows,
                phrase_count=phrase_count,
                context_count=context_count,
                window_relations=window_relations,
            ):
                self.add(triple)
            logging.info(".. Finished initialization")

    def generate_triples(
        self, 
        windows: dict={}, 
        phrase_count: dict={}, 
        context_count: dict={},
        window_relations: dict=None,
    ):
        """ """
        context_sep = self.params.get(CONTEXT_SEPARATOR, DEFAULT_CONTEXT_SEPARATOR)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)
        ns = dict(self.namespaces())
        lexicon_ns = ns['lexicon']
        context_ns = ns['context']
        window_ns = ns['window']

        for left, right in window_relations.keys():

            left_phrase, left_context = left
            right_phrase, right_context = right

            left_phrase_text = to_iri(left_phrase)
            left_p = to_iri(left_context[0])
            left_n = to_iri(left_context[1])
            
            right_phrase_text = to_iri(right_phrase)
            right_p = to_iri(right_context[0])
            right_n = to_iri(right_context[1])

            left_window_text = (
                left_p
                + context_sep
                + left_phrase_text
                + context_sep
                + left_n
            )
            right_window_text = (
                right_p
                + context_sep
                + right_phrase_text
                + context_sep
                + right_n
            )
            left_window_uri = URIRef(window_ns+left_window_text)
            right_window_uri = URIRef(window_ns+right_window_text)
            relation_uri = URIRef(window_ns+left_window_text+context_sep+context_sep+right_window_text)
            count = Literal(window_relations[(left, right)], datatype=XSD.nonNegativeInteger)
            if left_window_text not in right_window_text and right_window_text not in left_window_text:
                yield ((relation_uri, RDF.type, NIF.WindowRelation))
                yield ((relation_uri, NIFVEC.hasWindow, left_window_uri))
                yield ((relation_uri, NIFVEC.hasWindow, right_window_uri))
                yield ((relation_uri, NIFVEC.hasCount, count))
                yield ((left_window_uri, NIFVEC.isWindowOf, relation_uri))
                yield ((right_window_uri, NIFVEC.isWindowOf, relation_uri))

        for phrase in phrase_count.keys():
            phrase_text = to_iri(phrase)
            phrase_value = Literal(phrase_text, datatype=XSD.string)
            phrase_uri = URIRef(lexicon_ns + phrase_text)
            count = Literal(phrase_count[phrase], datatype=XSD.nonNegativeInteger)
            yield ((phrase_uri, RDF.type, NIF.Phrase))
            yield ((phrase_uri, RDF.value, phrase_value))
            yield ((phrase_uri, NIFVEC.hasCount, count))
        for context in context_count.keys():
            context_text = (
                to_iri(context[0]) + context_sep + to_iri(context[1])
            )
            context_value = Literal(context_text, datatype=XSD.string)
            left_context_value = Literal(to_iri(context[0]), datatype=XSD.string)
            right_context_value = Literal(to_iri(context[1]), datatype=XSD.string)
            context_uri = URIRef(context_ns + context_text)
            count = Literal(context_count[context], datatype=XSD.nonNegativeInteger)
            yield ((context_uri, RDF.type, NIFVEC.Context))
            yield ((context_uri, NIFVEC.hasLeftValue, left_context_value))
            yield ((context_uri, NIFVEC.hasRightValue, right_context_value))
            yield ((context_uri, RDF.value, context_value))
            yield ((context_uri, NIFVEC.hasCount, count))
        for phrase in windows.keys():
            for window in windows[phrase]:
                p = to_iri(window[0])
                n = to_iri(window[1])
                phrase_text = to_iri(phrase)
                phrase_uri = URIRef(lexicon_ns + phrase_text)
                context_uri = URIRef(context_ns + p + context_sep + n)
                window_text = (
                    p
                    + context_sep
                    + phrase_text
                    + context_sep
                    + n
                )
                window_value = Literal(window_text, datatype=XSD.string)
                window_uri = URIRef(window_ns + window_text)
                window_count = Literal(
                    windows[phrase][window], datatype=XSD.nonNegativeInteger
                )
                yield ((phrase_uri, NIFVEC.isPhraseOf, window_uri))
                yield ((context_uri, NIFVEC.isContextOf, window_uri))
                yield ((window_uri, RDF.type, NIFVEC.Window))
                yield ((window_uri, RDF.value, window_value))
                yield ((window_uri, NIFVEC.hasContext, context_uri))
                yield ((window_uri, NIFVEC.hasPhrase, phrase_uri))
                yield ((window_uri, NIFVEC.hasCount, window_count))

    def create_window_phrase_count_dicts(self, windows: dict={}):
        """
        Function to prune and create phrase dict and contexts dict
        """
        min_phrasecontext_count = self.params.get("min_phrasecontext_count", 5)
        min_phrase_count = self.params.get("min_phrase_count", 5)
        min_context_count = self.params.get("min_context_count", 5)

        # delete phrasewindow with number of occurrence < MIN_PHRASECONTEXT_COUNT
        to_delete = []
        for d_phrase in windows.keys():
            for d_window in windows[d_phrase].keys():
                if windows[d_phrase][d_window] < min_phrasecontext_count:
                    to_delete.append((d_phrase, d_window))
        logging.info(
            ".... deleting "+str(len(to_delete))+
            " windows from "+str(len([d_window for d_phrase in windows.keys() for d_window in windows[d_phrase].keys()]))
        )
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
        logging.info(".... deleting "+str(len(to_delete))+" phrases from "+str(len(phrase_count.keys())))
        for item in to_delete:
            del phrase_count[item]

        # delete windows with number of occurrence < MIN_CONTEXT_COUNT
        to_delete = [
            c for c in context_count.keys() if context_count[c] < min_context_count
        ]
        logging.info(".... deleting "+str(len(to_delete))+" contexts from "+str(len(context_count.keys())))
        for item in to_delete:
            del context_count[item]

        return phrase_count, context_count

    def generate_window_relations(
        self, 
        documents: list=None,
        windows: dict={}):
        """
        """
        phrase_sep = self.params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)
        forced_sentence_split_characters = self.params.get(FORCED_SENTENCE_SPLIT_CHARACTERS, [])

        relations = defaultdict(int)
        for key, value in documents.items():
            tokenized_text = tokenize_text(value, forced_sentence_split_characters)
            sentences = [
                [word["text"] for word in sentence] for sentence in tokenized_text
            ]
            found = []
            for phrase, context, location in generate_phrase_context(
                sentences=sentences,
                words_filter=self.words_filter,
                phrase_separator=phrase_sep,
                params=self.params,
            ):
                if windows.get(phrase, {}).get(context, None) is not None:
                    found.append((phrase, context, location))

            for f1, f2 in combinations(found, 2):
                f1_start, f1_end = f1[2]
                f2_start, f2_end = f2[2]
                if set(range(f1_start, f1_end)) & set(range(f2_start, f2_end)) == set():
                    relations[tuple(sorted([(f1[0], f1[1]), (f2[0], f2[1])]))] += 1

        # delete windows with number of occurrence < MIN_WINDOW_RELATION_COUNT
        min_window_relation_count = self.params.get("min_window_relation_count", 2)
        to_delete = [
            c for c in relations.keys() if relations[c] < min_window_relation_count
        ]
        logging.info(".... deleting "+str(len(to_delete))+" window relations "+str(len(relations.keys())))
        for item in to_delete:
            del relations[item]

        return relations

    def phrase_contexts(self, 
                        phrase: str=None,
                        phrase_uri: URIRef=None,
                        left: str=None,
                        right: str=None,
                        topn: int=15):
        """
        Function that returns the contexts of a phrase

        :param phrase: the phrase from which to derive the contexts (as a string)

        :param phrase_uri: the phrase from which to derive the contexts (as a uri)

        :param left: the left side of the context (optional, as a string)

        :param right: the right side of the context (optional, as a string)

        :param topn: restrict output to topn (default = 15)

        """
        ns = dict(self.namespaces())
        lexicon_ns = ns['lexicon']

        context_sep = self.params.get(CONTEXT_SEPARATOR, DEFAULT_CONTEXT_SEPARATOR)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)

        if phrase_uri is None:
            phrase_uri = URIRef(lexicon_ns + phrase_sep.join(phrase.split(" ")))
            
        q = """
    SELECT DISTINCT ?v (sum(?count) as ?n)
    WHERE
    {\n"""
        q += (
            """
        {
            """
            + phrase_uri.n3()
            + """ nifvec:isPhraseOf ?w .
            ?w rdf:type nifvec:Window .
            ?w nifvec:hasContext ?c .
            ?w nifvec:hasCount ?count .
            ?c rdf:value ?v .
            """)
        if left is not None:
            q += '?c nifvec:hasLeftValue "'+Literal(left)+'" .\n'
        if right is not None:
            q += '?c nifvec:hasRightValue "'+Literal(right)+'" .\n'

        q += ("""
        }
    }
    GROUP BY ?v
    ORDER BY DESC(?n)
    """
        )
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = Counter({
            tuple(r[0].split(context_sep)): r[1].value
            for r in self.query(q)
        })
        return results

    def most_similar(self, 
                     phrase: str=None, 
                     phrase_uri: URIRef=None,
                     context: str=None, 
                     context_uri: URIRef=None,
                     topn: int=15, 
                     topcontexts: int=25,
                     topphrases: int=25):
        """
        Function that returns most similar phrases of a phrase

        :param phrase: the phrase from which to derive similar phrases (as a string)

        :param phrase_uri: the phrase from which to derive similar phrases (as a uri)

        :param context: the context to take into account for deriving similar phrases (as a string)

        :param context: the context to take into account for deriving similar phrases (as a uri)

        :param topn: restrict output to topn (default = 15)

        :param topcontexts: number of similar contexts to use 

        :param topphrases: number of similar phrases to use

        """
        ns = dict(self.namespaces())
        lexicon_ns = ns['lexicon']
        phrase_sep = self.params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)
        if phrase_uri is None:
            phrase_uri = URIRef(lexicon_ns + phrase_sep.join(phrase.split(" ")))
        if context_uri is None and context is not None:
            context_ns = ns['context']
            context_sep = self.params.get(CONTEXT_SEPARATOR, DEFAULT_CONTEXT_SEPARATOR)
            context_uri = URIRef(context_ns + context_sep.join(context))

        q = """
    SELECT distinct ?v (count(?c) as ?num1)
    WHERE
    {\n"""
        q += (
            """
        {
            {
                SELECT DISTINCT ?c (sum(?count1) as ?n1) 
                WHERE
                {
                    """+phrase_uri.n3()+""" 
                        nifvec:isPhraseOf ?w1 .
                    ?w1 rdf:type nifvec:Window .
                    ?w1 nifvec:hasContext ?c .
                    ?w1 nifvec:hasCount ?count1 .
                }
                GROUP BY ?c
                ORDER BY DESC(?n1)
                LIMIT """+str(topcontexts)+"""
            }
            """)
        if context_uri is not None:
            q += ("""
                {
                    SELECT DISTINCT ?p (sum(?count2) as ?n2)
                    WHERE
                    {
                        """+context_uri.n3()+""" 
                            nifvec:isContextOf ?w2 .
                        ?w2 rdf:type nifvec:Window .
                        ?w2 nifvec:hasPhrase ?p .
                        ?w2 nifvec:hasCount ?count2 .
                    }
                    GROUP BY ?p
                    ORDER BY DESC(?n2)
                    LIMIT """+str(topphrases)+"""
                }
                """)
        q += ("""
            ?p nifvec:isPhraseOf ?w .
            ?c nifvec:isContextOf ?w .
            ?w rdf:type nifvec:Window .
            ?p rdf:value ?v .
        }
    }
    GROUP BY ?v
    ORDER BY DESC (?num1)
    """)
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = [item for item in self.query(q)]
        if len(results) > 0:
            norm = results[0][1].value
            results = dict({
                r[0].replace(phrase_sep, " "): (r[1].value, norm)
                for r in results
            })
        else:
            results = dict()
        return results

    def extract_rdf_type(self, rdf_type: str=None, topn: int=None):
        """ """
        context_sep = self.params.get(CONTEXT_SEPARATOR, DEFAULT_CONTEXT_SEPARATOR)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)
        q = """
    SELECT distinct ?v (sum(?count) as ?num)
    WHERE
    {\n"""
        q += (
            """
        {
            ?w rdf:type """
            + rdf_type
            + """ .
            ?w nifvec:hasCount ?count .
            ?w rdf:value ?v .
        }
    }
    GROUP BY ?v
    ORDER BY DESC (?num)
        """
        )
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = [item for item in self.query(q)]
        if rdf_type == "nif:Phrase":
            results = {
                r[0].replace(phrase_sep, " "): r[1].value
                for r in results
            }
        elif rdf_type == "nifvec:Context":
            results = {
                r[0].replace(context_sep, " "): r[1].value
                for r in results
            }
        return results

    def phrases(self, topn: int=None):
        """
        Returns phrases in the graph
        """
        return self.extract_rdf_type(rdf_type="nif:Phrase", topn=topn)

    def windows(self, topn: int=None):
        """
        Returns windows in the graph
        """
        return self.extract_rdf_type(rdf_type="nifvec:Window", topn=topn)

    def dict_phrases_contexts(
        g, 
        word: str=None, 
        topn: int=7, 
        topcontexts: int=10
    ):
        """ """
        contexts = g.phrase_contexts(word, topn=topcontexts)
        phrases = g.most_similar(word, topn=topn, topcontexts=topcontexts)
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

    def context_phrases(self, context: tuple = None, topn: int = 15):
        """
        Function that returns the phrases of a context

        """
        ns = dict(self.namespaces())
        context_ns = ns['context']

        context_sep = self.params.get(CONTEXT_SEPARATOR, DEFAULT_CONTEXT_SEPARATOR)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)
        context = (
            phrase_sep.join(context[0].split(" ")),
            phrase_sep.join(context[1].split(" ")),
        )
        context_uri = URIRef(context_ns + context_sep.join(context)).n3()
        q = """
    SELECT distinct ?v (sum(?s) as ?num)
    WHERE
    {\n"""
        q += (
            """
        {
            """
            + context_uri
            + """ nifvec:isContextOf ?window .
            ?window rdf:type nifvec:Window .
            ?window nifvec:hasCount ?s .
            ?phrase nifvec:isPhraseOf ?window .
            ?phrase rdf:value ?v .
        }
    }
    GROUP BY ?v
    ORDER BY DESC(?num)
    """
        )
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = Counter({
            r[0].replace(phrase_sep, " "): r[1].value
            for r in self.query(q)
        })
        return results

def generate_windows(documents: dict=None, params: dict={}):
    """
    """
    windows = dict()

    for key, document in documents.items():
        for phrase, context, _ in generate_phrase_context(
            document=document,
            params=params,
        ):
            if windows.get(phrase, None) is None:
                windows[phrase] = Counter()
            windows[phrase][context] += 1

    return windows

def generate_phrase_context(
    document: str=None,
    params: dict={},
):
    """
    """
    phrase_sep = params.get(PHRASE_SEPARATOR, DEFAULT_PHRASE_SEPARATOR)
    words_filter = params.get(WORDS_FILTER, None)
    forced_sentence_split_characters = params.get(FORCED_SENTENCE_SPLIT_CHARACTERS, [])

    max_phrase_length = params.get("max_phrase_length", 5)
    min_left_length = params.get("min_left_length", 1)
    max_left_length = params.get("max_left_length", 3)
    min_right_length = params.get("min_right_length", 1)
    max_right_length = params.get("max_right_length", 3)

    tokenized_text = tokenize_text(document, forced_sentence_split_characters)
    sentences = [
        [word["text"] for word in sentence] for sentence in tokenized_text
    ]

    # delete stopwords in sentence if enabled
    for sentence in sentences:
        sentence = ["SENTSTART"] + sentence + ["SENTEND"]
        # perform regex selection of sentence
        windows = {}
        sentence = [word for word in sentence if re.match("^[0-9]*[a-zA-Z]*$", word)]
        for idx, word in enumerate(sentence):
            for phrase_length, left_length, right_length in product(
                range(1, max_phrase_length+1),
                range(min_left_length, max_left_length+1),
                range(min_right_length, max_right_length+1)
            ):
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
                    phrase_list = [sentence[idx + i] for i in range(0, phrase_length)]
                    phrase = phrase_sep.join(
                        word for word in phrase_list
                    )
                    left_context_list = [sentence[idx - left_length + i] for i in range(0, left_length)]
                    left_context = phrase_sep.join(
                        word for word in left_context_list
                    )
                    right_context_list = [sentence[idx + phrase_length + i] for i in range(0, right_length)]
                    right_context = phrase_sep.join(
                        word for word in right_context_list
                    )
                    context = (left_context, right_context)
                    if context != ("SENTSTART", "SENTEND"):
                        if words_filter is None:
                            yield (phrase, context, (idx - left_length, idx + phrase_length + right_length))
                        else:
                            phrase_stop_words = [
                                words_filter["data"].get(word.lower(), False) for word in phrase_list
                            ]
                            left_phrase_stop_words = [
                                words_filter["data"].get(word.lower(), False) for word in left_context_list
                            ]
                            right_phrase_stop_words = [
                                words_filter["data"].get(word.lower(), False) for word in right_context_list
                            ]
                            if (
                                (not any(phrase_stop_words)) #and
                                # (not all(left_phrase_stop_words)) and 
                                # (not all(right_phrase_stop_words))
                            ):
                                yield (
                                    phrase, context, 
                                    (idx - left_length, idx + phrase_length + right_length)
                                )
