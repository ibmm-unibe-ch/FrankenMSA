"""
Functional API for the sequence generators
"""

from .remote_protein_mpnn import BiolibProteinMPNN

__default_generator_class__ = BiolibProteinMPNN
__default_generator__ = None


def set_sequence_generator_backend(generator_class_or_instance):
    """
    Set the default sequence generator backend

    Parameters
    ----------
    generator_class : SequenceGenerator
        The sequence generator backend class to use
    """
    global __default_generator_class__
    global __default_generator__

    if isinstance(generator_class_or_instance, type):
        __default_generator_class__ = generator_class_or_instance
        if __default_generator__ is not None and not isinstance(
            __default_generator__, generator_class_or_instance
        ):
            __default_generator__ = None
    else:
        __default_generator__ = generator_class_or_instance
        __default_generator_class__ = type(generator_class_or_instance)


def get_sequence_generator_backend():
    """
    Get the default sequence generator backend

    Returns
    -------
    SequenceGenerator
        The default sequence generator backend
    """
    global __default_generator__
    if __default_generator__ is None:
        __default_generator__ = __default_generator_class__()
        if getattr(__default_generator__, "needs_init", False):
            __default_generator__.init()
    return __default_generator__


def generate_sequences(
    pdb: str,
    n: int,
    generator=None,
    **kwargs,
):
    """
    Generate protein sequences from a PDB file

    Parameters
    ----------
    pdb : str
        The path to the PDB file
    n : int
        The number of sequences to generate
    generator : SequenceGenerator, optional
        The sequence generator backend to use, by default None
    **kwargs
        Additional keyword arguments to pass to the generator's `generate` method

    Returns
    -------
    List[str]
        The generated sequences
    Dict
        Extra information from the generator on the sequences
    """
    if generator is None:
        generator = get_sequence_generator_backend()
    return generator.generate(pdb, n, **kwargs)


inverse_fold = generate_sequences
"""
Alias for generate_sequences
"""
