from pathlib import Path
from frankenmsa.utils.fileio import read_a3m, write_a3m
from frankenmsa.utils.msatools import shuffle_msa, unify_length

input_files = [
    Path("tests/files/test1.a3m"),
    Path("tests/files/test2.a3m"),
]

for input_file in input_files:
    output_file = input_file.with_name(input_file.stem + "_shuffled.a3m")

    df = read_a3m(input_file)
    print(f"\nOriginal MSA from {input_file.name}:")
    print(df.head())

    # Ensure all sequences have the same length
    df = unify_length(df, "first")

    # Shuffle non-query sequences column-wise
    shuffled_df = shuffle_msa(df, preserve_gaps=True, random_state=42)
    print(f"\nShuffled MSA from {input_file.name}:")
    print(shuffled_df.head())

    # Write shuffled MSA to file
    write_a3m(shuffled_df, output_file)
    print(f"\nShuffled MSA written to: {output_file}")


    # Option 2: Shuffle only between columns 10 and 80
    #shuffled_partial = shuffle_msa(df, start=10, end=80, preserve_gaps=True, random_state=42)
    #print(f"\nShuffled (cols 10–80) MSA from {input_file.name}:")
    #print(shuffled_partial.head())
    #write_a3m(shuffled_partial, output_file_partial)
    #print(f"\nPartial shuffled MSA written to: {output_file_partial}")