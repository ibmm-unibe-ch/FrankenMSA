Visualization
=============

The visualization modules provide alignment rendering, summary statistics, and
dimensionality-reduction helpers that support both exploratory analysis and GUI
plots.

Visualization Package
---------------------

The package-level namespace collects the most common visualization helpers in a
single place, which is especially handy in short exploratory notebooks.

.. code-block:: python

   from frankenmsa.visual import gap_counts, visualize_msa

.. automodule:: frankenmsa.visual
   :members:

Alignment Charts
----------------

Alignment chart helpers render MSAs into visual summaries suitable for quick
inspection in notebooks or app components.

.. code-block:: python

   from frankenmsa.visual.alignment_chart import visualize_msa

   figure = visualize_msa(msa, backend="plotly")

.. automodule:: frankenmsa.visual.alignment_chart
   :members:

Dimensionality Reduction
------------------------

These helpers convert encoded sequences into lower-dimensional projections for
visual clustering and exploratory plotting.

.. code-block:: python

   from frankenmsa.visual.dimension_reduction import compute_PCA

   rest, query = compute_PCA(msa)

.. automodule:: frankenmsa.visual.dimension_reduction
   :members:

Summary Statistics
------------------

Summary functions compute per-position quantities such as gap counts,
conservation, and query identity without committing to any specific plotting
backend.

.. code-block:: python

   from frankenmsa.visual.summaries import conservation_scores

   scores = conservation_scores(msa)

.. automodule:: frankenmsa.visual.summaries
   :members: