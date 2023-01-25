# -*- coding: utf-8 -*-

import logging
import re
import uuid
from collections import defaultdict
from typing import Optional, Union
from zipfile import ZipFile

from rdflib import Graph
from rdflib.namespace import DC, DCTERMS, RDF, RDFS, XSD, Namespace, NamespaceManager
from rdflib.store import Store
from rdflib.term import IdentifiedNode, Literal, URIRef

from .const import ITSRDF, NIF, NIF_ONTOLOGY, OLIA, UD2OLIA_mappings, mapobject
from .converters import nafConverter
from .nafdocument import NafDocument
from .nifobjects import (
    NifContext,
    NifContextCollection,
    NifPage,
    NifParagraph,
    NifPhrase,
    NifSentence,
    NifWord,
)

DEFAULT_URI = "https://mangosaurus.eu/rdf-data/"
DEFAULT_PREFIX = "mangosaurus"


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
        bind_namespaces: "_NamespaceSetString" = "core",
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
        for r in collection.triples():
            self.add(r)

    def __parse_file(self, file: str = None):
        """
        Read data from a file.

        filename ending with "naf.xml": file is read and parsed as an xml file in NLP Annotation Format.
        filename ending with "zip": file is extracted and content is parsed.

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

    @property
    def collection(self, uri: str = DEFAULT_URI):
        """
        This property constructs and returns a `nif:ContextCollection` from the `NifGraph`.
        """

        def query_rdf_type(rdf_type: URIRef = None):

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

        dict_collections = query_rdf_type(NIF.ContextCollection)
        dict_context = query_rdf_type(NIF.Context)
        logging.info(".. extracting nif statements")
        logging.info(
            ".... found " + str(len(dict_collections.keys())) + " collections."
        )
        logging.info(".... found " + str(len(dict_context.keys())) + " contexts.")

        for collection_uri in dict_collections.keys():
            collection = NifContextCollection(uri=collection_uri)
            for predicate in dict_collections[collection_uri].keys():
                if predicate == NIF.hasContext:
                    for context_uri in dict_collections[collection_uri][predicate]:
                        nif_context = NifContext(URIScheme=self.URIScheme).load(
                            graph=self, uri=context_uri
                        )
                        collection.add_context(context=nif_context)
            return collection
        else:
            collection = NifContextCollection(uri=uri)
            for context_uri in dict_context.keys():
                nif_context = NifContext(URIScheme=self.URIScheme).load(
                    graph=self, uri=context_uri
                )
                collection.add_context(context=nif_context)
            return collection

    # @property
    # def catalog(self):
    #     """
    #     """
    #     # derive the conformsTo from the collection
    #     q = """
    #     SELECT ?s
    #     WHERE {
    #         ?a rdf:type nif:ContextCollection .
    #         ?a dcterms:conformsTo ?s
    #     }"""
    #     qres = self.query(q)
    #     dcterms_conformsTo = [row[0] for row in qres]

    #     # find all context in the graphs with corresponding data
    #     q = """SELECT ?s ?p ?o WHERE { ?s rdf:type nif:Context . ?s ?p ?o . }"""
    #     results = self.query(q)

    #     # construct DataFrame from query results
    #     d = defaultdict(dict)
    #     index = list()
    #     columns = set()
    #     for result in results:
    #         idx = result[0]
    #         col = result[1].n3(self.namespace_manager)
    #         if isinstance(result[2], rdflib.term.Literal):
    #             val = result[2].value
    #         else:
    #             val = result[2]
    #         # if ("dc:" in col or "dcterms:" in col or col == "nif:firstSentence"):
    #         d[idx][col] = val
    #         columns.add(col)
    #         if idx not in index:
    #             index.append(idx)
    #     return d

    # df = pd.DataFrame(
    #     index=index,
    #     columns=list(columns),
    #     data = [[d[idx][col] for col in columns] for idx in index]
    # )
    # df['dcterms:conformsTo'] = [", ".join(dcterms_conformsTo)]*len(df.index)
    # df = df.reindex(sorted(df.columns), axis=1)
    # return df

    # @property
    # def olia_annotations(self):
    #     """
    #     """
    #     df = self.extract(rdf_type="nif:Word", predicate="nif:oliaLink").reset_index()
    #     df[1] = True
    #     df = df.pivot_table(index=['index'], columns=['nif:oliaLink'], values=True, fill_value=0)
    #     df.index = self.natural_sort(df.index)
    #     return df

    # def extract(self,
    #             rdf_type: str=None,
    #             predicate: str="nif:anchorOf"):
    #     """
    #     """
    #     q = """
    #     SELECT ?a ?s
    #     WHERE {
    #         ?a rdf:type """+rdf_type+""" .
    #         ?a """+predicate+""" ?s .
    #     }"""
    #     qres = self.query(q)
    #     # construct DataFrame from query results
    #     index = [
    #         row[0]
    #         for row in qres
    #     ]
    #     columns = [predicate]
    #     data = [
    #         row[1].value
    #         if isinstance(row[1], rdflib.Literal)
    #         else row[1].n3(self.namespace_manager)
    #         for row in qres
    #     ]
    #     df = pd.DataFrame(
    #         index=index,
    #         columns=columns,
    #         data=data
    #     )
    #     # apply natural sort on indices (because they contain offsets without preceding zeros)
    #     df.index = self.natural_sort(df.index)
    #     df.index.name = "index"
    #     return df
