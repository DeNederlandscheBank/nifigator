==============
Short overview
==============

Below a short overview of the functionality of nifigator is given.

Creating a context
~~~~~~~~~~~~~~~~~~

A :class:`~nifigator.nifobjects.NifContext` contains a string of a document or part of it. Here's how to create a simple :class:`~nifigator.nifobjects.NifContext`.

.. code-block:: python

        # The NifContext contains a context which uses a URI scheme
        from nifigator import NifContext, OffsetBasedString

        # Make a context by passing uri, uri scheme and string
        context = NifContext(
          uri="https://mangosaurus.eu/rdf-data/doc_1",
          URIScheme=OffsetBasedString,
          isString="The cat sat on the mat. Felix was his name."
        )

        # Show the string representation of the context
        print(context)

The output shows the string representation of the :class:`~nifigator.nifobjects.NifContext` object:

.. code-block:: none

        (nif:Context) uri = <https://mangosaurus.eu/rdf-data/doc_1>
          isString : "The cat sat on the mat. Felix was his name."

.. note::
   Of each Nif object the string representation starts with the object class name between parenthesis and the specific uri of the Nif object. In the lines below the Nif predicates are shown with their value. In this case only one predicate is specified (isString).

Adding linguistic annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to add linguistic annotations to the context from the output of a Stanza pipeline.

.. code-block:: python

        import stanza

        # Create the Stanza pipeline for English language
        nlp = stanza.Pipeline("en", verbose=False)

        # Process the string of the context and convert is to a dictionary
        stanza_dict = nlp(context.isString).to_dict()

        # Load the dictionary in the context
        context.load_from_stanza_dict(stanza_dict)

Now all data can be accessed from the :class:`~nifigator.nifobjects.NifContext` object.

The first sentence in the context:

.. code-block:: python

        print(context.sentences[0])

This gives:

.. code-block:: none

        (nif:Sentence) uri = https://mangosaurus.eu/rdf-data/doc_1&nif=sentence_0_23
          referenceContext : https://mangosaurus.eu/rdf-data/doc_1
          beginIndex : 0
          endIndex : 23
          anchorOf : "The cat sat on the mat."
          nextSentence : "Felix was his name."
          firstWord : "The"
          lastWord : "."

The uri of this sentences is derived from the uri of the context by adding the specific offsets of the sentence within the context to the context uri. This is called an OffsetBasedString uri; it provides a unique uri for each sentence, word and phrase of the context.

The first word of the second sentence in the context:

.. code-block:: python

        print(context.sentences[1].words[0])

This results in:

.. code-block:: none

        (nif:Word) uri = https://mangosaurus.eu/rdf-data/doc_1&nif=word_24_29
          referenceContext : https://mangosaurus.eu/rdf-data/doc_1
          beginIndex : 24
          endIndex : 29
          anchorOf : "Felix"
          lemma : "Felix"
          pos : olia:ProperNoun
          morphofeats : olia:Singular
          dependency : https://mangosaurus.eu/rdf-data/doc_1&nif=word_42_43
          dependencyRelationtype : nsubj

.. note::
  The part-of-speech tags and the morphological features are converted from Universal Dependencies (the output of the Stanza NLP processor) to core `OLiA <https://github.com/acoli-repo/olia>`_ classes.

All individual predicates can be accessed from the object. For example, the lemma of the third word of the first sentence:

.. code-block:: python

        print(context.sentences[0].words[2].lemma)

This gives:

.. code-block:: none

        'sit'

This is the lemma of the word 'sat' (the third word of the first sentence).

Creating a collection
~~~~~~~~~~~~~~~~~~~~~

You can collect mutliple contexts in a :class:`~nifigator.nifobjects.NifContextCollection`.

.. code-block:: python

        # A NifContextCollection contains a set of contexts
        from nifigator import NifContextCollection

        # Make a collection by passing a uri
        collection = NifContextCollection(uri="https://mangosaurus.eu/rdf-data")

        # Add the context that was made earlier
        collection.add_context(context)

        # show the string representation of the collection
        print(collection)

This gives:

.. code-block:: none

        (nif:ContextCollection) uri = https://mangosaurus.eu/rdf-data
          hasContext : https://mangosaurus.eu/rdf-data/doc_1
          conformsTo : http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/2.1

The contexts are retrievable as a list of the collection and can be accessed in the following way:

.. code-block:: python

        # Retrieving the first context in the collection
        collection.contexts[0]

Creating a graph from a collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :class:`~nifigator.nifgraph.NifGraph` is a `rdflib.Graph` with additional functionality to convert to and from the Nif objects.

You an create a :class:`~nifigator.nifgraph.NifGraph` from a :class:`~nifigator.nifobjects.NifContextCollection` in the following way.

