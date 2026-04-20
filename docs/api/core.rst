Core API
========

The core API defines the main user-facing entry points of FrankenMSA: the
top-level import surface, the object-oriented ``MSA`` wrapper, and runtime
helpers that normalize behavior across local and notebook-based execution.

Top-level package
-----------------

The top-level package keeps the most common entry points close at hand, which
is often enough for quick scripts and exploratory notebooks without reaching
into the full internal module layout.

.. code-block:: python

   import frankenmsa as fm

   msa = fm.read_a3m("example.a3m")
   msa = fm.drop_duplicates(msa)
   msa = fm.filter_gaps(msa, allowed_gaps_faction=0.3)

.. automodule:: frankenmsa
   :members:

MSA Wrapper
-----------

The ``MSA`` wrapper provides a thin object layer around a pandas-backed
alignment while delegating the real work to the functional library modules.
It is useful when method chaining reads more clearly than repeatedly calling
standalone helpers.

.. code-block:: python

   from frankenmsa import MSA

   edited = (
      MSA.from_a3m("example.a3m")
      .slice_sequences(20, 120)
      .crop_to_depth(128)
      .drop_duplicates()
   )
   edited.write_a3m("trimmed.a3m")

.. automodule:: frankenmsa.msa
   :members:

Runtime Helpers
---------------

Runtime helpers centralize environment detection and launch-time settings for
local Python sessions, notebook launches, and app execution.

.. code-block:: python

   from frankenmsa.runtime import build_app_launch_env

   env = build_app_launch_env(port=8050, host="localhost", runtime="local")

.. automodule:: frankenmsa.runtime
   :members: