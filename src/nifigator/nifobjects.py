# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict, defaultdict, deque
from typing import Union, List

import iribaker
from rdflib import Graph
from rdflib.namespace import DC, DCTERMS, RDF, XSD
from rdflib.term import IdentifiedNode, Literal, URIRef

from .const import (
    ITSRDF,
    NIF,
    NIF_ONTOLOGY,
    OLIA,
    EntityOccurrence,
    OffsetBasedString,
    RFC5147String,
    TermOccurrence,
    mapobject,
    upos2olia,
)
from .utils import delete_accents, delete_diacritics, natural_sort


class NifContext:
    pass


class NifSentence:
    pass


class NifParagraph:
    pass


class NifPage:
    pass


class NifPhrase:
    pass


class NifWord:
    pass


class NifBase(object):
    """
    A NIF Base

    :param uri: the uri of the object

    """

    def __init__(self, uri: Union[URIRef, str] = None):
        self.set_uri(uri)

    def __eq__(self, other):
        return self._uri == other._uri

    @property
    def uri(self):
        """
        Returns the uri of the object
        """
        if self._uri is not None:
            return self._uri
        else:
            return None

    def set_uri(self, uri: Union[URIRef, str] = None):
        """
        Sets the uri of the object. If the uri is a string then it is converted to an iri.
        """
        if isinstance(uri, str):
            self._uri = URIRef(iribaker.to_iri(uri))
        else:
            self._uri = uri


class NifString(NifBase):
    """
    A NIF String

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    """

    def __init__(
        self,
        URIScheme: str = None,
        uri: Union[URIRef, str] = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        graph: Graph = None,
    ):
        self.set_URIScheme(URIScheme)
        self.set_referenceContext(referenceContext)
        self.set_beginIndex(beginIndex)
        self.set_endIndex(endIndex)
        self.set_uri(uri)
        self.set_graph(graph)

    def __eq__(self, other):
        return (
            (self._URIScheme == other._URIScheme)
            & (self._beginIndex == other._beginIndex)
            & (self._endIndex == other._endIndex)
            & (self._referenceContext.uri == other._referenceContext.uri)
            & super(NifBase, self).__eq__(other)
        )

    @property
    def beginIndex(self):
        """
        Returns the start index of the context string as an `int`.
        """
        if self._beginIndex is not None:
            return int(self._beginIndex)
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=NIF.beginIndex):
                return int(item)
        else:
            return None

    @property
    def endIndex(self):
        """
        Returns the end index of the context string as an `int`.
        """
        if self._endIndex is not None:
            return int(self._endIndex)
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=NIF.endIndex):
                return int(item)
        else:
            return None

    @property
    def referenceContext(self):
        """
        Returns the context of the current object
        """
        if self._referenceContext is not None:
            return self._referenceContext
        else:
            return None

    @property
    def anchorOf(self):
        """
        Returns the string of the object as a `str`. The anchorOf is not store in the object but extracted from the referenceContext.
        """
        return self.referenceContext.isString[self.beginIndex : self.endIndex]

    @property
    def anchorOf_no_accents(self):
        """
        Returns the string without accents of the object as a `str`.
        """
        anchorOf = self.referenceContext.isString[self.beginIndex : self.endIndex]
        if self._referenceContext.metadata is not None:
            lang = self._referenceContext._metadata.get(
                DC.language, Literal("en", datatype=XSD.string)
            )
        else:
            lang = Literal("en", datatype=XSD.string)
        return delete_accents(anchorOf, lang=lang)

    @property
    def anchorOf_no_diacritics(self):
        """
        Returns the string without diacritics of the object as a `str`.
        """
        anchorOf = self.referenceContext.isString[self.beginIndex : self.endIndex]
        if self._referenceContext.metadata is not None:
            lang = self._referenceContext._metadata.get(
                DC.language, Literal("en", datatype=XSD.string)
            )
        else:
            lang = Literal("en", datatype=XSD.string)

        return delete_diacritics(anchorOf, lang=lang)

    @property
    def URIScheme(self):
        """
        Returns the URIScheme
        """
        return self._URIScheme

    def set_uri(self, uri: Union[URIRef, str] = None):
        """
        Sets the uri of the object
        """
        if uri is not None:
            if not isinstance(uri, URIRef):
                if not isinstance(self, NifContext):
                    uri_format = OffsetBasedString
                    if uri_format == OffsetBasedString:
                        uri = (
                            uri
                            + "#offset_"
                            + str(self.beginIndex)
                            + "_"
                            + str(self.endIndex)
                        )
                    elif uri_format == RFC5147String:
                        uri = (
                            uri
                            + "#char="
                            + str(self.beginIndex)
                            + ","
                            + str(self.endIndex)
                        )
            super().set_uri(uri=uri)

    def set_beginIndex(self, beginIndex: Union[Literal, int] = None):
        """
        Sets the start of the index of the string. The type of beginIndex can be a `Literal` or
        an `int`. If the type is an `int` then it is converted to a Literal.
        """
        if isinstance(beginIndex, int) or isinstance(beginIndex, str):
            self._beginIndex = Literal(beginIndex, datatype=XSD.nonNegativeInteger)
        else:
            self._beginIndex = beginIndex

    def set_endIndex(self, endIndex: Union[Literal, int] = None):
        """
        Sets the end of the index of the string. The type of endIndex can be a `Literal` or
        an `int`. If the type is an `int` then it is converted to a Literal.
        """
        if isinstance(endIndex, int) or isinstance(endIndex, str):
            self._endIndex = Literal(endIndex, datatype=XSD.nonNegativeInteger)
        else:
            self._endIndex = endIndex

    def set_referenceContext(self, referenceContext: NifContext = None):
        """
        Sets the referenceContext of the object.
        """
        if referenceContext is not None:
            self._referenceContext = referenceContext

    def set_anchorOf(self, anchorOf: Union[str, Literal] = None):
        """
        The anchorOf should be consistent with the string in the referenceContext, otherwise an error is logged.
        """
        if self.anchorOf is not None:
            if str(anchorOf) != self.anchorOf:
                logging.error(
                    "Inconsistency in anchorOf string and (part in) referenceContext string: "
                    + str(uri)
                )
        # if isinstance(anchorOf, str):
        #     self._anchorOf = Literal(anchorOf, datatype=XSD.string)
        # elif isinstance(anchorOf, Literal):
        #     self._anchorOf = anchorOf

    def set_URIScheme(self, URIScheme: str = None):
        """
        Sets the URIScheme of the object
        """
        self._URIScheme = URIScheme

    def set_graph(self, graph: Graph = None):
        self.graph = graph

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            if self._URIScheme == OffsetBasedString:
                yield (self.uri, RDF.type, NIF.OffsetBasedString)
            elif self._URIScheme == RFC5147String:
                yield (self.uri, RDF.type, NIF.RFC5147String)
            yield (self.uri, RDF.type, NIF.String)
            if self._beginIndex is not None:
                yield (self.uri, NIF.beginIndex, self._beginIndex)
            if self._endIndex is not None:
                yield (self.uri, NIF.endIndex, self._endIndex)
            if self._referenceContext is not None:
                yield (self.uri, NIF.referenceContext, self._referenceContext.uri)


