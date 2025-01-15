"""
Multi-sequence alignment (MSA) module.
"""


def homooligomerize(msas, deletion_matrices, homooligomer=1):
    if homooligomer == 1:
        return msas, deletion_matrices
    else:
        new_msas = []
        new_mtxs = []
        for o in range(homooligomer):
            for msa, mtx in zip(msas, deletion_matrices):
                num_res = len(msa[0])
                L = num_res * o
                R = num_res * (homooligomer - (o + 1))
                new_msas.append(["-" * L + s + "-" * R for s in msa])
                new_mtxs.append([[0] * L + m + [0] * R for m in mtx])
        return new_msas, new_mtxs
