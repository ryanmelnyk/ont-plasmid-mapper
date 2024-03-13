#!/usr/bin/env python
# Ryan A. Melnyk - RAMelnyk@lbl.gov

import argparse
import os
import sys
import subprocess
from Bio import SeqIO


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


def prep_ref(ref):
    # read in plasmid sequence
    seqs = []
    for seq in SeqIO.parse(open(ref), 'fasta'):
        seqs.append(seq)
    if len(seqs) != 1:
        print("Check number of sequences in FASTA file...exiting.")
        sys.exit()
    
    # duplicate and concatenate plasmid sequence
    seqs[0].seq = seqs[0].seq*2
    o = open("tmp/concat_ref.fa", 'w')
    SeqIO.write(seq, o, 'fasta')
    o.close()
    return


def minimap(reads):
    cmd = f"""
    minimap2 -x map-ont -a -o tmp/{prefix}.sam tmp/concat_ref.fa {reads}
    """
    proc = subprocess.Popen(cmd.split())
    proc.wait()


def main():
    args = parse_args()
    reads_path = os.path.abspath(args.reads_file)
    ref_path = os.path.abspath(args.reference_file)
    global prefix
    if args.prefix:
        prefix = args.prefix
    else:
        prefix = "output"

    prep_ref(ref_path)
    minimap(reads_path)
    # make histogram of read lengths
    # % of reads that align?


if __name__ == '__main__':
    main()
