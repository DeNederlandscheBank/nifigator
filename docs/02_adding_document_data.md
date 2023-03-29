---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.5
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# PDF documents pipeline

Nifigator contains a PDFDocument object to extract text and page offsets from a PDF document. It uses the Python package PDFMiner.six for this.

## Creating a NifContext from extracted text

```python
from nifigator import PDFDocument

# Extract text from a pdf
filename = "..//data//dnb-annual-report-2021.pdf"
with open(filename, mode="rb") as f:
    pdf = PDFDocument().parse(file=f.read())
```

Write the PDFDocument in xml format to a file with PDFDocument.write() and PDFDocument.getstream(), and open an already saved PDFDocument in xml format with PDFDocument.open().

It is often useful to transform the original url or location of a document to a Universally Unique Identifier (UUID) when storing it.

```python
from nifigator import generate_uuid

original_uri = "https://www.dnb.nl/media/4kobi4vf/dnb-annual-report-2021.pdf"
uri = "https://dnb.nl/rdf-data/"+generate_uuid(uri=original_uri)
```

Then we construct the context

```python
from nifigator import NifContext, OffsetBasedString

# Make a context by passing uri, uri scheme and string
context = NifContext(
    uri=uri,
    URIScheme=OffsetBasedString,
    isString=pdf.text,
)
print(context)
```

```console
(nif:Context) uri = <https://dnb.nl/rdf-data/nif-5282967702ae37d486ad338b9771ca8f>
  isString : 'DNB Annual Report 2021\nStriking a \nnew balance\n\nDe Nederlandsche Bank N.V.\n2021
Annual Report\n\nStriking a new balance\n\nPresented to the General Meeting on 16 March
2022.\n\n1\n\nDNB Annual Report 2021The cut-off date for this report is 10 March
2022.\n\nNotes\n\nThe original Annual Report, including the financial statements, was prepared
in Dutch. In the event \n\nof discrepancies between the Dutch version and this English
translation, the Dutch version prevails. ... '
```


**_NOTE:_** By default, hyphenated words in the document are joined and the page offsets are corrected accordingly. You can turn of this correction off with by setting join_hyphenated_words = False in the PDFDocument constructor.

**_NOTE:_** By default, a number of control characters are deleted from the text. You can set these control characters in the PDFDocument constructor with the ignore_control_characters parameter (a string), default = "[\x00-\x08\x0b-\x0c\x0e-\x1f].

## Page offsets

In some situations it is necessary to know the specific page number that contains a certain part of the text.

```python
from nifigator import NifPage

# A list of NifPages is created using the page offsets from the pdf
pages = [
    NifPage(
        URIScheme=OffsetBasedString,
        uri=uri,
        beginIndex=page.beginIndex,
        endIndex=page.endIndex,
        pageNumber=page.pageNumber,
        referenceContext=context
    )
    for page in pdf.page_offsets]

# The list of pages are added to the context
context.set_Pages(pages)
```

```python
# The individual pages can be retrieved in the following way
context.pages[45]
```

```console
(nif:Page) uri = https://dnb.nl/rdf-data/nif-5282967702ae37d486ad338b9771ca8f&nif=page_105254_107257
  beginIndex : 105254
  endIndex : 107257
  anchorOf : 'Cash and payment systems\n\nConfidence in the payment system remained high in 2021. In a survey held in August 2021, 74% \n\nof\xa0respondents had a high or very high level of confidence in the payment system. Only 1% has \n\nlittle or very little confidence. We studied the drivers of confidence in the payment system for the \n\nfirst time in 2021 (see Figure 4). Being able to pay safely is the primary driver of confidence in the \n\npayment system, but wide acceptance of electronic means of payment, easy payments and fast \n\npayments are also important considerations. \n\nFigure 4  Factors driving confidence in the payment system\n\nSecure payments - 6.0\n\nAcceptance: electronic - 5.8\n\nEasy payments - 5.8\n\nFast payments - 5.8\n\nProper supervision of banks - 5.7\n\nNo sharing of payment data - 5.6\n\nLow risk of fraud - 5.6\n\nNo use of payment data - 5.6\n\nAccessibility - 5.6\n\nNo disruptions - 5.6\n\nAcceptance: cash - 5.3\n\nEnvironment - 4.6\n\n0\n\n20\n\n40\n\n60\n\n80\n\n100\n\n1 Does not contribute \nto my confidence at all\n... '
  pageNumber : 46
```


Note that the page number starts at 1.