.. code-block:: python

        from nifigator import NifGraph

        g = NifGraph(collection=collection)

You can then use all the functions of a `rdflib.Graph` such as serializing the graph.

.. code-block:: python

        print(g.serialize(format="turtle")[0:1890])

This gives the Nif data in RDF/turtle format:

.. code-block:: none

  @prefix dcterms: <http://purl.org/dc/terms/> .
  @prefix nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .
  @prefix olia: <http://purl.org/olia/olia.owl#> .
  @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
  
  <https://mangosaurus.eu/rdf-data> a nif:ContextCollection ;
      nif:hasContext <https://mangosaurus.eu/rdf-data/doc_1> ;
      dcterms:conformsTo <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/2.1> .
  
  <https://mangosaurus.eu/rdf-data/doc_1&nif=word_15_18> a nif:OffsetBasedString,
          nif:String,
          nif:Word ;
      nif:anchorOf "the"^^xsd:string ;
      nif:anchorOf_no_accents "the"^^xsd:string ;
      nif:anchorOf_no_diacritics "the"^^xsd:string ;
      nif:beginIndex "15"^^xsd:nonNegativeInteger ;
      nif:dependency <https://mangosaurus.eu/rdf-data/doc_1&nif=word_22_23> ;
      nif:dependencyRelationType "det"^^xsd:string ;
      nif:endIndex "18"^^xsd:nonNegativeInteger ;
      nif:lemma "the"^^xsd:string ;
      nif:oliaLink olia:Article,
          olia:Definite ;
      nif:pos olia:Determiner ;
      nif:referenceContext <https://mangosaurus.eu/rdf-data/doc_1> ;
      nif:sentence <https://mangosaurus.eu/rdf-data/doc_1&nif=sentence_0_23> .

  <https://mangosaurus.eu/rdf-data/doc_1&nif=word_19_22> a nif:OffsetBasedString,
          nif:String,
          nif:Word ;
      nif:anchorOf "mat"^^xsd:string ;
      nif:anchorOf_no_accents "mat"^^xsd:string ;
      nif:anchorOf_no_diacritics "mat"^^xsd:string ;
      nif:beginIndex "19"^^xsd:nonNegativeInteger ;
      nif:dependency <https://mangosaurus.eu/rdf-data/doc_1&nif=word_12_14> ;
      nif:dependencyRelationType "obl"^^xsd:string ;
      nif:endIndex "22"^^xsd:nonNegativeInteger ;
      nif:lemma "mat"^^xsd:string ;
      nif:oliaLink olia:Singular ;
      nif:pos olia:CommonNoun ;
      nif:referenceContext <https://mangosaurus.eu/rdf-data/doc_1> ;
      nif:sentence <https://mangosaurus.eu/rdf-data/doc_1&nif=sentence_0_23> .

You can also parse the serialized data from this graph into another :class:`~nifigator.nifgraph.NifGraph` and check whether they are isomorphic (meaning that they contain the same triples excepts from the blank nodes).

.. code-block:: python

        # Create an empty NifGraph
        g1 = NifGraph()
  
        # parse the serialized graph in turtle format
        g1.parse(data=g.serialize(format="turtle"))
  
        # Check whether the graphs are isomorphic
        print(g1.isomorphic(g))

This gives:

.. code-block:: none

        True

With the :class:`~nifigator.nifgraph.NifGraph` you can store the Nif data in a database or in a file with the functionality provided by RDFLib.

If you have read data into a graph then you can create a :class:`~nifigator.nifobjects.NifContextCollection` from this in the following way:

.. code-block:: python

        # generate a NifContextCollection from a `NifGraph`
        collection = g1.collection

        # show the string representation of the result
        print(collection)

The code will look for data in the graph that satisfies the Nif data format. This shows:

.. code-block:: none

        (nif:ContextCollection) uri = https://mangosaurus.eu/rdf-data
          hasContext : https://mangosaurus.eu/rdf-data/doc_1
          conformsTo : http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/2.1

All underlying Nif data can be accessed from this collection in the manner described above, so you can do

.. code-block:: python

        print(collection.contexts[0].sentences[0].words[0])

Which returns:

.. code-block:: none

        (nif:Word) uri = https://mangosaurus.eu/rdf-data/doc_1&nif=word_0_3
          referenceContext : https://mangosaurus.eu/rdf-data/doc_1
          nifsentence : https://mangosaurus.eu/rdf-data/doc_1&nif=sentence_0_23
          beginIndex : 0
          endIndex : 3
          anchorOf : "The"
          lemma : "the"
          pos : olia:Determiner
          morphofeats : olia:Article, olia:Definite
