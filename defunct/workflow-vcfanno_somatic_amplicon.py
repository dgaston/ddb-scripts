#!/usr/bin/env python

# Standard packages
import os
import sys
import argparse

# Third-party packages
from toil.job import Job

# Package methods
from ddb import configuration
from ddb_ngsflow import gatk
from ddb_ngsflow import annotation
from ddb_ngsflow import pipeline
from ddb_ngsflow.align import bwa
from ddb_ngsflow.utils import utilities
from ddb_ngsflow.qc import qc
from ddb_ngsflow.coverage import sambamba
from ddb_ngsflow.variation import variation
from ddb_ngsflow.variation import freebayes
from ddb_ngsflow.variation import mutect
from ddb_ngsflow.variation import platypus
from ddb_ngsflow.variation import vardict
from ddb_ngsflow.variation import scalpel
from ddb_ngsflow.variation.sv import pindel


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--samples_file', help="Input configuration file for samples")
    parser.add_argument('-c', '--configuration', help="Configuration file for various settings")
    Job.Runner.addToilOptions(parser)
    args = parser.parse_args()
    args.logLevel = "INFO"

    sys.stdout.write("Setting up analysis directory\n")

    if not os.path.exists("Logs"):
        os.makedirs("Logs")
    if not os.path.exists("FinalVCFs"):
        os.makedirs("FinalVCFs")
    if not os.path.exists("FinalBAMs"):
        os.makedirs("FinalBAMs")
    if not os.path.exists("Intermediates"):
        os.makedirs("Intermediates")
    if not os.path.exists("Coverage"):
        os.makedirs("Coverage")
    if not os.path.exists("Reports"):
        os.makedirs("Reports")

    sys.stdout.write("Parsing configuration data\n")
    config = configuration.configure_runtime(args.configuration)

    sys.stdout.write("Parsing sample data\n")
    samples = configuration.configure_samples(args.samples_file, config)

    # Workflow Graph definition. The following workflow definition should create a valid Directed Acyclic Graph (DAG)
    root_job = Job.wrapJobFn(pipeline.spawn_batch_jobs, cores=1)

    # Per sample jobs
    for sample in samples:
        vcfanno_job = Job.wrapJobFn(annotation.vcfanno, config, sample, samples,
                                    "{}.snpEff.{}.vcf".format(sample, config['snpeff']['reference']),
                                    cores=int(config['vcfanno']['num_cores']),
                                    memory="{}G".format(config['vcfanno']['max_mem']))

        # Create workflow from created jobs
        root_job.addChild(vcfanno_job)
    # Start workflow execution
    Job.Runner.startToil(root_job, args)
