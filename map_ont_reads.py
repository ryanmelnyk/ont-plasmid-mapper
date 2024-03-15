#!/usr/bin/env python
# Ryan A. Melnyk - RAMelnyk@lbl.gov

import argparse
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
import subprocess
from Bio import SeqIO
from Bio.Seq import Seq


def parse_args():
    parser = argparse.ArgumentParser(description='''
    Script for aligning nanopore reads to a reference plasmid
    ''')
    parser.add_argument(
        'reference_file',
        type=str,
        help='path to FASTA-format reference plasmid file')
    parser.add_argument(
        'reads_file',
        type=str,
        help='path to FASTQ file containing nanopore reads')
    parser.add_argument(
        '--prefix',
        type=str,
        help="prefix for output files"
    )
    return parser.parse_args()


def minimap_and_samtools(reads, ref):
    cmd = f"""
    minimap2 \
        -a -x map-ont \
        --secondary=no \
        -o tmp/{prefix}.sam \
        {ref} \
        {reads}
    """
    proc = subprocess.Popen(cmd.split())
    proc.wait()

    cmd = f"""
    samtools view -Sb tmp/{prefix}.sam -o tmp/{prefix}.bam
    """
    proc = subprocess.Popen(cmd.split())
    proc.wait()

    cmd = f"""
    samtools sort tmp/{prefix}.bam -o tmp/{prefix}.sorted.bam
    """
    proc = subprocess.Popen(cmd.split())
    proc.wait()

    cmd = f"""
    samtools mpileup \
        --reference {ref} \
        -o tmp/{prefix}.mpile.txt \
        tmp/{prefix}.sorted.bam
    """
    proc = subprocess.Popen(cmd.split())
    proc.wait()
    return


def read_data(reads_path):
    # get length of sequences
    seq_data = {}
    for seq in SeqIO.parse(open(reads_path), 'fastq'):
        seq_data[seq.id] = [len(seq), False, None]

    # check if read mapped to reference and try to extract barcode
    bc_regex = "CGAGGTCTCT([ATGCN]{20})CGTACGCTGC"
    for line in open(f"tmp/{prefix}.sam"):
        if line.startswith("@"):
            continue
        else:
            vals = line.rstrip().split()
            if vals[2] != "*":
                seq_data[vals[0]][1] = True
                if int(vals[1]) in [16, 2064]:
                    query = str(Seq(vals[9]).reverse_complement())
                else:
                    query = vals[9]
                res = re.search(bc_regex, query)
                if res is None:
                    pass
                else:
                    seq_data[vals[0]][2] = res.group(1)
    df = pd.DataFrame.from_dict(seq_data, orient="index")
    df.columns = ["length", "mapped", "barcode"]
    df.to_csv(f"tmp/{prefix}.csv")
    return df


def plot(seq_df):
    sns.histplot(
        data=seq_df,
        x="length",
        hue="mapped",
        multiple="stack",
        binwidth=100)
    plt.xlim(0, 10000)
    plt.savefig(f"tmp/{prefix}.hist.png", dpi=300)
    return


def main():
    args = parse_args()
    reads_path = os.path.abspath(args.reads_file)
    ref_path = os.path.abspath(args.reference_file)
    global prefix
    if args.prefix:
        prefix = args.prefix
    else:
        prefix = "output"

    minimap_and_samtools(reads_path, ref_path)

    seq_df = read_data(reads_path)
    plot(seq_df)


if __name__ == '__main__':
    main()
