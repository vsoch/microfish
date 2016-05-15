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

# We can't deal with author name disambiguation for now - I even see some spelling mistakes :/
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

collaborations.to_csv("%s/author_collaborations.tsv" %outfolder,sep="\t")

# Who has the most?
#collaborations.sum()[collaborations.sum()==274] / 2
#David Heckerman    137
#dtype: int64

# Mean
# 0.0015010968734855959
# collaborations.sum()[collaborations.sum()!=0].mean() /2
# Of those that have collaborations, mean is...
# 7.7502379190017976

# GRAPHISTRY VISUALIZATION ###############################################
df = pandas.DataFrame(columns=["source","target","value"])

count=1
thresh=0.9
seen = []
for row in collaborations.iterrows():
    author1_name = row[0]
    print "Parsing author %s, %s" %(author1_name,count)
    similar_authors = row[1][row[1].abs() >= thresh]
    for author2_name,v in similar_authors.iteritems():
        pair_id = "_".join(numpy.sort([author1_name,author2_name]))
        if author2_name != author1_name and pair_id not in seen:
            seen.append(pair_id)
            df.loc[count] = [author1_name,author2_name,v] 
            count+=1

# Make a lookup
alookup = dict()
unique_authors = numpy.unique(df["source"].tolist() + df["target"].tolist()).tolist()
for u in range(len(unique_authors)):
    alookup[unique_authors[u]] = unique_authors[u].decode('utf-8').encode('ascii',errors='replace').replace('?',' ')
    
# Replace sources and targets with lookups
sources = [alookup[x] for x in df["source"]]
targets = [alookup[x] for x in df["target"]]
df2=pandas.DataFrame()

df2["source"] = sources
df2["target"] = targets
df2["value"] = df["value"]
# [36647 rows x 3 columns]
df2.to_csv("%s/author_sims_graphistry_pt9.csv" %outfolder,index=False,encoding='utf-8')
