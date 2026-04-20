Clustering
==========

The clustering modules group aligned sequences into interpretable subsets and
provide the supporting helpers needed to project and save those subsets in the
library and GUI.

Clustering Package
------------------

The package namespace exposes the clustering backends and helper workflows from
one place, which is convenient when you want to try several grouping strategies
over the same alignment.

.. code-block:: python

   from frankenmsa.cluster import AFCluster, KMeans

   dbscan_like = AFCluster()
   partitioner = KMeans()

.. automodule:: frankenmsa.cluster
   :members:

AFCluster Backend
-----------------

AFCluster exposes DBSCAN-style clustering tailored to MSA analysis and follows
the AFCluster package used in conformational sampling workflows.

This follows the AFCluster workflow described by Wayment-Steele et al. for
exploring alternative conformational states through sequence-space clustering.

.. code-block:: python

   from frankenmsa.cluster.af_cluster import afcluster

   clustered = afcluster(msa, eps=8.0, min_samples=5)

.. automodule:: frankenmsa.cluster.af_cluster
   :members:

KMeans Backend
--------------

The KMeans backend provides a straightforward centroid-based clustering option
once sequences have been encoded into numerical feature vectors.

.. code-block:: python

   from frankenmsa.cluster.kmeans import kmeans

   clustered = kmeans(msa, n_clusters=6, sequence_encoding="onehot")

.. automodule:: frankenmsa.cluster.kmeans
   :members:

Ward Merge Backend
------------------

The Ward merge backend performs size-aware centroid merging on existing cluster
assignments, which is useful as a second-stage consolidation step.

.. code-block:: python

   from frankenmsa.cluster.ward import ward_merge_cluster_centroids

   merged = ward_merge_cluster_centroids(clustered, n_clusters=3)

.. automodule:: frankenmsa.cluster.ward
   :members: