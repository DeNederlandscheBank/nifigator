# -*- coding: utf-8 -*-

import logging
import uuid
from collections import defaultdict
from typing import Optional, Union, List
from zipfile import ZipFile

import rdflib
from rdflib import Graph
from rdflib.namespace import DC, DCTERMS, NamespaceManager
from rdflib.store import Store
from rdflib.term import IdentifiedNode, URIRef, Literal
from rdflib.plugins.stores import sparqlstore
from iribaker import to_iri

from .const import ITSRDF, NIF, OLIA, ONTOLEX, DECOMP, LEXINFO, TBX, SKOS

DEFAULT_URI = "https://mangosaurus.eu/rdf-data/"
DEFAULT_PREFIX = "mangosaurus"

from .lemonobjects import Lexicon

class LemonGraph(Graph):

    """
    An Ontolex-Lemon Graph

    The constructor accepts the same arguments as a `rdflib.Graph`.

    :param file: name of the file to read

    :param lexicon: an Ontolex-Lemon Lexicon

    """

    def __init__(
        self,
        file: str = None,
        lexicon: Lexicon = None,
        URIScheme: str = None,
        store: Union[Store, str] = "default",
        identifier: Optional[Union[IdentifiedNode, str]] = None,
        namespace_manager: Optional[NamespaceManager] = None,
        base: Optional[str] = None,
        bind_namespaces: str = "core",
    ):
        """
        An Ontolex-Lemon Graph

        :param file: name of the file to read

        :param lexicon: a Ontolex-Lemon Lexicon

        """

        super(LemonGraph, self).__init__(
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
        self.bind("tbx", TBX)
        self.bind("ontolex", ONTOLEX)
        self.bind("lexinfo", LEXINFO)
        self.bind("decomp", DECOMP)
        self.bind("skos", SKOS)

        self.open(file=file, lexicon=lexicon)

    def open(
        self,
        file: str = None,
        lexicon: Lexicon = None,
    ):
        """
        Read data from multiple sources into current `LemonGraph` object.

        :param file: name of the file to read

        :param lexicon: a Ontolex-Lemon Lexicon

        :return: None

        """
        if file is not None:
            self.__parse_file(file=file)
        elif lexicon is not None:
            if isinstance(lexicon, dict):
                for l in lexicon.values():
                    self.__parse_lexicon(lexicon=l)
        return self

    def __parse_lexicon(self, lexicon: Lexicon = None):
        """
        Read data from a Lexicon object.

        :param lexicon: a Lexicon

        :return: None

        """
        for r in lexicon.triples():
            self.add(r)

    def __parse_file(self, file: str = None):
        """
        Read data from a file.

        filename ending with "zip": file is extracted and content
        is parsed.

        :param file: a filename.

        :return: None

        """
        if file is not None:
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
                                self.parse(data=f.read().decode(), format="hext")
                            elif filename[-3:].lower() == "ttl":
                                self.parse(data=f.read().decode(), format="turtle")
                            else:
                                self.parse(data=f.read().decode())
            elif file[-4:].lower() == "hext":
                # if file ends with .hext then parse as hext file
                with open(file, encoding="utf-8") as f:
                    logging.info(".. Parsing file " + file + "")
                    self.parse(data=f.read(), format="hext")
            else:
                # otherwise let rdflib determine format
                with open(file, encoding="utf-8") as f:
                    logging.info(".. Parsing file " + file + "")
                    self.parse(data=f.read())

    # @property
    # def lexicon(self, uri: str = DEFAULT_URI):
    #     """
    #     This property constructs and returns a `ontolex:Lexicon`
    #     from the `LemonGraph`.
    #     """
    #     dict_collections = self.query_rdf_type(NIF.ContextCollection)
    #     dict_context = self.query_rdf_type(NIF.Context)
    #     logging.info(".. extracting nif statements")
    #     logging.info(
    #         ".... found " + str(len(dict_collections.keys())) + " collections."
    #     )
    #     logging.info(".... found " + str(len(dict_context.keys())) + " contexts.")

    #     for collection_uri in dict_collections.keys():
    #         collection = NifContextCollection(uri=collection_uri)
    #         for predicate in dict_collections[collection_uri].keys():
    #             if predicate == NIF.hasContext:
    #                 for context_uri in dict_collections[collection_uri][predicate]:
    #                     if isinstance(
    #                         self.store,
    #                         rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore,
    #                     ):
    #                         graph = self.context_graph(uri=context_uri)
    #                     else:
    #                         graph = self

    #                     nif_context = NifContext(
    #                         URIScheme=self.URIScheme,
    #                         uri=context_uri,
    #                         graph=graph,
    #                     )
    #                     collection.add_context(context=nif_context)
    #         return collection
    #     else:
    #         collection = NifContextCollection(uri=uri)
    #         for context_uri in dict_context.keys():
    #             if isinstance(
    #                 self.store, rdflib.plugins.stores.sparqlstore.SPARQLUpdateStore
    #             ):
    #                 graph = self.context_graph(uri=context_uri)
    #             else:
    #                 graph = self

    #             nif_context = NifContext(
    #                 URIScheme=self.URIScheme,
    #                 uri=context_uri,
    #                 graph=graph,
    #             )
    #             collection.add_context(context=nif_context)
    #         return collection

    def extract_lexicon(
        self, lexicon_uri: URIRef = None
    ):
        lexicon = Lexicon(uri=collection_uri)
        return lexicon

    def query_rdf_type(self, rdf_type: URIRef = None):
        if isinstance(self.store, sparqlstore.SPARQLUpdateStore):
            q = (
                """
            SELECT ?s ?p ?o
            WHERE {
                SERVICE <"""
                + self.store.query_endpoint
                + """>
                {
                    ?s rdf:type """
                + rdf_type.n3(self.namespace_manager)
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
                ?s rdf:type """
                + rdf_type.n3(self.namespace_manager)
                + """ .
                ?s ?p ?o .
            }"""
            )
        results = self.query(q)

        d = defaultdict(dict)
        for result in results:
            idx = result[0]
            col = result[1]
            val = result[2]

            if col == NIF.hasContext:
                if col in d[idx].keys():
                    d[idx][col].append(val)
                else:
                    d[idx][col] = [val]
            elif val in OLIA:
                if col in d[idx].keys():
                    d[idx][col].append(val)
                else:
                    d[idx][col] = [val]
            else:
                d[idx][col] = val

        return d
