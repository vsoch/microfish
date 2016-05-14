from glob import glob
import itertools
import pandas
import numpy
import json
import os
import re

home = os.environ["HOME"]
base = "%s/DATA/PUBMED" %os.environ["SCRATCH"]
infolder = "%s/methods/microsoft" %(base)
outfolder = "%s/results" %(infolder)

if not os.path.exists(outfolder):
    os.mkdir(outfolder)

data_files = glob("%s/*.tsv" %infolder)
len(data_files)
# 492 - out of ~520 is ok

meta = dict()
results = pandas.DataFrame()

def convert_utf8(entry):
    return {"abstract":entry["abstract"].encode('utf-8'),
            "title":entry["title"].encode('utf-8'),
            "date":entry["date"].encode('utf-8'),
            "url":entry["url"].encode('utf-8'),
            "authors":entry["authors"].encode('utf-8')}
                

def parse_authors(entry):
    author_list = [x.replace("and","").strip() for x in entry['authors'].split(',')]   
    # The last author has a date appended!
    author_list[-1] = re.sub("[0-9]+","",author_list[-1])
    author_list[-1] = "".join(re.findall('[A-Z][^A-Z]*', author_list[-1])[:-1])
    # Some authors are missing commas between the names, eg A. Aiken   M. Fähndrich
    author_list = list(itertools.chain(*[x.split("  ") for x in author_list]))
    # Don't include authors that are just a first initial or ''
    return [x.replace(".","").strip(" ") for x in author_list if len(x.strip(" ")) > 2] 


for i in range(len(data_files)):
    data_file = data_files[i]
    page_number = os.path.basename(data_file).split("_")[1]
    meta_file = "%s/page_%s_methods_meta.json" %(infolder,page_number)
    if os.path.exists(meta_file):
        print "Parsing page number %s" %(page_number)
        meta_result = json.load(open(meta_file,'r'))
        result = pandas.read_csv(data_file,sep="\t",index_col=0)
        # Only add those we have meta data for
        for mid,entry in meta_result.iteritems():
            if int(mid) in result.index:
                entry = convert_utf8(entry)
                meta[str(mid)] = entry
        results = results.append(result)
    
# We have duplicated results, interesting
results = results.drop_duplicates()
keepers = [x for x in meta.keys() if int(x) in results.index]
meta = { k: meta[k] for k in keepers }

# Not sure why drop_duplicates is missing an entry
duplicated = results.loc[140569]
duplicated.index = ['one','two']
results = results.drop([140569])
results.loc[140569] = duplicated.loc['one']

len(meta)
# 7957
len(results)
# 7957
# good!

# Let's make a data frame of authors by papers, for easy lookup
authors = []
for mid,entry in meta.iteritems():
    authors = authors + parse_authors(entry)

len(authors)
# 28332
authors = numpy.unique(authors).tolist()
len(authors)
# 9882

# We can't deal with author name disambiguation for now
lookup = pandas.DataFrame(0,index=authors,columns=meta.keys())
for mid,entry in meta.iteritems():
    author_list = parse_authors(entry)
    lookup.loc[author_list,mid] = 1     

# Save things to file
lookup.to_csv("%s/author_lookup.tsv" %outfolder,sep="\t")
metadf = pandas.DataFrame(meta).transpose()
metadf.to_csv("%s/microsoft_meta.tsv" %outfolder,sep="\t")
results.to_csv("%s/microsoft_pubs.tsv" %outfolder,sep="\t")

# Make collaborations table
collaborations = pandas.DataFrame(0,columns=lookup.index,index=lookup.index)
for author,row in lookup.iterrows():
    print "Parsing author %s" %(author)
    pubs = row[row==1].index.tolist()
    coauthors = lookup[pubs].sum(axis=1)
    coauthors = [x for x in coauthors[coauthors==1].index.tolist() if x!=author]
    if len(coauthors) > 0:
        collaborations.loc[author,coauthors] = collaborations.loc[author,coauthors] + 1
        collaborations.loc[coauthors,author] = collaborations.loc[coauthors,author] + 1

collaborations_df = pandas.DataFrame(columns=["source","target","value"])
