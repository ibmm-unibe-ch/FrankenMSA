def test_get_from_rscb():
    import frankenfold

    pdbid = "1UBQ"
    pdb = frankenfold.core.pdbio.PDB.from_rcsb(pdbid)

    from buildamol import Molecule

    mol = Molecule._from_pdb_string(pdb.data)
    assert mol is not None
    assert mol.count_atoms() > 0
    assert mol.count_residues() > 0


def test_write():
    from frankenfold.core.pdbio import PDB

    pdb = PDB.from_rcsb("1UBQ")
    pdb.write("test.pdb")

    with open("test.pdb", "r") as f:
        pdb_data = f.read()

    assert pdb_data == pdb.data

    import os

    os.remove("test.pdb")


def test_chains():
    from frankenfold.core.pdbio import PDB

    pdb = PDB.from_rcsb("1UBQ")
    chains = pdb.chains

    assert len(chains) == 1
    assert chains[0] == "A"


def test_to_tmpfile():
    from frankenfold.core.pdbio import PDB

    pdb = PDB.from_rcsb("1UBQ")
    pdb.to_tmpfile()

    with open(pdb.file, "r") as f:
        pdb_data = f.read()

    assert pdb_data == pdb.data

    import os

    os.remove(pdb.file)
