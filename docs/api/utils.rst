Utilities
=========

The utility modules contain the low-level building blocks that most higher
level workflows depend on: file parsing, core MSA editing and filtering, and
sequence encoding helpers.

File I/O
--------

The file I/O helpers translate between A3M, FASTA, CSV-like tables, and the
DataFrame representation used throughout FrankenMSA. They also cover the
chain-aware helpers needed for multimer workflows.

.. code-block:: python

   from frankenmsa.utils.fileio import read_a3m, split_dataframe_by_chain

   msa = read_a3m("multimer.a3m")
   chains = split_dataframe_by_chain(msa, base_name="target_")

.. automodule:: frankenmsa.utils.fileio
   :members:

MSA Transforms
--------------

These functions implement the core edit, filter, sort, merge, and reshape
operations for alignments represented as DataFrames with a ``sequence`` column.

.. code-block:: python

   from frankenmsa.utils.msatools import slice_sequences, drop_duplicates

   focused = slice_sequences(msa.copy(), 50, 150)
   focused = drop_duplicates(focused)

.. automodule:: frankenmsa.utils.msatools
   :members:

Sequence Helpers
----------------

Sequence helper functions provide shared encodings and related utilities that
support clustering, dimensionality reduction, and other sequence-aware steps.

.. code-block:: python

   from frankenmsa.utils.seqtools import get_encoding_func

   encode = get_encoding_func("onehot")
   encoded = encode(msa["sequence"])

.. automodule:: frankenmsa.utils.seqtools
   :members: