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
    STOPWORDS,
    RDF,
    XSD,
    NIF,
    NIFVEC,
    ONTOLEX,
    LEXINFO,
    DECOMP,
    DEFAULT_URI,
    DEFAULT_PREFIX,
    MIN_PHRASE_COUNT,
    MIN_CONTEXT_COUNT,
    MIN_PHRASECONTEXT_COUNT,
    MAX_PHRASE_LENGTH,
    MAX_CONTEXT_LENGTH,
    TRIPLE_BATCH_SIZE,
    CONTEXT_SEPARATOR,
    PHRASE_SEPARATOR,
    WORDS_FILTER,
    FORCED_SENTENCE_SPLIT_CHARACTERS,
    REGEX_FILTER,
)
from .utils import tokenizer, tokenize_text, to_iri
from .nifgraph import NifGraph
from .multisets import merge_multiset

default_min_phrase_count = 2
default_min_phrasecontext_count = 2
default_min_context_count = 2
default_max_context_length = 5
default_max_phrase_length = 5
default_context_separator = "_"
default_phrase_separator = "+"
default_regex_filter = None  # "^[0-9]*[a-zA-Z]*$"


class NifVectorGraph(NifGraph):
    """
    A NIF Vector graph

    :param nif_graph (NifGraph): the graph from which to construct the NIF Vector graph (optional)

    :param context_uris (list): the context uris of the contexts used with the nif_graph to construct the NIF Vector graph (optional)

    :param documents (list): the documents from which to construct the NIF Vector graph (optional)

    :param base_uri (Namespace): the namespace of the nifvec data

    :param lang (str): the language of the nifvec data

    :param params (dict): parameters for constructing the NIF Vector graph

    """

    def __init__(
        self,
        nif_graph: NifGraph = None,
        context_uris: list = None,
        documents: list = None,
        base_uri: Namespace = Namespace(DEFAULT_URI + "nifvec-data/"),
        lang: str = None,
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

        words_filter = params.get(WORDS_FILTER, None)
        if words_filter is not None:
            # reformulate to dict for efficiency
            self.params[WORDS_FILTER]["data"] = {
                phrase: True for phrase in words_filter["data"]
            }
        else:
            self.params[WORDS_FILTER] = None

        self.base_uri = base_uri
        self.lang = lang
        self.bind("nifvec-data", base_uri)
        self.bind("nifvec", NIFVEC)
        self.bind("nif", NIF)
        self.bind("ontolex", ONTOLEX)
        self.bind("lexinfo", LEXINFO)
        self.bind("decomp", DECOMP)

        if nif_graph is not None:
            # if nif_graph is available then contexts are extracted from this graph
            logging.debug(".. extracting documents from graph")
            documents = dict()
            contexts = nif_graph.contexts
            for context in contexts:
                # if context_uris is None then all contexts are extracted
                # otherwise only those in the context_uris list
                if context_uris is None or context.uri in context_uris:
                    isString = context.isString
                    if isString is not None:
                        documents[context.uri] = preprocess(isString, self.params)
                    else:
                        logging.warning("No isString found for " + str(context.uri))

        if documents is not None:
            phrases = generate_document_phrases(documents=documents, params=self.params)
            contexts, phrases = generate_document_contexts(
                init_phrases=phrases, documents=documents, params=self.params
            )
            self.store_triples(
                phrases=phrases,
                contexts=contexts,
            )

    def store_triples(
        self,
        phrases: dict = {},
        contexts: dict = {},
    ):
        """
        Function to store the triples from a document set into the NifVector graph.

        The triples are loaded in batches into the NifVector graph, to prevent the number of SPARQL updates.

        :param phrases: dictionary of all phrases to be stored

        :param contexts: dictionary of all contexts to be stored

        """
        triple_batch_size = self.params.get(TRIPLE_BATCH_SIZE, 5e6)
        count = 1
        temp_g = Graph()
        for triple in self.generate_triples(phrases=phrases, contexts=contexts):
            temp_g.add(triple)
            if count == triple_batch_size:
                self += temp_g
                count = 1
                temp_g = Graph()
            else:
                count += 1
        self += temp_g
        logging.debug(".. finished storing triples")

    def generate_triples(
        self,
        phrases: dict = {},
        contexts: dict = {},
    ):
        """
        Function to create all triples of a set of documents

        :param phrases: dictionary of all phrases to be stored

        :param contexts: dictionary of all contexts to be stored

        """

        logging.debug(".. collecting triples")

        context_sep = self.params.get(CONTEXT_SEPARATOR, default_context_separator)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, default_phrase_separator)

        # to add: nifvec graph definition, which contexts? which language, stopwords

        for phrase, value in phrases.items():
            phrase_uri = URIRef(self.base_uri + to_iri(phrase))
            phrase_value = Literal(phrase.replace(phrase_sep, " "), datatype=XSD.string)
            count = Literal(value, datatype=XSD.nonNegativeInteger)
            yield ((phrase_uri, RDF.type, NIF.Phrase))
            yield ((phrase_uri, RDF.value, phrase_value))
            yield ((phrase_uri, NIFVEC.hasCount, count))
        logging.debug(".... finished triples for phrases")

        for ((left_part, right_part)), value in contexts.items():
            context_uri = URIRef(
                self.base_uri + to_iri(left_part) + context_sep + to_iri(right_part)
            )
            left_context_value = Literal(
                left_part.replace(phrase_sep, " "), datatype=XSD.string
            )
            right_context_value = Literal(
                right_part.replace(phrase_sep, " "), datatype=XSD.string
            )
            context_count = Literal(
                sum(v for v in value.values()), datatype=XSD.nonNegativeInteger
            )
            yield ((context_uri, RDF.type, NIFVEC.Context))
            yield ((context_uri, NIFVEC.hasLeftValue, left_context_value))
            yield ((context_uri, NIFVEC.hasRightValue, right_context_value))
            yield ((context_uri, NIFVEC.hasCount, context_count))
        logging.debug(".... finished triples for contexts")

        for ((left_part, right_part)), value in contexts.items():
            context_uri = URIRef(
                self.base_uri + to_iri(left_part) + context_sep + to_iri(right_part)
            )
            for phrase, phrase_value in value.items():
                window_uri = URIRef(
                    self.base_uri
                    + to_iri(left_part)
                    + context_sep
                    + to_iri(phrase)
                    + context_sep
                    + to_iri(right_part)
                )
                phrase_uri = URIRef(self.base_uri + to_iri(phrase))
                window_count = Literal(phrase_value, datatype=XSD.nonNegativeInteger)
                yield ((window_uri, RDF.type, NIFVEC.Window))
                yield ((window_uri, NIFVEC.hasContext, context_uri))
                yield ((window_uri, NIFVEC.hasPhrase, phrase_uri))
                yield ((window_uri, NIFVEC.hasCount, window_count))
                yield ((phrase_uri, NIFVEC.isPhraseOf, window_uri))
                yield ((context_uri, NIFVEC.isContextOf, window_uri))
        logging.debug(".... finished triples for windows")

    def phrase_contexts(
        self,
        phrase: str = None,
        phrase_uri: URIRef = None,
        left: str = None,
        right: str = None,
        topn: int = 15,
    ):
        """
        Function that returns the contexts of a phrase

        :param phrase: the phrase from which to derive the contexts (as a string)

        :param phrase_uri: the phrase from which to derive the contexts (as a uri)

        :param left: the left side of the context (optional, as a string)

        :param right: the right side of the context (optional, as a string)

        :param topn: restrict output to topn (default = 15)

        """
        context_sep = self.params.get(CONTEXT_SEPARATOR, default_context_separator)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, default_phrase_separator)

        if phrase_uri is None:
            phrase_uri = URIRef(self.base_uri + phrase_sep.join(phrase.split(" ")))

        q = """
    SELECT DISTINCT ?value_left ?value_right (sum(?count) as ?n)
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
            """
        )
        if left is not None:
            q += '?c nifvec:hasLeftValue "' + Literal(left) + '" .\n'
        q += "?c nifvec:hasLeftValue ?value_left .\n"
        if right is not None:
            q += '?c nifvec:hasRightValue "' + Literal(right) + '" .\n'
        q += "?c nifvec:hasRightValue ?value_right .\n"
        q += """
        }
    }
    GROUP BY ?value_left ?value_right
    ORDER BY DESC(?n)
    """
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = Counter(
            {tuple([r[0].value, r[1].value]): r[2].value for r in self.query(q)}
        )
        return results

    def most_similar(
        self,
        phrase: str = None,
        phrase_uri: URIRef = None,
        context: str = None,
        context_uri: URIRef = None,
        contexts: list = None,
        contexts_uris: list = None,
        topn: int = 15,
        topcontexts: int = 25,
        topphrases: int = 25,
    ):
        """
        Function that returns most similar phrases of a phrase

        :param phrase: the phrase from which to derive similar phrases (as a string)

        :param phrase_uri: the phrase from which to derive similar phrases (as a uri)

        :param context: the context to take into account for deriving similar phrases (as a string)

        :param context_uri: the context to take into account for deriving similar phrases (as a uri)

        :param contexts: use list of contexts to filter

        :param contexts_uris: filter contexts

        :param topn: restrict output to topn (default = 15)

        :param topcontexts: number of similar contexts to use when using phrase or phrase_uri

        :param topphrases: number of similar phrases to use when using context or context_uri

        """
        phrase_sep = self.params.get(PHRASE_SEPARATOR, default_phrase_separator)
        context_sep = self.params.get(CONTEXT_SEPARATOR, default_context_separator)
        if phrase is not None:
            phrase_uri = URIRef(self.base_uri + phrase_sep.join(phrase.split(" ")))
        if context is not None:
            context_uri = URIRef(
                self.base_uri
                + context_sep.join([c.replace(" ", phrase_sep) for c in context])
            )
        if contexts is not None:
            contexts_uris = [
                URIRef(
                    self.base_uri
                    + context_sep.join([c.replace(" ", phrase_sep) for c in context])
                )
                for context in contexts
            ]

        q = """
    SELECT distinct ?v (count(?c) as ?num1)
    WHERE
    {\n"""
        q += """
        {"""
        if phrase_uri is not None:
            q += (
                """
            {
                SELECT DISTINCT ?c (sum(?count1) as ?n1) 
                WHERE
                {
                    """
                + phrase_uri.n3()
                + """ 
                        nifvec:isPhraseOf ?w1 .
                    ?w1 rdf:type nifvec:Window .
                    ?w1 nifvec:hasContext ?c .
                    ?w1 nifvec:hasCount ?count1 .
                }
                GROUP BY ?c
                ORDER BY DESC(?n1)
                LIMIT """
                + str(topcontexts)
                + """
            }
            """
            )
        if context_uri is not None:
            q += (
                """
                {
                    SELECT DISTINCT ?p (sum(?count2) as ?n2)
                    WHERE
                    {
                        """
                + context_uri.n3()
                + """ 
                            nifvec:isContextOf ?w2 .
                        ?w2 rdf:type nifvec:Window .
                        ?w2 nifvec:hasPhrase ?p .
                        ?w2 nifvec:hasCount ?count2 .
                    }
                    GROUP BY ?p
                    ORDER BY DESC(?n2)
                    LIMIT """
                + str(topphrases)
                + """
                }
                """
            )
        q += """
            ?p nifvec:isPhraseOf ?w .
            ?c nifvec:isContextOf ?w .
            ?w rdf:type nifvec:Window .
            ?p rdf:value ?v ."""

        if contexts_uris is not None:
            q += "FILTER (?c IN ("
            for contexts_uri in contexts_uris:
                q += contexts_uri.n3()
                if contexts_uri != contexts_uris[-1]:
                    q += ", "
            q += "))"
        q += """
        }
    }
    GROUP BY ?v
    ORDER BY DESC (?num1)
    """
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = [item for item in self.query(q)]
        if len(results) > 0:
            norm = results[0][1].value
            results = dict({r[0].value: (r[1].value, norm) for r in results})
        else:
            results = dict()
        return results

    def extract_rdf_type(self, rdf_type: str = None, topn: int = None):
        """ """
        context_sep = self.params.get(CONTEXT_SEPARATOR, default_context_separator)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, default_phrase_separator)
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
            results = {r[0].replace(phrase_sep, " "): r[1].value for r in results}
        elif rdf_type == "nifvec:Context":
            results = {r[0].replace(context_sep, " "): r[1].value for r in results}
        return results

    def phrases(self, topn: int = None):
        """
        Returns phrases with their counts in the graph
        """
        q = """
    SELECT distinct ?v (sum(?count) as ?num)
    WHERE
    {\n"""
        q += """
        {
            ?w rdf:type nif:Phrase .
            ?w nifvec:hasCount ?count .
            ?w rdf:value ?v .
        }
    }
    GROUP BY ?v
    ORDER BY DESC (?num)
        """
        if topn is not None:
            q += "LIMIT " + str(topn) + "\n"
        results = Counter({r[0].value: r[1].value for r in self.query(q)})
        return results

    def dict_phrases_contexts(
        g, word: str = None, topn: int = 7, topcontexts: int = 10
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

    def context_phrases(self,
        context: tuple = None,
        left: str = None,
        right: str = None,
        topn: int = 15
        ):
        """
        Function that returns the phrases of a context

        """
        context_sep = self.params.get(CONTEXT_SEPARATOR, default_context_separator)
        phrase_sep = self.params.get(PHRASE_SEPARATOR, default_phrase_separator)
        if context is not None:
            context = (
                phrase_sep.join(context[0].split(" ")),
                phrase_sep.join(context[1].split(" ")),
            )
            context_uri = URIRef(self.base_uri + context_sep.join(context)).n3()
        q = """
    SELECT distinct ?v (sum(?s) as ?num)
    WHERE
    {\n"""
        q += (
            """
        {""")
        if context is not None:
            q += context_uri + ' nifvec:isContextOf ?window .'
        if left is not None:
            q += '?context nifvec:hasLeftValue "'+Literal(left)+'" . '
        if right is not None:
            q += '?context nifvec:hasRightValue "'+Literal(right)+'" . '
        q += ("""
            ?context nifvec:isContextOf ?window .
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
        results = Counter({r[0].value: r[1].value for r in self.query(q)})
        return results

    def compact(self):
        """
        This function compacts the NifVector graph by replacing all hasCount triples by one sum hasCount triple
        """
        logging.info("Compacting")
        logging.info(".. stage 1 / 3")
        self.update(
            """
        INSERT { ?s nifvec:hasTotalCount ?tc }
        WHERE {
            {
                SELECT ?s (sum(?c) as ?tc)
                WHERE {
                    ?s nifvec:hasCount ?c 
                }
                GROUP BY ?s
            }
        }
        """
        )
        logging.info(".. stage 2 / 3")
        self.update(
            """
        DELETE { ?s nifvec:hasCount ?c }
        WHERE { ?s nifvec:hasCount ?c }
        """
        )
        logging.info(".. stage 3 / 3")
        self.update(
            """
        DELETE { ?s nifvec:hasTotalCount ?c }
        INSERT { ?s nifvec:hasCount ?c }
        WHERE { ?s nifvec:hasTotalCount ?c }
        """
        )
        logging.info(".. finished")
        return None

    def find_otherForms(
        self,
        phrase: str = None,
        phrase_uri: URIRef = None,
    ):
        """ """
        phrase_sep = self.params.get(PHRASE_SEPARATOR, default_phrase_separator)
        if phrase_uri is None:
            phrase_uri = URIRef(self.base_uri + phrase_sep.join(phrase.split(" ")))

        q = (
            """
        SELECT distinct ?f (sum(?c) as ?num1)
        WHERE
        {
            """
            + phrase_uri.n3()
            + """ rdf:value ?v . 
            {
                ?e ontolex:canonicalForm [ ontolex:writtenRep ?v ] .
            }
            UNION
            {
                ?e ontolex:otherForm [ ontolex:writtenRep ?v ] .
            }
            ?e ontolex:otherForm|ontolex:canonicalForm [ ontolex:writtenRep ?f ] .
            ?p rdf:value ?f .
            ?p nifvec:hasCount ?c .
            ?p rdf:type nif:Phrase .
        }
        GROUP BY ?f
        ORDER BY ?num1
        """
        )
        results = [item for item in self.query(q)]
        if len(results) > 0:
            results = dict({r[0].value: r[1].value for r in results})
        else:
            results = dict()
        return results

    # setup a dictionary with phrases and their contexts to speed up
    def load_vectors(
        self,
        documents: dict = None,
        vectors: dict = None,
        topn: int = 15,
        includePhraseVectors: bool = True,
        includeContextVectors: bool = False,
        includeOtherForms: bool = False,
    ):
        """
        Function to retrieve the vectors of phrases and context of a set of documents

        """
        if vectors is None:
            vectors = dict()
        params = {
            WORDS_FILTER: {"data": {phrase: True for phrase in STOPWORDS}},
            MIN_PHRASE_COUNT: 1,
        }

        documents = {
            key: preprocess(value, self.params) for key, value in documents.items()
        }

        phrases = generate_document_phrases(documents=documents, params=params)
        for phrase in phrases.keys():
            if includePhraseVectors:
                if vectors.get(phrase, None) is None:
                    if includeOtherForms:
                        vector = Counter()
                        for form in self.find_otherForms(phrase):
                            vector += self.phrase_contexts(form, topn=topn)
                    else:
                        vector = self.phrase_contexts(phrase, topn=topn)
                    vectors[phrase] = vector
            if includeContextVectors:
                if vectors.get(context, None) is None:
                    vectors[context] = self.context_phrases(context, topn=topn)
        return vectors


def document_vector(
    documents: dict = None,
    vectors: dict = None,
    includePhraseVectors: bool = True,
    includeContextVectors: bool = False,
    topn: int = 15,
    merge_dict: bool = False,
    params: dict = None,
):
    """
    extract the phrases of a string and create dict of phrases with their contexts
    """
    params = {
        WORDS_FILTER: {"data": {phrase: True for phrase in STOPWORDS}},
        MIN_PHRASE_COUNT: 1,
        MIN_CONTEXT_COUNT: 1,
        MIN_PHRASECONTEXT_COUNT: 1,
    }
    phrase_sep = params.get(PHRASE_SEPARATOR, default_phrase_separator)
    documents = {key: preprocess(value, params) for key, value in documents.items()}
    phrases = generate_document_phrases(
        documents=documents, 
        params=params
    )
    if includeContextVectors:
        contexts, phrases = generate_document_contexts(
            documents=documents, 
            init_phrases=phrases, 
            params=params
        )
    res = dict()
    if includePhraseVectors:
        for phrase in phrases.keys():
            p = phrase.replace(phrase_sep, " ")
            if p not in vectors.keys():
                logging.debug("Phrase " + repr(p) + " not found in vectors.")
            else:
                res[p] = Counter({key:value for key, value in vectors.get(p, Counter()).most_common(topn)})
    if includeContextVectors:
        for ((left, right)) in contexts.keys():        
            c = (left.replace(phrase_sep, " "), right.replace(phrase_sep, " "))
            if c not in vectors.keys():
                logging.debug("Context " + repr(c) + " not found in vectors.")
            else:
                res[c] = Counter({key:value for key, value in vectors.get(c, Counter()).most_common(topn)})
    if merge_dict:
        res = merge_multiset(res)
    return res


def generate_document_contexts(
    init_phrases: dict = None, documents: dict = None, params: dict = {}
):
    """ """

    logging.debug(".. generate document contexts started")

    max_context_length = params.get(MAX_CONTEXT_LENGTH, default_max_context_length)
    min_context_count = params.get(MIN_CONTEXT_COUNT, default_min_context_count)
    min_phrasecontext_count = params.get(
        MIN_PHRASECONTEXT_COUNT, default_min_phrasecontext_count
    )
    phrase_sep = params.get(PHRASE_SEPARATOR, default_phrase_separator)

    init_contexts = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    for phrase, docs in init_phrases.items():
        for doc, locs in docs.items():
            for sent_idx, begin_idx, end_idx in locs:
                sent = documents[doc][sent_idx]
                if begin_idx - 1 >= 0 and end_idx + 1 <= len(sent):
                    l = sent[begin_idx - 1]
                    r = sent[end_idx]
                    init_contexts[(l, r)][phrase][doc].add(
                        (sent_idx, begin_idx, end_idx)
                    )
    del init_phrases

    to_process_contexts = dict()
    for d_context, d_phrases in init_contexts.items():
        if len(d_phrases.keys()) > 1:
            to_process_contexts[d_context] = (d_phrases, 1, 1)

    # aggegrate results into contexts dict
    final_contexts = defaultdict(Counter)
    for d_context, d_phrases in init_contexts.items():
        d_phrase_counter = Counter(
            {
                d_phrase: sum(len(loc) for loc in docs.values())
                for d_phrase, docs in d_phrases.items()
                if sum(len(loc) for loc in docs.values()) >= min_phrasecontext_count
            }
        )
        if (
            len(d_phrase_counter.keys()) > 0
            and sum(v for v in d_phrase_counter.values()) >= min_context_count
        ):
            final_contexts[d_context] = d_phrase_counter
        else:
            if d_context in to_process_contexts.keys():
                del to_process_contexts[d_context]

    del init_contexts

    logging.debug(".... added contexts: " + str(len(to_process_contexts)))

    while to_process_contexts != dict():
        new_contexts = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        for d_context, (
            (d_phrases, left_size, right_size)
        ) in to_process_contexts.items():
            # print("evaluating "+str(d_context) + ": "+str(left_size)+", "+str(right_size))
            for phrase, docs in d_phrases.items():
                for doc, locs in docs.items():
                    for sent_idx, begin_idx, end_idx in locs:
                        sent = documents[doc][sent_idx]
                        if d_context == (
                            phrase_sep.join(sent[begin_idx - left_size : begin_idx]),
                            phrase_sep.join(sent[end_idx : end_idx + right_size]),
                        ):
                            # right
                            if (
                                begin_idx - left_size >= 0
                                and end_idx + right_size + 1 <= len(sent)
                            ):
                                l = phrase_sep.join(
                                    sent[begin_idx - left_size : begin_idx]
                                )
                                r = phrase_sep.join(
                                    sent[end_idx : end_idx + right_size + 1]
                                )
                                # print(".. (right) adding " +str((l, r)))
                                new_contexts[(l, r)][phrase][doc].add(
                                    (sent_idx, begin_idx, end_idx)
                                )
                            # left
                            if (
                                begin_idx - left_size - 1 >= 0
                                and end_idx + right_size <= len(sent)
                            ):
                                l = phrase_sep.join(
                                    sent[begin_idx - left_size - 1 : begin_idx]
                                )
                                r = phrase_sep.join(
                                    sent[end_idx : end_idx + right_size]
                                )
                                # print(".. (left) adding " +str((l, r)))
                                new_contexts[(l, r)][phrase][doc].add(
                                    (sent_idx, begin_idx, end_idx)
                                )

        # determine contexts for further processing
        to_process_contexts = dict()
        for ((left_part, right_part)), d_phrases in new_contexts.items():
            if (
                len(d_phrases.keys()) > 1
                and len(left_part.split(phrase_sep)) < max_context_length
                and len(right_part.split(phrase_sep)) < max_context_length
            ):
                to_process_contexts[(left_part, right_part)] = (
                    d_phrases,
                    len(left_part.split(phrase_sep)),
                    len(right_part.split(phrase_sep)),
                )

        # add new contexts to contexts
        for d_context, d_phrases in new_contexts.items():
            d_phrase_counter = Counter(
                {
                    d_phrase: sum(len(loc) for loc in docs.values())
                    for d_phrase, docs in d_phrases.items()
                    if sum(len(loc) for loc in docs.values()) >= min_phrasecontext_count
                }
            )
            if (
                len(d_phrase_counter.keys()) > 0
                and sum(v for v in d_phrase_counter.values()) >= min_context_count
            ):
                final_contexts[d_context] = d_phrase_counter
            else:
                if d_context in to_process_contexts.keys():
                    del to_process_contexts[d_context]

        logging.debug(".... added contexts: " + str(len(to_process_contexts)))

    # create final phrases dict from contexts
    phrases = Counter()
    for d_context, d_phrases in final_contexts.items():
        for phrase, value in d_phrases.items():
            phrases[phrase] += value

    logging.debug(".. generate document contexts finished")
    logging.debug(".... total contexts: " + str(len(final_contexts.keys())))
    logging.debug(".... total phrases: " + str(len(phrases.keys())))

    return final_contexts, phrases


def generate_document_phrases(documents: dict = None, params: dict = {}):
    """
    This function generates all phrases in the documents

    :param documents: a dict with context.uri as keys and context.isString as values

    :param params: a dict with parameters

    """
    logging.debug(".. generating document phrases")

    min_phrase_count = params.get(MIN_PHRASE_COUNT, default_min_phrase_count)

    # create a dict for each phrase that contain the phrase locations
    phrases = defaultdict(lambda: defaultdict(set))
    for context_uri, context_isString in documents.items():
        for phrase, loc in generate_sentence_phrases(context_isString, params=params):
            phrases[phrase][context_uri].add(loc)

    # delete all phrases that occur less than then the min_phrase_count
    to_delete = set()
    for phrase, docs in phrases.items():
        if sum(len(loc) for loc in docs.values()) < min_phrase_count:
            to_delete.add(phrase)
    for phrase in to_delete:
        del phrases[phrase]

    logging.debug(".... found phrases: " + str(len(phrases.keys())))

    return phrases


def generate_sentence_phrases(
    sentences: list = None,
    params: dict = {},
):
    """
    Generator for all phrases and their location in the sentences
    """
    phrase_sep = params.get(PHRASE_SEPARATOR, default_phrase_separator)
    words_filter = params.get(WORDS_FILTER, None)
    max_phrase_length = params.get(MAX_PHRASE_LENGTH, default_max_phrase_length)
    for sent_idx, sentence in enumerate(sentences):
        for word_idx, word in enumerate(sentence):
            for phrase_length in range(1, max_phrase_length + 1):
                if word_idx + phrase_length <= len(sentence):
                    phrase_list = [
                        sentence[word_idx + i] for i in range(0, phrase_length)
                    ]
                    phrase = phrase_sep.join(word for word in phrase_list)
                    if words_filter is None:
                        yield (
                            phrase,
                            (sent_idx, word_idx, word_idx + phrase_length),
                        )
                    else:
                        # phrases may not start or end with one of the stopwords
                        phrase_stop_words = [
                            words_filter["data"].get(word.lower(), False)
                            for word in [phrase_list[0], phrase_list[-1]]
                        ]
                        if not any(phrase_stop_words):
                            yield (
                                phrase,
                                (sent_idx, word_idx, word_idx + phrase_length),
                            )


def preprocess(
    document: str = None,
    params: dict = {},
):
    """ """
    split_characters = params.get(FORCED_SENTENCE_SPLIT_CHARACTERS, [])
    regex_filter = params.get(REGEX_FILTER, default_regex_filter)
    # tokenize documents into sentences
    sentences = [
        [word["text"] for word in sentence]
        for sentence in tokenize_text(document, split_characters)
    ]
    if regex_filter is not None:
        # select tokens given a regex filter and add start and end of sentence tokens SENTSTART and SENTEND
        preprocessed = [
            ["SENTSTART"]
            + [word for word in sentence if re.match(regex_filter, word)]
            + ["SENTEND"]
            for sentence in sentences
        ]
    else:
        preprocessed = [
            ["SENTSTART"] + sentence + ["SENTEND"] for sentence in sentences
        ]
    return preprocessed
