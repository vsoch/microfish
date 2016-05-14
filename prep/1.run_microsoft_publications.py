from glob import glob
import json
import time
import pandas
import requests
import numpy
import pickle
import os
import re

home = os.environ["HOME"]
base = "%s/DATA/PUBMED" %os.environ["SCRATCH"]
outfolder = "%s/methods/microsoft" %(base)
scripts = "%s/SCRIPT/python/microfish" %(home)
rundir = "%s/methods" %(scripts)

# We will extract publication (abstracts) from Microsoft pages
pages = range(1,521)

words_vectors = "%s/models/vectors/methods_word2vec.tsv" %scripts
methods_vectors = "%s/models/method_vectors.tsv" %scripts

if not os.path.exists(outfolder):
    os.mkdir(outfolder)

for page_number in pages:
    output_file = "%s/page_%s_methods_match.tsv" %(outfolder,page_number)
    if not os.path.exists(output_file):
        job_id = "%s" %(page_number)
        jobfile = "%s/wikipedia/.job/%s.job" %(scripts,job_id)
        filey = open(jobfile,"w")
        filey.writelines("#!/bin/bash\n")
        filey.writelines("#SBATCH --job-name=%s\n" %(job_id))
        filey.writelines("#SBATCH --output=.out/%s.out\n" %(job_id))
        filey.writelines("#SBATCH --error=.out/%s.err\n" %(job_id))
        filey.writelines("#SBATCH --time=1:00:00\n")
        filey.writelines("#SBATCH --mem=4000\n")
        filey.writelines("module load python/2.7.5\n")
        filey.writelines("python %s/prep/1.microsoft_publications.py %s %s %s %s\n" %(scripts,page_number,outfolder,words_vectors,methods_vectors))
        filey.close()
        os.system("sbatch -p russpold --qos=russpold " + "%s/prep/.job/%s.job" %(scripts,job_id))



# Or just run with breaks!
for page_number in pages:
    output_file = "%s/page_%s_methods_match.tsv" %(outfolder,page_number)
    if not os.path.exists(output_file):
        os.system("sbatch -p russpold --qos=russpold " + "%s/prep/.job/%s.job" %(scripts,page_number))

