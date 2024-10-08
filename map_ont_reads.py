#!/usr/bin/env python
# Ryan A. Melnyk - RAMelnyk@lbl.gov

import argparse
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
import Levenshtein
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
    parser.add_argument(
        '--barcode',
        action="store_true",
        help="use if input has a barcode region"
    )
    return parser.parse_args()


def minimap_and_samtools(reads, ref):
    cmd = f"""
    minimap2 \
        -a -x map-ont \
        --secondary=no \
        -o tmp/{prefix}.all.sam \
        {ref} \
        {reads}
    """
    proc = subprocess.Popen(cmd.split())
    proc.wait()

    cmd = f"""
    samtools view -h -F 2048 -o tmp/{prefix}.sam tmp/{prefix}.all.sam
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


def lev_dist(seq_df):
    bc_df = seq_df[~seq_df["barcode"].isna()].copy()
    bcs = list(bc_df["barcode"])
    min_dist = []
    for i, bc in enumerate(bcs):
        this_min = 20
        for j, bc2 in enumerate(bcs):
            if i == j:
                continue
            else:
                k = Levenshtein.distance(bc, bc2)
                if k < this_min:
                    this_min = k
        min_dist.append(this_min)
    
    bc_df["min_dist"] = min_dist
    sns.histplot(
        data = bc_df,
        x="min_dist",
        binwidth=1
    )
    total = bc_df.shape[0]
    unique = bc_df["barcode"].nunique()
    plt.title(f"minimum Levenshtein distance - {total} barcodes, {unique} unique")
    plt.xlim(0,15)
    plt.savefig(f"tmp/{prefix}.dist.hist.png", dpi=300)
    return


def plot(seq_df):
    sns.histplot(
        data=seq_df,
        x="length",
        hue="mapped",
        multiple="stack",
        binwidth=100)
    plt.xlim(0, 10000)
    plt.title(f"Read length distribution - {prefix}")
    plt.savefig(f"tmp/{prefix}.map.hist.png", dpi=300)
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
    if args.barcode:
        lev_dist(seq_df)
    plot(seq_df)


if __name__ == '__main__':
    main()
