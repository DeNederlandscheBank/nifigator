
.. image:: https://img.shields.io/pypi/v/nifigator.svg
    :alt: PyPI-Server
    :target: https://pypi.org/project/nifigator/

.. image:: https://readthedocs.org/projects/nifigator/badge/?version=latest
    :alt: ReadTheDocs
    :target: https://nifigator.readthedocs.io/en/latest/

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
        :target: https://opensource.org/licenses/MIT
        :alt: License: MIT

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Code style: black

=========
Nifigator
=========

Nifigator is a pure Python package for working with NLP in RDF. It uses the `NLP Interchange Format (NIF) <https://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html>`_ and is build on top of `RDFLib <https://github.com/RDFLib/rdflib>`_. 

Here is what is does:

* Convert data from text documents to NIF data in RDF

  - Currently supported formats: txt, PDF (text, page and paragraph offsets)

* Add linguistic annotations from NLP processors

  - Currently supported processor: `Stanza <https://stanfordnlp.github.io/stanza/>`_

* Create NIF Vector graph to find phrase and sentences similarities

* RDFLib is used to serialize and deserialize NIF data.

See the `documentation <https://nifigator.readthedocs.io>`_ built from the code.


Installation
------------

To install Nifigator, run this command in your terminal:

.. code-block:: console

    $ pip install nifigator

To install the package from Github

.. code-block:: console

    $ pip install -e git+https://github.com/denederlandschebank/nifigator.git