The page offsets are aligned with the context string. 

```python
# The page offsets are aligned with the context string
for page in pdf.page_offsets[1:2]:
    print(repr(context.isString[page.beginIndex:page.endIndex]))
```

which gives

```console
'De Nederlandsche Bank N.V.\n2021 Annual Report\n\nStriking a new balance\n\nPresented to the General Meeting on 16 March 2022.\n\n1\n\nDNB Annual Report 2021'
```


## Using the tokenizer from the syntok package


It is possible to use the tokenizer from the syntok package before you process the text through a Stanza NLP processor in the following way.

```python
from nifigator import replace_escape_characters, tokenizer

text = replace_escape_characters(context.isString)
tokenized_text = tokenizer(text)

# correction for bug in stanza
if tokenized_text != []:
    if tokenized_text[-1][-1]['text']=="":
        tokenized_text[-1] = tokenized_text[-1][:-1]
```

```python
print(tokenized_text[0][0:3])
```

which gives:

```console
[{'text': 'DNB', 'start_char': 0, 'end_char': 3}, {'text': 'Annual', 'start_char': 4, 'end_char': 10}, {'text': 'Report', 'start_char': 11, 'end_char': 17}]
```


Next we make the Stanza pipeline for this pretokenized data

```python
import stanza

# create a Stanza pipeline for pretokenized data
nlp = stanza.Pipeline(
        lang='en', 
        processors='tokenize, lemma, pos, depparse', 
        tokenize_pretokenized=True,
        download_method=None,
        verbose=False
)
```

We use the English models for this document. If documents in multiple languages are used then you need to detect the language beforehand from the output of the PDFDocument.

**_NOTE:_** Here we used the lemma, pos and depparse processor. However, you can select the processors you will need; the output from processors lemma, pos and depparse will be added to the NifContext.


Then we process the text through the Stanza pipeline. This will take some time.

```python
from nifigator import align_stanza_dict_offsets

# extract the text from the tokenized data
sentences_text = [[word['text'] for word in sentence] for sentence in tokenized_text]

# run the Stanza pipeline and convert the output to a dictionary
stanza_dict = nlp(sentences_text).to_dict()

# align the stanza output with the tokenized text
stanza_dict = align_stanza_dict_offsets(stanza_dict, tokenized_text)

# load the output into the context
context.load_from_dict(stanza_dict)
```

**_NOTE:_** The Stanza pipeline assumes that between the words there is exactly one space character. In practice multiple spaces and escape characters occur, so that the start_char and the end_char of the Stanza output won't align with the start_char and end_char from the tokenizer output. Therefore we need to correct the start_char and end_char in the Stanza output to the original values. This is done with the function align_stanza_dict_offsets. It replaces the start_char and the end_char of every word from the Stanza output by the respective start_char and end_char from the tokenizer.

If you process text with Stanza then the lemma will be a string Literal in the RDF data. That may not always be convenient because to find lemmas you will need to find string matches. You can also set a lexicon uri in the context. The nif:lemma will then a URIRef of the lexicon uri and the lemma. So if you do in advance: context.set_lexicon(URIRef("https://mangosaurus.eu/rdf-data/lexicon/en/")) then the nif:lemma of the lemma "tree" will be URIRef("https://mangosaurus.eu/rdf-data/lexicon/en/tree").


Metadata can be added to the context by providing a dict with DC and DCTERMS items, for example:

```python
from rdflib import DC, DCTERMS, URIRef, Literal

context.set_metadata({DC.source: URIRef(original_uri),
                      DC.coverage: Literal(2021)})
```

Metadata can be retrieved with:

```python
context.metadata
```

which gives:

```console
{rdflib.term.URIRef('http://purl.org/dc/elements/1.1/source'): 
    rdflib.term.URIRef('https://www.dnb.nl/media/4kobi4vf/dnb-annual-report-2021.pdf'),
 rdflib.term.URIRef('http://purl.org/dc/elements/1.1/coverage'): 
    rdflib.term.Literal('2021', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#integer'))}
```


To store the context add it to a collection

```python
from nifigator import NifContextCollection

# create a collection and add the context
collection = NifContextCollection(uri="https://dnb.nl/rdf-data/")
collection.add_context(context)
```

and serialize the graph to a file in turtle-format:

```python
from nifigator import NifGraph

# create a NifGraph from this collection and serialize it 
g = NifGraph(collection=collection)

g.serialize("..//data//"+generate_uuid(uri=original_uri)+".ttl", format="turtle")
```