class NifContext(NifString):
    """
    A NIF Context

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param sourceUrl: the source url of the context

    :param predLang: the predominant language of the context

    :param isString: the string of the context

    :param metadata: a list of URIRefs with metadata

    """

    def __init__(
        self,
        URIScheme: str = None,
        uri: Union[URIRef, str] = None,
        sourceUrl: URIRef = None,
        predLang: URIRef = None,
        isString: Union[Literal, str] = None,
        metadata: dict = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=0 if isString is not None else None,
            endIndex=len(isString) if isString is not None else None,
            referenceContext=self,
        )
        self.set_Sentences(None)
        self.set_Paragraphs(None)
        self.set_Pages(None)
        self.set_Phrases(None)
        self.set_graph(graph)
        self.set_sourceUrl(sourceUrl)
        self.set_predLang(predLang)
        self.set_isString(isString)
        self.set_metadata(metadata)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = f"(nif:Context) uri = {self.uri.n3()}\n"
        if self.sourceUrl is not None:
            s += f"  sourceUrl : {self.sourceUrl.n3()}\n"
        if self.predLang is not None:
            s += f"  predLang : {self.predLang.n3()}\n"
        if self.isString is not None:
            if len(self.isString) > 1000:
                s += f'  isString : {repr(self.isString[0:1000]+"... ")}\n'
            else:
                s += f"  isString : {repr(self.isString)}\n"
        if self.firstSentence is not None:
            s += f"  firstSentence : {repr(self.firstSentence.anchorOf)}\n"
        if self.lastSentence is not None:
            s += f"  lastSentence : {repr(self.lastSentence.anchorOf)}\n"
        if self._metadata is not None and self._metadata != {}:
            for d in self._metadata.keys():
                s += f"  {d} : {self._metadata[d]}\n"
        return s

    def __eq__(self, other):
        return (
            (self._URIScheme == other._URIScheme)
            & (self._uri == other._uri)
            & (self.sourceUrl == other.sourceUrl)
            & (self.predLang == other.predLang)
            & (self.isString == other.isString)
            & (self.metadata == other.metadata)
            & super(NifBase, self).__eq__(other)
        )

    @property
    def metadata(self):
        """
        Returns the metadata of the context
        """
        if self._metadata is not None:
            return self._metadata
        elif self.graph is not None:
            metadata = {}
            for p, o in self.graph.predicate_objects(subject=self.uri):
                if p in DC or p in DCTERMS:
                    metadata[p] = o
            return metadata
        else:
            return None

    @property
    def sourceUrl(self):
        """
        Returns the sourceUrl of the context
        """
        if self._sourceUrl is not None:
            return self._sourceUrl
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=NIF.sourceUrl):
                return item
        else:
            return None

    @property
    def predLang(self):
        """
        Returns the predLang of the context
        """
        if self._predLang is not None:
            return self._predLang
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=NIF.predLang):
                return item.value
        else:
            return None

    @property
    def isString(self):
        """
        Returns the isString of the context
        """
        if self._isString is not None:
            return self._isString.value
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=NIF.isString):
                return item.value
        else:
            return None

    @property
    def firstSentence(self):
        """
        Returns the first sentence of the context.
        """
        if self._sentences is not None:
            return self._sentences[0]
        else:
            return None

    @property
    def lastSentence(self):
        """
        Returns the last sentence of the context.
        """
        if self._sentences is not None:
            return self._sentences[-1]
        else:
            return None

    @property
    def sentences(self):
        """
        Returns all sentences in the context as a list.
        """
        if self._sentences is not None:
            return list(self._sentences)
        else:
            return None

    @property
    def firstParagraph(self):
        """
        Returns the first paragraph of the context.
        """
        if self._paragraphs is not None:
            return self._paragraphs[0]
        else:
            return None

    @property
    def lastParagraph(self):
        """
        Returns the last paragraph of the context.
        """
        if self._paragraphs is not None:
            return self._paragraphs[-1]
        else:
            return None

    @property
    def paragraphs(self):
        """
        Returns all paragraphs in the context as a list.
        """
        if self._paragraphs is not None:
            return list(self._paragraphs)
        else:
            return None

    @property
    def firstPage(self):
        """
        Returns the first page of the context.
        """
        if self._pages is not None:
            return self._pages[0]
        else:
            return None

    @property
    def lastPage(self):
        """
        Returns the last page of the context.
        """
        if self._pages is not None:
            return self._pages[-1]
        else:
            return None

    @property
    def pages(self):
        """
        Returns all pages in the context as a list.
        """
        if self._pages is not None:
            return list(self._pages)
        else:
            return None

    @property
    def firstPhrase(self):
        """
        Returns the first phrase of the context.
        """
        if self._phrases is not None:
            return self._phrases[0]
        else:
            return None

    @property
    def lastPhrase(self):
        """
        Returns the last phrase of the context.
        """
        if self._phrases is not None:
            return self._phrases[-1]
        else:
            return None

    @property
    def phrases(self):
        """
        Returns all phrases in the context as a list.
        """
        if self._phrases is not None:
            return list(self._phrases)
        else:
            return None

    def set_metadata(self, metadata: dict = None):
        """
        Sets the metadata of the context (a dict of predicates and objects)
        """
        if metadata is not None:
            self._metadata = metadata
        else:
            self._metadata = {}

    def set_sourceUrl(self, sourceUrl: URIRef = None):
        """
        Sets the sourceUrl of the context
        """
        self._sourceUrl = sourceUrl

    def set_predLang(self, predLang: Union[URIRef, str] = None):
        """
        Sets the predominant language of the context
        """
        if predLang is not None:
            if not isinstance(predLang, URIRef):
                self._predLang = Literal(predLang)
            else:
                self._predLang = predLang
        else:
            self._predLang = None

    def set_isString(self, isString: Union[Literal, str] = None):
        """
        Sets the string of the context (rdflib.Literal or string)
        """
        if isinstance(isString, str):
            self._isString = Literal(isString, datatype=XSD.string)
        else:
            self._isString = isString

    def set_Pages(self, pages: list = None):
        """
        Sets the pages of the context (a list of NifPage)
        """
        if pages is not None:
            self._pages = deque(pages)
        else:
            self._pages = None

    def set_Paragraphs(self, paragraphs: list = None):
        """
        Sets the paragraphs of the context (a list of NifParagraph)
        """
        if paragraphs is not None:
            self._paragraphs = deque(paragraphs)
        else:
            self._paragraphs = None

    def set_Phrases(self, phrases: list = None):
        """
        Sets the phrases of the context (a list of NifPhrases)
        """
        if phrases is not None:
            self._phrases = deque(phrases)
        else:
            self._phrases = None

    def set_Sentences(self, sentences: list = None):
        """
        Sets the sentences of the context (a list of NifSentence)
        """
        if sentences is not None:
            self._sentences = deque(sentences)
        else:
            self._sentences = None

    def add_sentence(self, sentence: NifSentence = None):
        """
        Adds a sentences to the context (a NifSentence)
        """
        if sentence is not None:
            if self._sentences is None:
                self._sentences = deque([sentence])
            else:
                self._sentences.append(sentence)

    def set_graph(self, graph: Graph = None):
        self.graph = graph
        if graph is not None:
            self.load()

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.Context)
            for key in self._metadata.keys():
                yield (self.uri, key, self._metadata[key])
            if self._isString is not None:
                yield (self.uri, NIF.isString, self._isString)
            if self._sourceUrl is not None:
                yield (self.uri, NIF.sourceUrl, self._sourceUrl)
            if self._predLang is not None:
                yield (self.uri, NIF.predLang, self._predLang)
            if self.firstSentence is not None:
                yield (self.uri, NIF.firstSentence, self.firstSentence.uri)
            if self.lastSentence is not None:
                yield (self.uri, NIF.lastSentence, self.lastSentence.uri)

            if self._sentences is not None:
                for sentence in self._sentences:
                    for triple in sentence.triples():
                        yield triple

            if self._paragraphs is not None:
                for paragraph in self._paragraphs:
                    for triple in paragraph.triples():
                        yield triple

            if self._pages is not None:
                for page in self._pages:
                    for triple in page.triples():
                        yield triple

            if self._phrases is not None:
                for phrase in self._phrases:
                    for triple in phrase.triples():
                        yield triple

            for triple in super().triples():
                yield triple

    def load(self):
        """
        Load a context from a graph (based on uri)
        """
        sent_uris = natural_sort(
            [s for s in self.graph.subjects(predicate=RDF.type, object=NIF.Sentence)]
        )
        page_uris = natural_sort(
            [s for s in self.graph.subjects(predicate=RDF.type, object=NIF.Page)]
        )
        para_uris = natural_sort(
            [s for s in self.graph.subjects(predicate=RDF.type, object=NIF.Para)]
        )
        phrase_uris = natural_sort(
            [s for s in self.graph.subjects(predicate=RDF.type, object=NIF.Phrase)]
        )
        # for _, _, o in graph.triples((uri, NIF.beginIndex, None)):
        #     self.set_beginIndex(o)
        # for _, _, o in graph.triples((uri, NIF.endIndex, None)):
        #     self.set_endIndex(o)
        # for o in self.graph.objects(subject=self.uri, predicate=NIF.isString):
        #     self.set_isString(o)
        # for _, _, o in graph.triples((uri, NIF.sourceUrl, None)):
        #     self.set_sourceUrl(o)
        # for _, _, o in graph.triples((uri, NIF.predLang, None)):
        #     self.set_predLang(o)
        for o in self.graph.objects(subject=self.uri, predicate=RDF.type):
            if o == NIF.OffsetBasedString or o == NIF.RFC5147String:
                self.set_URIScheme(o)

        # extract pages from graph
        self.set_Pages(
            [
                NifPage(
                    URIScheme=self.URIScheme,
                    uri=page_uri,
                    referenceContext=self,
                    graph=self.graph,
                )
                for page_uri in page_uris
            ]
        )
        # extract paragraphs from graph
        self.set_Paragraphs(
            [
                NifParagraph(
                    URIScheme=self.URIScheme,
                    uri=para_uri,
                    referenceContext=self,
                    graph=self.graph,
                )
                for para_uri in para_uris
            ]
        )
        # extract phrases from graph
        self.set_Phrases(
            [
                NifPhrase(
                    URIScheme=self.URIScheme,
                    uri=phrase_uri,
                    referenceContext=self,
                    graph=self.graph,
                )
                for phrase_uri in phrase_uris
            ]
        )

        nifsentences = []
        for sent_uri in sent_uris:
            nifsentence = NifSentence(
                URIScheme=self.URIScheme,
                uri=sent_uri,
                referenceContext=self,
                graph=self.graph,
            )

            word_uris = list()
            for s in self.graph.subjects(predicate=NIF.sentence, object=sent_uri):
                if (s, RDF.type, NIF.Word) in self.graph:
                    word_uris.append(s)
            word_uris = natural_sort(word_uris)

            # extract words from graph
            words = OrderedDict()
            for word_uri in word_uris:
                words[word_uri] = NifWord(
                    URIScheme=self.URIScheme,
                    uri=word_uri,
                    referenceContext=self.referenceContext,
                    nifsentence=nifsentence,
                    graph=self.graph,
                )
            nifsentence.set_Words(words.values())

            # replace dependency uris by word objects
            for word_idx, word in enumerate(words.values()):
                word.set_dependency([words[dep] for dep in word.dependency])

            words = nifsentence.words
            if words is not None:
                # replace nextWord and previousWord uris by word objects
                for word_idx, word in enumerate(words):
                    if word_idx > 0:
                        word.set_previousWord(words[word_idx - 1])
                    if word_idx < len(words) - 1:
                        word.set_nextWord(words[word_idx + 1])

            nifsentences.append(nifsentence)

        self.set_Sentences(nifsentences)
        sentences = self.sentences
        if sentences is not None:
            for sent_idx, sentence in enumerate(sentences):
                if sent_idx > 0:
                    sentence.set_previousSentence(sentences[sent_idx - 1])
                if sent_idx < len(sentences) - 1:
                    sentence.set_nextSentence(sentences[sent_idx + 1])

    def load_from_dict(self, stanza_dict: list = None):
        """
        Load a context from stanza dictionary
        """
        if stanza_dict is not None:
            for sent_idx, sent in enumerate(stanza_dict):
                nif_sent = NifSentence(
                    uri=str(self.uri),
                    beginIndex=sent[0]["start_char"],
                    endIndex=sent[-1]["end_char"],
                    referenceContext=self,
                    URIScheme=self.URIScheme,
                )
                self.add_sentence(nif_sent)

                for word_idx, word in enumerate(sent):
                    nif_word = NifWord(
                        uri=str(self.uri),
                        beginIndex=word["start_char"],
                        endIndex=word["end_char"],
                        referenceContext=self,
                        nifsentence=nif_sent,
                        URIScheme=self.URIScheme,
                    )
                    nif_sent.add_word(nif_word)

                    nif_word.set_lemma(word.get("lemma", None))

                    upos = word.get("upos", None)
                    if upos is not None:
                        if upos in upos2olia.keys():
                            nif_word.add_pos(upos2olia.get(word["upos"]))
                        else:
                            logging.error(
                                ".. part-of-speech tag not found: " + word["upos"]
                            )
                    feats = word.get("feats", None)
                    if feats is not None:
                        for i in feats.split("|"):
                            p = i.split("=")[0]
                            o = i.split("=")[1]
                            olia = mapobject(p, o)
                            if olia is not None:
                                nif_word.add_morphofeat(URIRef(olia))

                for word_idx, word in enumerate(sent):
                    nif_sent._words[word_idx].set_dependencyRelationType(
                        word.get("deprel", None)
                    )

                    dep = word.get("head", None)
                    if dep is not None:
                        if dep != 0:  # if dep is 0 then it is the root
                            nif_sent._words[word_idx].set_dependency(
                                [nif_sent._words[dep - 1]]
                            )

                words = nif_sent._words
                if words is not None:
                    for word_idx, word in enumerate(words):
                        if word_idx < len(words) - 1:
                            word.set_nextWord(words[word_idx + 1])
                        if word_idx > 0:
                            word.set_previousWord(words[word_idx - 1])

            sentences = self.sentences
            if sentences is not None:
                for sent_idx, sentence in enumerate(sentences):
                    if sent_idx < len(sentences) - 1:
                        sentence.set_nextSentence(sentences[sent_idx + 1])
                    if sent_idx > 0:
                        sentence.set_previousSentence(sentences[sent_idx - 1])


class NifStructure(NifString):
    """
    A NIF Structure

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    """

    def __init__(
        self,
        uri: Union[URIRef, str] = None,
        URIScheme: str = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=referenceContext,
            graph=graph,
        )

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            for triple in super().triples():
                yield triple


class NifPhrase(NifStructure):
    """
    A NIF Phrase

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    :param taIdentRef: text analysis identifier reference

    :param taClassRef: text analysis class reference

    :param taConfidence: confidence of the annotation

    :param PhraseType: type of phrase (EntityOccurrence, TermOccurrence)
    """

    def __init__(
        self,
        uri: Union[URIRef, str] = None,
        URIScheme: str = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        taIdentRef: URIRef = None,
        taClassRef: URIRef = None,
        taConfidence: Union[Literal, float] = None,
        PhraseType: str = None,
        nextPhrase: NifPhrase = None,
        previousPhrase: NifPhrase = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=referenceContext,
            graph=graph,
        )
        self.set_taIdentRef(taIdentRef)
        self.set_taClassRef(taClassRef)
        self.set_taConfidence(taConfidence)
        self.set_PhraseType(PhraseType)
        self._set_nextPhrase(nextPhrase)
        self._set_previousPhrase(previousPhrase)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self._PhraseType == EntityOccurrence:
            s = f"(nif:EntityOccurrence) uri = {self.uri.n3()}\n"
        else:
            s = f"(nif:TermOccurrence) uri = {self.uri.n3()}\n"
        if self.referenceContext is not None:
            s += f"  referenceContext : {self.referenceContext.uri}\n"
        if self.beginIndex is not None:
            s += f"  beginIndex : {self.beginIndex}\n"
        if self.endIndex is not None:
            s += f"  endIndex : {self.endIndex}\n"
        if self.anchorOf is not None:
            s += f'  anchorOf : "{self.anchorOf}"\n'
        if self.taIdentRef is not None:
            s += f"  taIdentRef : {self.taIdentRef}\n"
        if self.taClassRef is not None:
            s += f"  taClassRef : {self.taClassRef}\n"
        if self.taConfidence is not None:
            s += f"  taConfidence : {self.taConfidence}\n"
        return s

    @property
    def PhraseType(self):
        """
        Returns the phrasetype (entity or term occurrence)
        """
        if self._PhraseType is not None:
            return self._PhraseType
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=RDF.type):
                if o in [TermOccurrence, EntityOccurrence]:
                    return o
        else:
            return None

    @property
    def taIdentRef(self):
        """
        Returns text analysis identifier reference
        """
        if self._taIdentRef is not None:
            return self._taIdentRef
        elif self.graph is not None:
            for item in self.graph.objects(
                subject=self.uri, predicate=ITSRDF.taIdentRef
            ):
                return item
        else:
            return None

    @property
    def taClassRef(self):
        """
        Returns text analysis class reference
        """
        if self._taClassRef is not None:
            return self._taClassRef
        elif self.graph is not None:
            for item in self.graph.objects(
                subject=self.uri, predicate=ITSRDF.taClassRef
            ):
                return item
        else:
            return None

    @property
    def taConfidence(self):
        """
        Returns text analysis confidence
        """
        if self._taConfidence is not None:
            return float(self._taConfidence.value)
        elif self.graph is not None:
            for item in self.graph.objects(
                subject=self.uri, predicate=ITSRDF.taConfidence
            ):
                return float(item.value)
        else:
            return None

    @property
    def nextPhrase(self):
        """
        Returns the next phrase
        """
        if self._nextPhrase is not None:
            return self._nextPhrase
        else:
            return None

    @property
    def previousPhrase(self):
        """
        Returns the previous phrase
        """
        if self._previousPhrase is not None:
            return self._previousPhrase
        else:
            return None

    def set_PhraseType(self, PhraseType: str = None):
        """
        Sets the phrase type (EntityOccurrence or TermOccurrence)
        """
        self._PhraseType = PhraseType

    def set_taIdentRef(self, taIdentRef: Union[URIRef, str] = None):
        """
        Sets the text analysis identifier reference (as a rdflib.URIRef)
        """
        if isinstance(taIdentRef, str):
            self._taIdentRef = URIRef(taIdentRef)
        else:
            self._taIdentRef = taIdentRef

    def set_taClassRef(self, taClassRef: Union[URIRef, str] = None):
        """
        Sets the text analysis class reference (as a rdflib.URIRef)
        """
        if isinstance(taClassRef, str):
            self._taClassRef = URIRef(taClassRef)
        else:
            self._taClassRef = taClassRef

    def set_taConfidence(self, taConfidence: Union[Literal, float] = None):
        """
        Sets the text analysis confidence (float)
        """
        if isinstance(taConfidence, float) or isinstance(taConfidence, str):
            self._taConfidence = Literal(taConfidence, datatype=XSD.float)
        else:
            self._taConfidence = taConfidence

    def _set_nextPhrase(self, nextPhrase: NifPhrase = None):
        """
        Sets the next phrase
        """
        self._nextPhrase = nextPhrase

    def _set_previousPhrase(self, previousPhrase: NifPhrase = None):
        """
        Sets the previous phrase
        """
        self._previousPhrase = previousPhrase

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.Phrase)
            if self._PhraseType == EntityOccurrence:
                yield (self.uri, RDF.type, NIF.EntityOccurrence)
            elif self._PhraseType == TermOccurrence:
                yield (self.uri, RDF.type, NIF.TermOccurrence)
            if self.taClassRef is not None:
                yield (self.uri, ITSRDF.taClassRef, self._taClassRef)
            if self.taIdentRef is not None:
                yield (self.uri, ITSRDF.taIdentRef, self._taIdentRef)
            if self.taConfidence is not None:
                yield (self.uri, ITSRDF.taConfidence, self._taConfidence)
            for triple in super().triples():
                yield triple


class NifSentence(NifStructure):
    """
    A NIF Sentence

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    :param nextSentence: the next sentence in the context

    :param previousSentence: the previous sentence in the context

    """

    def __init__(
        self,
        uri: Union[URIRef, str] = None,
        URIScheme: str = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        nextSentence: Union[URIRef, str] = None,
        previousSentence: Union[URIRef, str] = None,
        words: List[Union[NifWord, URIRef]] = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=referenceContext,
            graph=graph,
        )
        self.set_nextSentence(nextSentence)
        self.set_previousSentence(previousSentence)
        self.set_Words(words)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = f"(nif:Sentence) uri = {self.uri}\n"
        if self.referenceContext is not None:
            s += f"  referenceContext : {self.referenceContext.uri}\n"
        if self.beginIndex is not None:
            s += f"  beginIndex : {self.beginIndex}\n"
        if self.endIndex is not None:
            s += f"  endIndex : {self.endIndex}\n"
        if self.anchorOf is not None:
            s += f"  anchorOf : {repr(self.anchorOf)}\n"
        if self.nextSentence is not None:
            if len(self.nextSentence.anchorOf) > 100:
                s += f"  nextSentence : {repr(self.nextSentence.anchorOf[0:100])}...\n"
            else:
                s += f"  nextSentence : {repr(self.nextSentence.anchorOf)}\n"
        if self.previousSentence is not None:
            if len(self.previousSentence.anchorOf) > 100:
                s += f"  previousSentence : {repr(self.previousSentence.anchorOf[0:100])}... \n"
            else:
                s += f"  previousSentence : {repr(self.previousSentence.anchorOf)}\n"
        if self.firstWord is not None:
            s += f'  firstWord : "{self.firstWord.anchorOf}"\n'
        if self.lastWord is not None:
            s += f'  lastWord : "{self.lastWord.anchorOf}"\n'
        return s

    @property
    def nextSentence(self):
        if self._nextSentence is not None:
            return self._nextSentence
        else:
            return None

    @property
    def previousSentence(self):
        if self._previousSentence is not None:
            return self._previousSentence
        else:
            return None

    @property
    def firstWord(self):
        if self._words is not None:
            return self._words[0]
        else:
            return None

    @property
    def lastWord(self):
        if self._words is not None:
            return self._words[-1]
        else:
            return None

    @property
    def words(self):
        if self._words is not None:
            return list(self._words)
        else:
            return None

    @property
    def lemmas(self):
        return " ".join([w.lemma for w in self.words])

    def set_nextSentence(self, nextSentence: NifSentence = None):
        self._nextSentence = nextSentence

    def set_previousSentence(self, previousSentence: NifSentence = None):
        self._previousSentence = previousSentence

    def set_Words(self, words: list = None):
        if words is not None:
            self._words = deque(words)
        else:
            self._words = None

    def add_word(self, word: NifWord = None):
        if word is not None:
            if self._words is None:
                self._words = deque([word])
            else:
                self._words.append(word)

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.Sentence)
            for triple in super().triples():
                yield triple
            if self.nextSentence is not None:
                yield (self.uri, NIF.nextSentence, self.nextSentence.uri)
            if self.previousSentence is not None:
                yield (self.uri, NIF.previousSentence, self.previousSentence.uri)
            if self.firstWord is not None:
                yield (self.uri, NIF.firstWord, self.firstWord.uri)
            if self.lastWord is not None:
                yield (self.uri, NIF.lastWord, self.lastWord.uri)
            for word in self._words:
                for triple in word.triples():
                    yield triple

    def load(
        self,
        graph: Graph = None,
        referenceContext: NifContext = None,
        uri: URIRef = None,
    ):
        """
        Load a sentence from a graph (based on uri)
        """
        self.set_uri(uri)
        self.set_referenceContext(referenceContext)
        # for s, p, o in graph.triples((uri, NIF.beginIndex, None)):
        #     self.set_beginIndex(o)
        # for s, p, o in graph.triples((uri, NIF.endIndex, None)):
        #     self.set_endIndex(o)
        # for s, p, o in graph.triples((uri, NIF.anchorOf, None)):
        #     self.set_anchorOf(o)
        # for s, p, o in graph.triples((uri, NIF.nextSentence, None)):
        #     self.set_nextSentence(o)
        # for s, p, o in graph.triples((uri, NIF.previousSentence, None)):
        #     self.set_previousSentence(o)
        # for s, p, o in graph.triples((uri, NIF.firstWord, None)):
        #     first_word = o
        # for s, p, o in graph.triples((uri, NIF.lastWord, None)):
        #     last_word = o

        return self


class NifParagraph(NifStructure):
    """
    A NIF Paragraph

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    """

    def __init__(
        self,
        URIScheme: str = None,
        uri: Union[URIRef, str] = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=referenceContext,
            graph=graph,
        )

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = f"(nif:Paragraph) uri = {self.uri}\n"
        if self.beginIndex is not None:
            s += f"  beginIndex : {self.beginIndex}\n"
        if self.endIndex is not None:
            s += f"  endIndex : {self.endIndex}\n"
        if self.anchorOf is not None:
            if len(self.anchorOf) > 1000:
                s += f'  anchorOf : {repr(self.anchorOf[0:1000]+"... ")}\n'
            else:
                s += f"  anchorOf : {repr(self.anchorOf)}\n"
        return s

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.Paragraph)
            for triple in super().triples():
                yield triple


class NifPage(NifStructure):
    """
    A NIF Page

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    """

    def __init__(
        self,
        URIScheme: str = None,
        uri: Union[URIRef, str] = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=referenceContext,
            graph=graph,
        )

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = f"(nif:Page) uri = {self.uri}\n"
        if self.beginIndex is not None:
            s += f"  beginIndex : {self.beginIndex}\n"
        if self.endIndex is not None:
            s += f"  endIndex : {self.endIndex}\n"
        if self.anchorOf is not None:
            if len(self.anchorOf) > 1000:
                s += f'  anchorOf : {repr(self.anchorOf[0:1000]+"... ")}\n'
            else:
                s += f"  anchorOf : {repr(self.anchorOf)}\n"
        return s

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.Page)
            for triple in super().triples():
                yield triple


