Alignment
=========

The alignment modules cover MSA generation and search workflows, including
remote services and shared input normalization used by the GUI and notebooks.

Alignment Package
-----------------

The package-level alignment namespace collects the supported backends behind a
single import surface, which makes it easier to compare different retrieval or
search paths without cluttering notebook imports.

.. code-block:: python

   from frankenmsa.align import PLMSearch

   backend = PLMSearch()

.. automodule:: frankenmsa.align
   :members:

PLM-Search Backend
------------------

This backend wraps the PLM-Search remote service for structure-aware sequence
similarity lookup. It is the right entry point when you want a search-oriented
workflow instead of building a conventional MSA from homolog retrieval alone.

PLM-Search itself is an external remote service, so FrankenMSA acts as a
client here rather than implementing the search method locally.

.. code-block:: python

   from frankenmsa.align.plm_search import PLMSearch

   backend = PLMSearch()
   hits = backend.align(["MKTAYIAKQRQISFVKSHFSRQ"])

.. automodule:: frankenmsa.align.plm_search
   :members: