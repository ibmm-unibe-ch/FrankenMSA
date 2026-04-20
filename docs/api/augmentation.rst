Augmentation
============

Augmentation in FrankenMSA focuses on generating additional alignment content
from limited inputs, especially single-sequence starting points.

GhostFold Backend
-----------------

The GhostFold backend wraps the GhostFold command-line tool for synthetic MSA
generation from a single input sequence.

GhostFold itself is an external augmentation tool, and FrankenMSA integrates it
through its CLI rather than reimplementing the model internals.

.. code-block:: python

   from frankenmsa.augment.ghostfold import GhostFold

   ghostfold = GhostFold()
   augmented = ghostfold.augment("ACDEFGHIKLMNPQRSTVWY")

.. automodule:: frankenmsa.augment.ghostfold
   :members: