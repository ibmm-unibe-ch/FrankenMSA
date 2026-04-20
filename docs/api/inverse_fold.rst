Inverse Folding
===============

The inverse folding modules generate protein sequences from structure inputs,
with support for both local and remote ProteinMPNN-based workflows.

Public API
----------

This functional layer provides the stable public entry points for choosing a
backend and requesting sequence generation.

.. code-block:: python

   from frankenmsa.inverse_fold.api import generate_sequences

   sequences, meta = generate_sequences("target.pdb", n=8)

.. automodule:: frankenmsa.inverse_fold.api
   :members:

Inverse Fold Package
--------------------

The package namespace gathers the backends, helpers, and workflow functions so
inverse-folding features can be imported from one place when convenient.

.. code-block:: python

   from frankenmsa.inverse_fold import LocalProteinMPNN, BiolibProteinMPNN

.. automodule:: frankenmsa.inverse_fold
   :members:

Local ProteinMPNN Backend
-------------------------

This backend runs a local ProteinMPNN checkout and is the preferred path when
you want reproducible offline execution or tighter control over model assets.

ProteinMPNN itself is the inverse-folding method introduced by Dauparas et al.,
and FrankenMSA expects an existing local installation rather than shipping the
model weights directly as part of the package.

.. code-block:: python

   from frankenmsa.inverse_fold.protein_mpnn import LocalProteinMPNN

   backend = LocalProteinMPNN.from_directory("~/tools/ProteinMPNN")
   backend.init()

.. automodule:: frankenmsa.inverse_fold.protein_mpnn
   :members:

Remote ProteinMPNN Backend
--------------------------

The remote backend delegates sequence generation to the hosted BioLib
ProteinMPNN service, which can be convenient when a local installation is not
available.

Here FrankenMSA talks to the BioLib-hosted ProteinMPNN service instead of a
repository-local checkout, which makes it useful for quick remote experiments.

.. code-block:: python

   from frankenmsa.inverse_fold.remote_protein_mpnn import BiolibProteinMPNN

   backend = BiolibProteinMPNN()

.. automodule:: frankenmsa.inverse_fold.remote_protein_mpnn
   :members:

ProteinMPNN Support
-------------------

Support helpers resolve local ProteinMPNN roots, weights directories, and
output locations in a consistent way across scripts, notebooks, and the app.

.. code-block:: python

   from frankenmsa.inverse_fold.protein_mpnn_support import resolve_proteinmpnn_root

   root = resolve_proteinmpnn_root()

.. automodule:: frankenmsa.inverse_fold.protein_mpnn_support
   :members: