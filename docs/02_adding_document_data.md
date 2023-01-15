---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.4
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Adding document data

Nifigator contains a PDFDocument object to extract text and paragraph and page offsets from a PDF document. It uses the Python package PDFMiner.six for this.

## Creating a NifContext from extracted text

```python
from nifigator import PDFDocument

# Extract text from a pdf
filename = "..//data//dnb-annual-report-2021.pdf"
with open(filename, mode="rb") as f:
    pdf = PDFDocument(file=f.read())
```

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

## Paragraph offsets

Similarly it can be necessary to know the specific paragraph number that contains a certain part of the text.

```python
from nifigator import NifParagraph

# A list of NifParagraphs is created using the paragraph offsets from the pdf
paragraphs = [
    NifParagraph(
        URIScheme=OffsetBasedString,
        uri=uri,
        beginIndex=paragraph.beginIndex,
        endIndex=paragraph.endIndex,
        referenceContext=context
    )
    for paragraph in pdf.paragraph_offsets]

context.set_Paragraphs(paragraphs)
```

The paragraphs are then retrievable as a list from the context, for example:

```python
context.paragraphs[150]
```

which gives:

```console
(nif:Paragraph) uri = https://dnb.nl/rdf-data/nif-5282967702ae37d486ad338b9771ca8f#offset_124771_125627
  beginIndex : 124771
  endIndex : 125627
  anchorOf : '\nConstruction of the new DNB Cash Centre in Zeist, a sustainable facility, is progressing well.
\n\nDuring demolition work on the head office building at Frederiksplein, asbestos was found in a \n\nlarge
part of the building’s structure, which means the renovation will experience some delay. \n\nThe move back to
our head office will therefore take place in 2024, which is later than we had \n\nanticipated. In 2021 the
round Satellite tower was dismantled, and it will be given a new purpose \n\nelsewhere. Some of its concrete
is being reused as part of a circular chain in the building and \n\nelsewhere in Amsterdam. The structural
construction phase of the DNB Cash Centre has been \n\ncompleted, and the finishing phase has started.
Ecological integration is a major consideration in \n\nthe\xa0design and construction phases. See also Annex 1
Additional information.\n'
```

We can then derive the linguistic data, add this to a collection

```python
import stanza
nlp = stanza.Pipeline("en", verbose=False)
stanza_dict = nlp(context.isString).to_dict()
context.load_from_dict(stanza_dict)

from nifigator import NifContextCollection
collection = NifContextCollection(uri="https://dnb.nl/rdf-data/")
collection.add_context(context)

from nifigator import NifGraph
g = NifGraph(collection=collection)
```

and serialize the graph to a file in hext-format:

```python
g.serialize("..//data//"+generate_uuid(uri=original_uri)+".hext", format="hext")
```

```python

```