# class NifTitle(NifStructure):

#     def __init__(self, uri: str=None):
#         super().__init__(uri)


class NifWord(NifStructure):
    """
    A NIF Word

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param beginIndex: the start index in the context string

    :param endIndex: the end index in the context string

    :param referenceContext: the context to which the string refers

    :param nifsentence: the sentence of the word

    :param lemma: the lemma of the word

    :param pos: the part-of-speech tags (a list)

    :param morphofeats: the morphological features (a list)

    :param dependency: dependency relations of the word (a list)

    :param dependencyRelationType: the type of dependency relation of the word

    :param nextWord: the next word in the sentence

    :param previousWord: the previous word in the sentence

    """

    def __init__(
        self,
        URIScheme: str = None,
        uri: Union[URIRef, str] = None,
        beginIndex: Union[Literal, int] = None,
        endIndex: Union[Literal, int] = None,
        referenceContext: NifContext = None,
        nifsentence: NifSentence = None,
        lemma: str = None,
        pos: list = None,
        morphofeats: list = None,
        dependency: list = None,
        dependencyRelationType: str = None,
        nextWord: str = None,
        previousWord: str = None,
        graph: Graph = None,
    ):
        super().__init__(
            URIScheme=URIScheme,
            uri=uri,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=referenceContext,
            graph=graph,
        )
        self.set_nifsentence(nifsentence)
        self.set_lemma(lemma)
        self.set_pos(pos)
        self.set_morphofeats(morphofeats)
        self.set_dependency(dependency)
        self.set_dependencyRelationType(dependencyRelationType)
        self.set_nextWord(nextWord)
        self.set_previousWord(previousWord)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = f"(nif:Word) uri = {self.uri}\n"
        if self.referenceContext is not None:
            s += f"  referenceContext : {self.referenceContext.uri}\n"
        if self.nifsentence is not None:
            s += f"  nifsentence : {self.nifsentence.uri}\n"
        if self.beginIndex is not None:
            s += f"  beginIndex : {self.beginIndex}\n"
        if self.endIndex is not None:
            s += f"  endIndex : {self.endIndex}\n"
        if self.nextWord is not None:
            s += f'  nextWord : "{self.nextWord.anchorOf}"\n'
        if self.previousWord is not None:
            s += f'  previousWord : "{self.previousWord.anchorOf}"\n'
        if self.anchorOf is not None:
            s += f'  anchorOf : "{self.anchorOf}"\n'
        if self.lemma is not None:
            s += f'  lemma : "{self.lemma}"\n'
        if self.pos is not None and self.pos != []:
            s += f'  pos : {", ".join([str(m).replace(OLIA, "olia:") for m in self.pos])}\n'
        if self.morphofeats is not None and self.morphofeats != []:
            s += f'  morphofeats : {", ".join([str(m).replace(OLIA, "olia:") for m in self.morphofeats])}\n'
        if self.dependency is not None and self.dependency != []:
            s += f'  dependency : {", ".join([dep.uri for dep in self.dependency])}\n'  # [str(dep.uri) for dep in self.dependency]
        if self.dependencyRelationType is not None:
            s += f"  dependencyRelationtype : {self.dependencyRelationType}\n"
        return s

    @property
    def nifsentence(self):
        """
        Returns the sentence to which the word belongs
        """
        if self._nifsentence is not None:
            return self._nifsentence
        else:
            return None

    @property
    def lemma(self):
        """
        Returns the lemma of the word
        """
        if self._lemma is not None:
            return self._lemma.value
        elif self.graph is not None:
            for item in self.graph.objects(subject=self.uri, predicate=NIF.lemma):
                return item.value
        else:
            return None

    @property
    def pos(self):
        """
        Returns the part-of-speech (pos) of the word
        """
        if self._pos is not None:
            return self._pos
        elif self.graph is not None:
            return [
                item for item in self.graph.objects(subject=self.uri, predicate=NIF.pos)
            ]
        else:
            return None

    @property
    def morphofeats(self):
        """
        Returns the morphological features of the word as a list
        """
        if self._morphofeats is not None:
            return self._morphofeats
        elif self.graph is not None:
            return [
                item
                for item in self.graph.objects(subject=self.uri, predicate=NIF.oliaLink)
            ]
        else:
            return []

    @property
    def dependency(self):
        """
        Returns the dependencies of the word as a list
        """
        if self._dependency is not None:
            return self._dependency
        elif self.graph is not None:
            return [
                item
                for item in self.graph.objects(
                    subject=self.uri, predicate=NIF.dependency
                )
            ]
        else:
            return []

    @property
    def dependencyRelationType(self):
        """
        Returns the dependency relation type of the word
        """
        if self._dependencyRelationType is not None:
            return self._dependencyRelationType.value
        elif self.graph is not None:
            for item in self.graph.objects(
                subject=self.uri, predicate=NIF.dependencyRelationType
            ):
                return item.value
        else:
            return None

    @property
    def nextWord(self):
        """
        Returns the next word of the word in the sentence
        """
        if self._nextWord is not None:
            return self._nextWord
        else:
            return None

    @property
    def previousWord(self):
        """
        Returns the previous word of the word in the sentence
        """
        if self._previousWord is not None:
            return self._previousWord
        else:
            return None

    def set_nifsentence(self, nifsentence: NifSentence = None):
        """
        Sets the sentence of which the word is a part
        """
        self._nifsentence = nifsentence

    def set_lemma(self, lemma: str = None):
        """
        Sets the lemma of the word (a string)
        """
        if lemma is not None and lemma != "":
            self._lemma = Literal(lemma, datatype=XSD.string)
        else:
            self._lemma = None

    def set_pos(self, pos: list = None):
        """
        Sets the part-of-speech (pos) of the word
        (a rdflib.URIRef or a list of rdflib.URIRef)
        """
        if pos is not None and pos != []:
            self._pos = pos
        else:
            self._pos = None

    def set_morphofeats(self, morphofeats: list = None):
        """
        Sets the morphological features of the word
        (a rdflib.URIRef or a list of rdflib.URIRef)
        """
        if morphofeats is not None and morphofeats != []:
            self._morphofeats = morphofeats
        else:
            self._morphofeats = None

    def set_dependency(self, dependency: list = None):
        """
        Sets the dependency of the word (a list)
        """
        if dependency is not None and dependency != []:
            self._dependency = dependency
        else:
            self._dependency = None

    def set_dependencyRelationType(self, dependencyRelationType: str = None):
        """
        Sets the dependencyRelationType of the word (a string)
        """
        if dependencyRelationType is not None and dependencyRelationType != "":
            self._dependencyRelationType = Literal(
                dependencyRelationType, datatype=XSD.string
            )
        else:
            self._dependencyRelationType = None

    def set_nextWord(self, nextWord: NifWord = None):
        """
        Sets the next word of the word in the sentence
        """
        self._nextWord = nextWord

    def set_previousWord(self, previousWord: NifWord = None):
        """
        Sets the previous word of the word in the sentence
        """
        self._previousWord = previousWord

    def add_dependency(self, dependency: URIRef = None):
        """
        Add a dependency to the list of dependencies of the word
        """
        if self.dependency is not None and self.dependency != []:
            self.dependency.append(dependency)
        else:
            self.set_dependency([dependency])

    def add_morphofeat(self, morphofeat: URIRef = None):
        """
        Add a morphofeat to the list of morphofeats of the word
        """
        if self.morphofeats is not None and self.morphofeats != []:
            self.morphofeats.append(morphofeat)
        else:
            self.set_morphofeats([morphofeat])

    def add_pos(self, pos: URIRef = None):
        """
        Add a pos to the list of pos of the word
        """
        if self.pos is not None and self.pos != []:
            self.pos.append(pos)
        else:
            self.set_pos([pos])

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.Word)
            if self.nifsentence is not None:
                yield (self.uri, NIF.sentence, self._nifsentence.uri)
            for triple in super().triples():
                yield triple
            yield (self.uri, NIF.anchorOf, Literal(self.anchorOf, datatype=XSD.string))
            if self.lemma is not None:
                yield (self.uri, NIF.lemma, self._lemma)
            if self.pos is not None and self._pos != []:
                for pos in self._pos:
                    yield (self.uri, NIF.pos, pos)
            if self._morphofeats is not None and self._morphofeats != []:
                for morphofeat in self._morphofeats:
                    yield (self.uri, NIF.oliaLink, morphofeat)
            if self.nextWord is not None:
                yield (self.uri, NIF.nextWord, self.nextWord.uri)
            if self.previousWord is not None:
                yield (self.uri, NIF.previousWord, self.previousWord.uri)
            if self.dependencyRelationType is not None:
                yield (
                    self.uri,
                    NIF.dependencyRelationType,
                    self._dependencyRelationType,
                )
            if self._dependency is not None:
                for dep in self._dependency:
                    yield (self.uri, NIF.dependency, dep.uri)


