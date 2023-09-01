# -*- coding: utf-8 -*-

import logging
import uuid
from collections import defaultdict
from typing import Optional, Union, List
from zipfile import ZipFile
import pandas as pd

import rdflib
from rdflib import Graph
from rdflib.namespace import DC, RDF, DCTERMS, NamespaceManager
from rdflib.store import Store
from rdflib.term import IdentifiedNode, URIRef, Literal
from rdflib.plugins.stores import sparqlstore
from iribaker import to_iri

from .converters import nafConverter
from .nafdocument import NafDocument
from .nifobjects import (
    NifContext,
    NifContextCollection,
    NifSentence,
)
from .utils import tokenize_text
from .const import ITSRDF, NIF, OLIA, DEFAULT_URI, DEFAULT_PREFIX
from .lemonobjects import Lexicon, LexicalEntry, Form


class NifGraph(Graph):

    """
    An NIF Graph

    The constructor accepts the same arguments as a `rdflib.Graph`.

    :param file: name of the file to read

    :param nafdocument: an xml file in NLP Annotation Format

    :param collection: an NifContextCollection

    """

    def __init__(
        self,
        file: str = None,
        nafdocument: NafDocument = None,
        collection: NifContextCollection = None,
        URIScheme: str = None,
        store: Union[Store, str] = "default",
        identifier: Optional[Union[IdentifiedNode, str]] = None,
        namespace_manager: Optional[NamespaceManager] = None,
        base: Optional[str] = None,
        bind_namespaces: str = "core",
    ):
        """
        An NIF Graph

        :param file: name of the file to read

        :param nafdocument: an xml file in NLP Annotation Format

        :param collection: an NifContextCollection

        """

        super(NifGraph, self).__init__(
            store=store,
            identifier=identifier,
            namespace_manager=namespace_manager,
            base=base,
            bind_namespaces=bind_namespaces,
        )

        self.URIScheme = URIScheme

        self.bind("rdf", ITSRDF)
        self.bind("rdfs", ITSRDF)
        self.bind("itsrdf", ITSRDF)
        self.bind("xsd", ITSRDF)
        self.bind("dcterms", DCTERMS)
        self.bind("dc", DC)
        self.bind("nif", NIF)
        self.bind("olia", OLIA)

        self.open(file=file, nafdocument=nafdocument, collection=collection)

    def open(
        self,
        file: str = None,
        nafdocument: NafDocument = None,
        collection: NifContextCollection = None,
    ):
        """
        Read data from multiple sources into current `NifGraph` object.

        :param file: name of the file to read

        :param nafdocument: an xml file in NLP Annotation Format

        :param collection: an NifContextCollection

        :return: None

        """
        if file is not None:
            self.__parse_file(file=file)
        elif nafdocument is not None:
            self.__parse_nafdocument(nafdocument=nafdocument)
        elif collection is not None:
            self.__parse_collection(collection=collection)
        return self

    def __parse_nafdocument(self, nafdocument: NafDocument = None):
        """
        Read data from an xml file in NLP Annotation Format

        :param nafdocument: an xml file in NLP Annotation Format

        :return: None

        """
        logging.info(".. Parsing NafDocument to NifGraph")

        doc_uri = nafdocument.header["public"]["{http://purl.org/dc/elements/1.1/}uri"]
        doc_uuid = "nif-" + str(uuid.uuid3(uuid.NAMESPACE_DNS, doc_uri).hex)

        base_uri = DEFAULT_URI
        base_prefix = DEFAULT_PREFIX

        collection = nafConverter(
            collection_name="collection",
            context_name=doc_uuid,
            nafdocument=nafdocument,
            base_uri=base_uri,
            base_prefix=base_prefix,
            URIScheme=self.URIScheme,
        )

        self.__parse_collection(collection)

    # self.parse_collection(collection)

    def __parse_collection(self, collection: NifContextCollection = None):
        """
        Read data from a NifContextCollection object.

        :param collection: a NifContextCollection

        :return: None

        """
        g = Graph(identifier=self.identifier)
        for r in collection.triples():
            g.add(r)
        self += g

    def __parse_file(self, file: str = None):
        """
        Read data from a file.

        filename ending with "naf.xml": file is read and parsed as
        an xml file in NLP Annotation Format.
        filename ending with "zip": file is extracted and content
        is parsed.

        :param file: a filename.

        :return: None

        """
        if file is not None:
            if file[-7:].lower() == "naf.xml":
                logging.info(".. Parsing file " + file + "")
                nafdocument = NafDocument().open(file)
                self.__parse_nafdocument(nafdocument=nafdocument)
            else:
                if file[-3:].lower() == "zip":
                    # if zip file then parse all files in zip
                    with ZipFile(file, mode="r") as zipfile:
                        logging.info(".. Reading zip file " + file)
                        for filename in zipfile.namelist():
                            with zipfile.open(filename) as f:
                                logging.info(
                                    ".. Parsing file " + filename + " from zip file"
                                )
                                if filename[-4:].lower() == "hext":
                                    self += Graph().parse(
                                        data=f.read().decode(), format="hext"
                                    )
                                elif filename[-3:].lower() == "ttl":
                                    self += Graph().parse(
                                        data=f.read().decode(), format="turtle"
                                    )
                                else:
                                    self += Graph().parse(data=f.read().decode())
                elif file[-4:].lower() == "hext":
                    # if file ends with .hext then parse as hext file
                    with open(file, encoding="utf-8") as f:
                        logging.info(".. Parsing file " + file + "")
                        self += Graph().parse(data=f.read(), format="hext")
                else:
                    # otherwise let rdflib determine format
                    with open(file, encoding="utf-8") as f:
                        logging.info(".. Parsing file " + file + "")
                        self += Graph().parse(data=f.read())

    @property
    def contexts(self, uri: str = DEFAULT_URI):
        """
        This property constructs and returns a `nif:Context`
        from the `NifGraph`.

        :return: list of `nif:Context` in the graph

        """
        uris = list(self.subjects(RDF.type, NIF.Context))
        return [NifContext(uri=uri, graph=self) for uri in uris]

    @property
    def collections(self, uri: str = DEFAULT_URI):
        """
        This property constructs and returns a list of `nif:ContextCollection`
        from the `NifGraph`.

        :return: list of `nif:ContextCollection` in the graph

        """
        uris = list(self.subjects(RDF.type, NIF.ContextCollection))
        return [NifContextCollection(uri=uri, graph=self) for uri in uris]

    @property
    def collection(self, uri: str = DEFAULT_URI):
        """
        This property constructs and returns the first `nif:ContextCollection`
        from the `NifGraph`.

        :return: the first `nif:ContextCollection` in the graph

        """
        for uri in list(self.subjects(RDF.type, NIF.ContextCollection)):
            return NifContextCollection(uri=uri, graph=self)

        # dict_collections = self.query_rdf_type(NIF.ContextCollection)
        # dict_context = self.query_rdf_type(NIF.Context)
        # logging.info(".. extracting nif statements")
        # logging.info(
        #     ".... found " + str(len(dict_collections.keys())) + " collections."
        # )
        # logging.info(".... found " + str(len(dict_context.keys())) + " contexts.")

        # for collection_uri in dict_collections.keys():
        #     collection = NifContextCollection(uri=collection_uri)
        #     for predicate in dict_collections[collection_uri].keys():
        #         if predicate == NIF.hasContext:
        #             for context_uri in dict_collections[collection_uri][predicate]:
        #                 if isinstance(
        #                     self.store,
        #                     rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore,
        #                 ):
        #                     graph = self.context_graph(uri=context_uri)
        #                 else:
        #                     graph = self

        #                 nif_context = NifContext(
        #                     URIScheme=self.URIScheme,
        #                     uri=context_uri,
        #                     graph=graph,
        #                 )
        #                 collection.add_context(context=nif_context)
        #     return collection
        # else:
        #     collection = NifContextCollection(uri=uri)
        #     for context_uri in dict_context.keys():
        #         if isinstance(
        #             self.store, rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore
        #         ):
        #             graph = self.context_graph(uri=context_uri)
        #         else:
        #             graph = self

        #         nif_context = NifContext(
        #             URIScheme=self.URIScheme,
        #             uri=context_uri,
        #             graph=graph,
        #         )
        #         collection.add_context(context=nif_context)
        #     return collection

    @property
    def catalog(self):
        """ """
        # derive the conformsTo from the collection
        if isinstance(self.store, sparqlstore.SPARQLUpdateStore):
            q = (
                """
            SELECT ?s ?p ?o
            WHERE {
                SERVICE <"""
                + self.store.query_endpoint
                + """>
                {
                    ?s rdf:type nif:ContextCollection .
                    ?s ?p ?o .
                }
            }"""
            )
        else:
            q = """
            SELECT ?s ?p ?o
            WHERE {
                ?s rdf:type nif:ContextCollection .
                ?s ?p ?o .
            }"""
        results = self.query(q)
        collections = defaultdict(dict)
        for s, p, o in results:
            if p == NIF.hasContext:
                if collections[s].get(p, None) is None:
                    collections[s][p] = [o]
                else:
                    collections[s][p].append(o)
            else:
                collections[s][p] = o

        # find all context in the graphs with corresponding data
        if isinstance(self.store, sparqlstore.SPARQLUpdateStore):
            q = (
                """
            SELECT ?s ?p ?o 
            WHERE { 
                SERVICE <"""
                + self.store.query_endpoint
                + """>
                {
                    ?s rdf:type nif:Context . ?s ?p ?o . 
                }
            }"""
            )
        else:
            q = """
            SELECT ?s ?p ?o 
            WHERE { 
                ?s rdf:type nif:Context . ?s ?p ?o . 
            }"""
        results = self.query(q)

        # construct DataFrame from query results
        d = defaultdict(dict)
        index = list()
        columns = set()
        for result in results:
            idx = result[0]
            col = result[1].n3(self.namespace_manager)
            if isinstance(result[2], Literal):
                val = result[2].value
            else:
                val = result[2]
            if "dc:" in col or "dcterms:" in col:
                d[idx][col] = val
                columns.add(col)
            if idx not in index:
                index.append(idx)

        df = pd.DataFrame(
            index=index,
            columns=list(columns),
            data=[[d[idx][col] for col in columns] for idx in index],
        )
        for idx in df.index:
            for c in collections.keys():
                if idx in collections[c][NIF.hasContext]:
                    df.loc[idx, DCTERMS.conformsTo] = collections[c][DCTERMS.conformsTo]
                    df.loc[idx, NIF.ContextCollection] = c
        df = df.reindex(sorted(df.columns), axis=1)
        return df

    # def query_rdf_type(self, rdf_type: URIRef = None):
    #     if isinstance(self.store, sparqlstore.SPARQLUpdateStore):
    #         q = (
    #             """
    #         SELECT ?s ?p ?o
    #         WHERE {
    #             SERVICE <"""
    #             + self.store.query_endpoint
    #             + """>
    #             {
    #                 ?s rdf:type """
    #             + rdf_type.n3(self.namespace_manager)
    #             + """ .
    #                 ?s ?p ?o .
    #             }
    #         }"""
    #         )
    #     else:
    #         q = (
    #             """
    #         SELECT ?s ?p ?o
    #         WHERE {
    #             ?s rdf:type """
    #             + rdf_type.n3(self.namespace_manager)
    #             + """ .
    #             ?s ?p ?o .
    #         }"""
    #         )
    #     results = self.query(q)

    #     d = defaultdict(dict)
    #     for result in results:
    #         idx = result[0]
    #         col = result[1]
    #         val = result[2]

    #         if col == NIF.hasContext:
    #             if col in d[idx].keys():
    #                 d[idx][col].append(val)
    #             else:
    #                 d[idx][col] = [val]
    #         elif val in OLIA:
    #             if col in d[idx].keys():
    #                 d[idx][col].append(val)
    #             else:
    #                 d[idx][col] = [val]
    #         else:
    #             d[idx][col] = val

    #     return d

    def context_graph(self, uri: URIRef = None):
        """ """
        if isinstance(self.store, rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore):
            q = (
                """
            SELECT ?s ?p ?o
            WHERE {
                SERVICE <"""
                + graph.store.query_endpoint
                + """>
                {
                    ?s nif:referenceContext """
                + uri.n3(graph.namespace_manager)
                + """ .
                    ?s ?p ?o .
                }
            }"""
            )
        else:
            q = (
                """
            SELECT ?s ?p ?o
            WHERE {
                ?s nif:referenceContext """
                + uri.n3(graph.namespace_manager)
                + """ .
                ?s ?p ?o .
            }"""
            )
        results = self.query(q)

        graph = Graph(store="SimpleMemory")
        for s, p, o in results:
            # necessary if data is read from http protocol
            if isinstance(o, Literal) and isinstance(o.value, str):
                o = Literal(o.value.replace("\r\n", "\n"), datatype=XSD.string)
            graph.add((s, p, o))
        return graph

    @property
    def lexicon(self):
        """ """

        def noNumber(s: str = ""):
            return not s.replace(".", "", 1).replace(",", "", 1).isdigit()

        # query for all anchorOfs of all word with optional lemma
        if isinstance(self.store, rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore):
            q = (
                """
                SELECT ?anchor ?lemma ?pos ?lang
                WHERE {
                    SERVICE <"""
                + graph.store.query_endpoint
                + """>
                    {
                        ?w rdf:type nif:Word .
                        ?w nif:anchorOf ?anchor .
                        ?w nif:referenceContext ?context .
                        OPTIONAL {?w nif:lemma ?lemma . } .
                        OPTIONAL {?w nif:pos ?pos . } .
                        OPTIONAL {?context dc:language ?lang }
                    }
                }"""
            )
        else:
            q = """
                SELECT ?anchor ?lemma ?pos ?lang
                WHERE {
                    ?w rdf:type nif:Word .
                    ?w nif:anchorOf ?anchor .
                    ?w nif:referenceContext ?context .
                    OPTIONAL {?w nif:lemma ?lemma . } .
                    OPTIONAL {?w nif:pos ?pos . } .
                    OPTIONAL {?context dc:language ?lang }
                }
            """
        # execute the query
        results = self.query(q)

        lexica = dict()

        for anchorOf, lemma, pos, lang in results:
            if lemma is not None and noNumber(lemma):
                # default language is "en"
                if lang is None:
                    lang = "en"

                # construct lexicon if necessary
                if lang not in lexica.keys():
                    lexica[lang] = Lexicon(uri=URIRef(DEFAULT_URI + "lexicon/" + lang))
                    lexica[lang].set_language(lang)

                # derive lexical entry uri from the lemma
                if not isinstance(lemma, URIRef):
                    entry_uri = to_iri(str(lexica[lang].uri) + "/" + lemma)
                else:
                    entry_uri = lemma

                # create the lexical entry
                entry = LexicalEntry(uri=entry_uri, language=lexica[lang].language)

                # set canonicalForm (this is the lemma)
                entry.set_canonicalForm(
                    Form(
                        uri=URIRef(entry_uri),
                        formVariant="canonicalForm",
                        writtenReps=[lemma],
                    )
                )

                # set otherForm if the anchorOf is not the same as the lemma
                if anchorOf.value != lemma.value:
                    entry.set_otherForms(
                        [
                            Form(
                                uri=URIRef(entry_uri),
                                formVariant="otherForm",
                                writtenReps=[anchorOf],
                            )
                        ]
                    )

                # set part of speech if it exists
                if pos is not None:
                    entry.set_partOfSpeechs([pos])

                lexica[lang].add_entry(entry)

        return lexica

    def get(self, uri: URIRef = None):
        """ """
        if uri is None:
            return None
        else:
            r = list(self.triples([uri, RDF.type, None]))
            if len(r) > 0:
                rdf_type = r[0][2]
            else:
                logging.warning("uri not found: " + str(uri))
                return None

            if rdf_type == NIF.ContextCollection:
                collection = NifContextCollection(uri=uri, graph=self)
                return collection
            elif rdf_type == NIF.Context:
                return NifContext(uri=uri, graph=self)
            else:
                context_uri = uri.split("&nif=")[0] + "&nif=context"
                context = NifContext(uri=context_uri, graph=self)
                if rdf_type == NIF.Sentence:
                    return NifSentence(uri=uri, referenceContext=context, graph=self)
                elif rdf_type == NIF.Page:
                    return NifPage(uri=uri, referenceContext=context, graph=self)
                elif rdf_type == NIF.Paragraph:
                    return NifParagraph(uri=uri, referenceContext=context, graph=self)
                elif rdf_type == NIF.Phrase:
                    return NifPhrase(uri=uri, referenceContext=context, graph=self)
                elif rdf_type == NIF.Word:
                    return NifWord(uri=uri, referenceContext=context, graph=self)
