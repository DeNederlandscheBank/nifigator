# coding: utf-8

"""converters"""

import logging
from rdflib.namespace import DC, DCTERMS, XSD
from rdflib.term import Literal, URIRef

from .const import OLIA, mapobject
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


def nafConverter(
    collection_name: str = None,
    context_name: str = None,
    nafdocument: NafDocument = None,
    base_uri: str = None,
    base_prefix: str = None,
    URIScheme: str = None,
):

    collection_uri = base_uri + collection_name
    context_uri = base_uri + context_name

    # create nif:collection
    nif_collection = NifContextCollection(uri=collection_uri)

    # create nif:context
    if nafdocument.raw is None:
        doc_raw = ""
    else:
        doc_raw = nafdocument.raw

    # create NifContext
    nif_context = NifContext(
        isString=doc_raw,
        uri=URIRef(context_uri),
        URIScheme=URIScheme,
    )
    nif_context.set_referenceContext(nif_context)
    nif_collection.add_context(nif_context)

    # set metadata
    metadata = nafdocument.header["public"]
    metadata = {
        URIRef(key.replace("{", "").replace("}", "")): Literal(
            metadata[key], datatype=XSD.string
        )
        for key in metadata.keys()
    }
    metadata[DC.language] = Literal(nafdocument.language, datatype=XSD.string)
    metadata[DCTERMS.created] = Literal(
        nafdocument.header["fileDesc"]["creationtime"], datatype=XSD.string
    )
    metadata[DCTERMS.provenance] = Literal(
        nafdocument.header["fileDesc"]["filename"], datatype=XSD.string
    )
    # correction in naf files, dc:uri is incorrect, should be dcterms:URI
    metadata[DCTERMS.URI] = metadata[URIRef("http://purl.org/dc/elements/1.1/uri")]
    del metadata[URIRef("http://purl.org/dc/elements/1.1/uri")]
    metadata[DCTERMS.identifier] = Literal(nif_context.uri, datatype=XSD.string)
    nif_context.set_metadata(metadata)

    # create nif:sentence and nif:word
    doc_words = {word["id"]: word for word in nafdocument.text}
    doc_terms = {term["id"]: term for term in nafdocument.terms}

    doc_sentences = nafdocument.sentences
    for sent_idx, sentence in enumerate(doc_sentences):
        beginIndex = int(doc_words[sentence["span"][0]["id"]]["offset"])
        endIndex = int(doc_words[sentence["span"][-1]["id"]]["offset"]) + int(
            doc_words[sentence["span"][-1]["id"]]["length"]
        )
        nif_sentence = NifSentence(
            uri=base_uri + context_name,
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=nif_context,
            URIScheme=URIScheme
            # annotation reference missing
        )
        sentence["nif"] = nif_sentence

    nif_words = dict()
    for sent_idx, sentence in enumerate(doc_sentences):

        nif_context.add_sentence(sentence["nif"])

        # Add nextSentence and previousSentence to make graph traversable
        if sent_idx < len(doc_sentences) - 1:
            sentence["nif"].set_nextSentence(doc_sentences[sent_idx + 1]["nif"])
        if sent_idx > 0:
            sentence["nif"].set_previousSentence(doc_sentences[sent_idx - 1]["nif"])

        for word_idx, word_id in enumerate(sentence["span"]):
            word = doc_words[word_id["id"]]
            beginIndex = int(word["offset"])
            endIndex = int(word["offset"]) + int(word["length"])
            nif_word = NifWord(
                beginIndex=beginIndex,
                endIndex=endIndex,
                referenceContext=nif_context,
                nifsentence=sentence["nif"],
                # annotation reference missing
                uri=base_uri + context_name,
                URIScheme=URIScheme,
            )
            word["nif"] = nif_word
            nif_words[nif_word.uri] = nif_word

        # Add nextWord and previousWord
        for word_idx, word_id in enumerate(sentence["span"]):
            word = doc_words[word_id["id"]]
            sentence["nif"].add_word(word["nif"])

            if word_idx < len(sentence["span"]) - 1:
                word["nif"].set_nextWord(
                    doc_words[sentence["span"][word_idx + 1]["id"]]["nif"]
                )
            if word_idx > 0:
                word["nif"].set_previousWord(
                    doc_words[sentence["span"][word_idx - 1]["id"]]["nif"]
                )

        for term in sentence["terms"]:
            term_words = [s["id"] for s in doc_terms[term["id"]]["span"]]
            beginIndex = int(doc_words[term_words[0]]["offset"])
            endIndex = int(doc_words[term_words[-1]]["offset"]) + int(
                doc_words[term_words[-1]]["length"]
            )
            term_lemma = doc_terms[term["id"]].get("lemma", None)
            term_pos = doc_terms[term["id"]].get("pos", None)
            term_pos = mapobject("pos", term_pos.lower()).replace("olia:", "")
            term_pos = [OLIA[term_pos]]
            term_morphofeats = []
            morphofeats = doc_terms[term["id"]].get("morphofeat", None)
            if morphofeats is not None:
                for feat in morphofeats.split("|"):

                    if (
                        feat.split("=")[0] in ["Foreign", "Reflex", "Poss", "Abbr"]
                        and feat.split("=")[1] == "Yes"
                    ):
                        olia_term = (
                            feat.split("=")[0]
                            .replace("Poss", "PossessivePronoun")
                            .replace("Abbr", "Abbreviation")
                            .replace("Reflex", "ReflexivePronoun")
                        )
                        term_morphofeats.append(olia_term)
                    else:
                        term_morphofeats.append(
                            mapobject(feat.split("=")[0], feat.split("=")[1]).replace(
                                "olia:", ""
                            )
                        )

            term_morphofeats = [OLIA[m] for m in term_morphofeats]
            nif_term = NifWord(
                beginIndex=beginIndex,
                endIndex=endIndex,
                referenceContext=nif_context,
                lemma=term_lemma,
                pos=term_pos,
                morphofeats=term_morphofeats,
                # annotation reference missing
                uri=base_uri + context_name,
                URIScheme=URIScheme,
            )
            doc_terms[term["id"]]["nif"] = nif_term

            if nif_term.uri not in nif_words.keys():
                nif_words[nif_term.uri] = nif_term
            else:
                nif_words[nif_term.uri].set_lemma(term_lemma)
                nif_words[nif_term.uri].set_pos(term_pos)
                nif_words[nif_term.uri].set_morphofeats(term_morphofeats)

    # create nif:page
    nif_pages = []
    if len(nafdocument.text) > 0:
        page_number = int(nafdocument.text[0]["page"])
        page_start = int(nafdocument.text[0]["offset"])
        page_end = int(nafdocument.text[0]["offset"])
    else:
        page_number = 1
        page_start = 0
        page_end = 0
    beginIndex = page_start
    endIndex = page_end
    for word in nafdocument.text:
        if int(word["page"]) != page_number:
            nif_page = NifPage(
                beginIndex=beginIndex,
                endIndex=endIndex,
                referenceContext=nif_context,
                uri=base_uri + context_name,
                URIScheme=URIScheme,
            )
            beginIndex = int(word["offset"])
            endIndex = int(word["offset"]) + int(word["length"])
            nif_pages.append(nif_page)
            page_number += 1
        endIndex = int(word["offset"]) + int(word["length"])
    nif_page = NifPage(
        beginIndex=beginIndex,
        endIndex=endIndex,
        referenceContext=nif_context,
        uri=base_uri + context_name,
        URIScheme=URIScheme,
    )
    nif_pages.append(nif_page)

    nif_context.set_Pages(page for page in nif_pages)

    # create nif:phrases
    nif_phrases = []
    for entity in nafdocument.entities:
        taClassRef = "https://stanfordnlp.github.io/stanza#" + entity.get(
            "type", "unknown"
        )
        entity_words = [
            ss["id"] for s in entity["span"] for ss in doc_terms[s["id"]]["span"]
        ]
        beginIndex = int(doc_words[entity_words[0]]["offset"])
        endIndex = int(doc_words[entity_words[-1]]["offset"]) + int(
            doc_words[entity_words[-1]]["length"]
        )
        nif_phrase = NifPhrase(
            beginIndex=beginIndex,
            endIndex=endIndex,
            referenceContext=nif_context,
            taClassRef=URIRef(taClassRef),
            entityOccurrence=True,
            uri=base_uri + context_name,
            URIScheme=URIScheme,
        )
        nif_phrases.append(nif_phrase)
    nif_context.set_Phrases(nif_phrases)

    # Add dependencies:
    for dep in nafdocument.deps:
        from_term = doc_terms[dep["from_term"]]
        to_term = doc_terms[dep["to_term"]]
        rfunc = dep["rfunc"]
        if "nif" in from_term.keys() and "nif" in to_term.keys():
            from_term["nif"].add_dependency(to_term["nif"])
            from_term["nif"].set_dependencyRelationType(rfunc)
        else:
            if "nif" not in from_term.keys():
                logging.warning(
                    ".. from term in dependency not found:\n" + str(from_term)
                )
            if "nif" not in to_term.keys():
                logging.warning(".. to term in dependency not found:\n" + str(to_term))

    # create nif:paragraph
    doc_paragraphs = nafdocument.paragraphs
    for para_idx, paragraph in enumerate(doc_paragraphs):

        if paragraph["span"] != []:

            beginIndex = int(doc_words[paragraph["span"][0]["id"]]["offset"])
            endIndex = int(doc_words[paragraph["span"][-1]["id"]]["offset"]) + int(
                doc_words[paragraph["span"][-1]["id"]]["length"]
            )
            nif_paragraph = NifParagraph(
                beginIndex=beginIndex,
                endIndex=endIndex,
                referenceContext=nif_context,
                # annotation reference missing
                uri=base_uri + context_name,
                URIScheme=URIScheme,
            )
            paragraph["nif"] = nif_paragraph

    nif_context.set_Paragraphs(paragraph["nif"] for paragraph in doc_paragraphs)

    return nif_collection
