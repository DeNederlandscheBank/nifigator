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
    NIF2VEC,
)
from .utils import (
    tokenizer
)
from .nifgraph import NifGraph

DEFAULT_URI = "https://mangosaurus.eu/rdf-data/"
DEFAULT_PREFIX = "mangosaurus"

MIN_PHRASE_COUNT = "min_phrase_count"
MIN_CONTEXT_COUNT = "min_context_count"
MIN_PHRASECONTEXT_COUNT = "min_phrasecontext_count"
MAX_PHRASE_LENGTH = "max_phrase_length"
MAX_CONTEXT_LENGTH = "max_context_length"
CONTEXT_SEPARATOR = "context_separator"
PHRASE_SEPARATOR = "phrase_separator"

def to_iri(s: str=""):
    return s.replace('"', "%22").replace("µ", "mu").replace("ª", "_").replace("º", "_").replace("'", "%27").replace(">", "").replace("<", "")

class NifVecGraph(Graph):
    
    def __init__(
        self,
        nif_graph: NifGraph=None,
        context_uris: list=None,
        lexicon: Namespace=None,
        window: Namespace=None,
        context: Namespace=None,
        params: dict={},
        store: Union[Store, str] = "default",
        identifier: Optional[Union[IdentifiedNode, str]] = None,
        namespace_manager: Optional[NamespaceManager] = None,
        base: Optional[str] = None,
        bind_namespaces: str = "core"):
    
        super(NifVecGraph, self).__init__(
            store=store,
            identifier=identifier,
            namespace_manager=namespace_manager,
            base=base,
            bind_namespaces=bind_namespaces,
        )        
        self.min_phrase_count = params.get(MIN_PHRASE_COUNT, 5)
        self.min_context_count = params.get(MIN_CONTEXT_COUNT, 5)
        self.min_phrasecontext_count = params.get(MIN_PHRASECONTEXT_COUNT, 4)
        self.max_phrase_length = params.get(MAX_PHRASE_LENGTH, 4)
        self.max_context_length = params.get(MAX_CONTEXT_LENGTH, 4)
        self.context_separator = params.get(CONTEXT_SEPARATOR, "_")
        self.phrase_separator = params.get(PHRASE_SEPARATOR, "+")
        
        self.bind("nif2vec", NIF2VEC)
        self.bind("nif", NIF)

        if lexicon is None:
            self.lexicon = Namespace(DEFAULT_URI+"lexicon/")
        self.bind("lexicon", self.lexicon)
        if window is None:
            self.window = Namespace(DEFAULT_URI+"window/")
        self.bind("window", self.window)
        if context is None:
            self.context = Namespace(DEFAULT_URI+"context/")
        self.bind("context", self.context)

        logging.info(".. Creating windows dict")
        windows = self.generate_windows(g=nif_graph, context_uris=context_uris)
        logging.info(".. Creating phrase and context dicts")
        phrase_count, context_count = self.create_window_phrase_count_dicts(windows=windows)
        logging.info(".. Adding triples to graph")
        for triple in self.generate_triples(
            windows=windows, 
            phrase_count=phrase_count, 
            context_count=context_count
        ):
            self.add(triple)

    def generate_triples(self, windows: dict={}, phrase_count: dict={}, context_count: dict={}):
    
        for phrase in phrase_count.keys():
            phrase_uri = URIRef(self.lexicon+to_iri(phrase))
            yield ((phrase_uri, RDF.type, NIF.Phrase))
            yield ((phrase_uri, NIF2VEC.hasCount, Literal(phrase_count[phrase], datatype=XSD.nonNegativeInteger)))

        for context in context_count.keys():
            context_uri = URIRef(self.context+to_iri(context[0])+self.context_separator+to_iri(context[1]))
            yield ((context_uri, RDF.type, NIF2VEC.Context))
            yield ((context_uri, NIF2VEC.hasCount, Literal(context_count[context], datatype=XSD.nonNegativeInteger)))

        for phrase in windows.keys():

            for window in windows[phrase]:

                count = windows[phrase][window]
                p = to_iri(window[0])
                n = to_iri(window[1])
                phrase_uri = URIRef(self.lexicon+to_iri(phrase))
                context_uri = URIRef(self.context+p+self.context_separator+n)
                window_uri = URIRef(self.window+p+self.context_separator+to_iri(phrase)+self.context_separator+n)

                yield ((phrase_uri, NIF2VEC.occursIn, window_uri))
                yield ((context_uri, NIF2VEC.occursIn, window_uri))
                yield ((window_uri, RDF.type, NIF2VEC.Window))
                yield ((window_uri, NIF2VEC.hasContext, context_uri))
                yield ((window_uri, NIF2VEC.hasPhrase, phrase_uri))
                yield ((window_uri, NIF2VEC.hasCount, Literal(count, datatype=XSD.nonNegativeInteger)))
    
    def create_window_phrase_count_dicts(self, windows: dict={}):
        """
        """
        # delete phrasewindow with number of occurrence < MIN_PHRASECONTEXT_COUNT
        to_delete = []
        for d_phrase in windows.keys():
            for d_window in windows[d_phrase].keys():
                if windows[d_phrase][d_window] < self.min_phrasecontext_count:
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
        to_delete = [p for p in phrase_count.keys() if phrase_count[p] < self.min_phrase_count]
        for item in to_delete:
            del phrase_count[item]

        # delete windows with number of occurrence < MIN_CONTEXT_COUNT
        to_delete = [c for c in context_count.keys() if context_count[c] < self.min_context_count]
        for item in to_delete:
            del context_count[item]

        return phrase_count, context_count

    def generate_windows(self, g: NifGraph=None, context_uris: list=None):
    
        collection = g.collection

        if context_uris is None:
            context_uris = [c.uri for c in collection.contexts]
        contexts = [c for c in collection.contexts if c.uri in context_uris]

        windows = {}

        for context in contexts:
    
            tokenized_text = tokenizer(context.isString)

            for tok_sentence in tokenized_text:

                sentence = (
                    ["SENTSTART"] + 
                    [word['text'] for word in tok_sentence 
                    if re.match("^[0-9]*[a-zA-Z]*$", word["text"])] + ["SENTEND"]
                )

                for idx, word in enumerate(sentence):

                    for phrase_length in range(1, self.max_phrase_length+1):

                        for pre_length in range(1, self.max_context_length+1):

                            for post_length in range(1, self.max_context_length+1):

                                if idx >= pre_length and idx <= len(sentence)-phrase_length-post_length:

                                    pre_phrase = self.phrase_separator.join(sentence[idx-pre_length+i] for i in range(0, pre_length))
                                    phrase = self.phrase_separator.join(sentence[idx+i] for i in range(0, phrase_length))
                                    post_phrase = self.phrase_separator.join(sentence[idx+phrase_length+i] for i in range(0, post_length))

                                    c = (pre_phrase, post_phrase)

                                    if windows.get(phrase, None) is None:
                                        windows[phrase] = defaultdict(int)

                                    windows[phrase][c] += 1

        return windows
    
    def phrase_contexts(self, phrase: str="", topn: int=15):
        """
        """
        phrase_uri = "<"+self.lexicon+self.phrase_separator.join(phrase.split(" "))+">"
        q = """
    SELECT DISTINCT ?c (sum(?count) as ?n)
    WHERE
    {\n"""
        if not isinstance(self.store, memory.Memory):
            q += "SERVICE <"+self.store.query_endpoint+"> "
        q += """
        {
            """+phrase_uri+""" nif2vec:occursIn ?w .
            ?w nif2vec:hasContext ?c .
            ?w nif2vec:hasCount ?count .
        }
    }
    GROUP BY ?c
    ORDER BY DESC(?n)
    """
        if topn is not None:
            q += "LIMIT "+str(topn)+"\n"
        results = [(tuple(r[0].split("/")[-1].split(self.context_separator)), r[1].value) for r in self.query(q)]
        return results
    
    def most_similar(self,
                     phrase: str="", 
                     topn: int=15, 
                     topcontexts: int=25):

        phrase_uri = "<"+self.lexicon+self.phrase_separator.join(phrase.split(" "))+">"
        q = """
    SELECT distinct ?word (count(?c) as ?num)
    WHERE
    {\n"""
        if not isinstance(self.store, memory.Memory):
            q += "SERVICE <"+self.store.query_endpoint+"> "
        q += """
        {
            SELECT DISTINCT ?c (sum(?count) as ?n)
            WHERE
            {
                """+phrase_uri+""" nif2vec:occursIn ?w .
                ?w nif2vec:hasContext ?c .
                ?w nif2vec:hasCount ?count .
             }
             GROUP BY ?c
             ORDER BY DESC(?n)
             LIMIT """+str(topcontexts)+"""
         }
         ?c nif2vec:occursIn ?w1 .
         ?word nif2vec:occursIn ?w1 .
         ?word rdf:type nif:Phrase .
    }
    GROUP BY ?word
    ORDER BY DESC (?num)
    """
        if topn is not None:
            q += "LIMIT "+str(topn)+"\n"
        results = [item for item in self.query(q)]
        norm = results[0][1].value
        results = [(r[0].split("/")[-1].replace(self.phrase_separator, " "), 1 - r[1].value / norm) for r in results]
        return results

    def df_words_contexts(self, word: str=None, topn=7, topcontexts=10):

        columns = [s[0] for s in self.word_contexts(word, topn=topcontexts)]

        index = [line[0] for line in self.similar_words(word, topn=topn)]
        df = pd.DataFrame(columns=columns, 
                          index=index)
        df.fillna(0, inplace=True)
        for idx in index:
            for c in self.word_contexts(idx, topn = None):
                if c[0] in columns:
                    df.at[idx, c[0]] = c[1]
        return df    