class NifContextCollection(NifBase):
    """
    A NIF Context Collection

    :param URIScheme: the URIScheme of the object

    :param uri: the uri of the object

    :param hasContext: the list of contexts of the collection

    :param conformsTo: the NIF Ontology version

    """

    def __init__(
        self,
        URIScheme: str = None,
        uri: Union[URIRef, str] = None,
        hasContext: list = None,
        conformsTo: Union[URIRef, str] = None,
    ):
        super().__init__(uri=uri)
        self.set_hasContext(hasContext)
        self.set_conformsTo(conformsTo)

    @property
    def hasContext(self):
        if self._hasContext is not None:
            return list(self._hasContext.values())
        else:
            return []

    def set_hasContext(self, hasContext: list = None):
        if hasContext is not None:
            self._hasContext = {context.uri: context for context in hasContext}
        else:
            self._hasContext = {}

    @property
    def conformsTo(self):
        if self._conformsTo is not None:
            return self._conformsTo
        else:
            return None

    def set_conformsTo(self, conformsTo: Union[URIRef, str]):
        if conformsTo is not None:
            if isinstance(conformsTo, str):
                self._conformsTo = URIRef(conformsTo)
            else:
                self._conformsTo = conformsTo
        else:
            self._conformsTo = URIRef(NIF_ONTOLOGY)

    def add_context(self, context: NifContext = None):
        if context is not None:
            self._hasContext[context.uri] = context

    @property
    def contexts(self):
        return list(self._hasContext.values())

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = f"(nif:ContextCollection) uri = {self.uri}\n"
        s += f"  conformsTo : {self.conformsTo}\n"
        for context in self.hasContext[0:10]:
            s += f"  hasContext : {context.uri}\n"
        if len(self.hasContext) > 10:
            s += "  hasContext : ... \n"
        return s

    def triples(self):
        """
        Generates all the triples
        """
        if self.uri is not None:
            yield (self.uri, RDF.type, NIF.ContextCollection)
            if self.conformsTo is not None:
                yield (self.uri, DCTERMS.conformsTo, self.conformsTo)
            for context in self.hasContext:
                yield (self.uri, NIF.hasContext, context.uri)
                for triple in context.triples():
                    yield triple
