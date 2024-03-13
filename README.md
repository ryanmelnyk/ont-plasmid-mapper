# ont-plasmid-mapper
Scripts for aligning ONT reads to plasmids


### Environment

I haven't created a yaml file yet as I'm not sure if this is a pipeline sort of thing that merits nextflow integration or just a collection of scripts. For now I'm just listing the required python and command line tools below.

I installed minimap2/samtools using `homebrew` in OSX and managed python packages with the pip installed by conda in my base environment.

```
minimap2 v2.27-r1193
samtools v1.19.2

pip install Bio
```

### Input data

- Reference fasta file of expected plasmid (e.g. `test/reference.fa`)
- FASTQ reads from nanopore (e.g. `test/reads.fastq`)
