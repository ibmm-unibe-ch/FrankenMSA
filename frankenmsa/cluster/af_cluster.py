"""
Cluster an MSA using DBSCAN as described by


[Wayment-Steele, H. K. et al. Predicting multiple conformations via sequence clustering and AlphaFold2. Nature 625, 832–839 (2024)](https://www.nature.com/articles/s41586-023-06832-9)

"""

from afcluster import AFCluster, afcluster


dbscan = afcluster
"""
Alias for `afcluster` function.
"""

DBScan = AFCluster
"""
Alias for `AFCluster` class.
"""
