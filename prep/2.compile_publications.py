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

# Who has the most collaborations? Let's binarize to 1, so working with someone >1 doesn't
# give extra points!
collaborations_bin = collaborations.copy()
collaborations_bin[collaborations_bin!=0] = 1
ranked_collab = collaborations_bin.sum()
ranked_collab.sort_values(inplace=True,ascending=False)

#David Heckerman            137
#Matthew J Smith            122
#Jamie Shotton              120
#Jie Liu                    106
#Li Deng                    100
#Mary Czerwinski             96
#Antonio Criminisi           93
#Shahram Izadi               90
#Edward Cutrell              86
#Jaime Teevan                84
#Steve Hodges                83
#Jim Gray                    83
#Geoffrey Zweig              80
#Ranveer Chra                76
#Dong Yu                     76
#Xiaodong He                 74
#Bongshin Lee                74
#Jonathan M Carlson          74
#Wei-Ying Ma                 73
#Malcolm Slaney              72
#Wolfram Schulte             72
#Alex Acero                  72
#Pushmeet Kohli              71
#Richard Szeliski            70
#Thomas Moscibroda           69
#Abigail Sellen              69
#Ben Glocker                 69
#Dimitrios Lymberopoulos     69
#Ender Konukoglu             68
#Jianfeng Gao                68


# Who has the most publications?
leaders.sort_values(inplace=True,ascending=False)
leaders = leaders.index.tolist()
leader_counts = pandas.DataFrame(columns=["name","count"])

for leader in leaders:
    count = len(lookup.loc[leader][lookup.loc[leader]!=0].index)
    leader_counts.loc[leader] = [leader,count]

# Who has the most publications?
#leader_counts[leader_counts["count"]==leader_counts["count"].max()]
#Li Deng  Li Deng    149

leader_counts.sort_values(inplace=True,by=["count"],ascending=False)
leader_counts

#Li Deng                                      Li Deng    149
#Alex Acero                                Alex Acero    133
#Dong Yu                                      Dong Yu    107
#Yu Zheng                                    Yu Zheng     77
#Thomas Zimmermann                  Thomas Zimmermann     76
#Richard Szeliski                    Richard Szeliski     74
#Philip A Chou                          Philip A Chou     65
#Wei-Ying Ma                              Wei-Ying Ma     65
#Heung-Yeung Shum                    Heung-Yeung Shum     65
#Mary Czerwinski                      Mary Czerwinski     65
#Jie Liu                                      Jie Liu     63
#Jim Gray                                    Jim Gray     62
#Jaime Teevan                            Jaime Teevan     61
#Margus Veanes                          Margus Veanes     61
#Edward Cutrell                        Edward Cutrell     61
#Christopher M Bishop            Christopher M Bishop     57
#Surajit Chaudhuri                  Surajit Chaudhuri     57
#Benjamin Livshits                  Benjamin Livshits     57
#Jianfeng Gao                            Jianfeng Gao     57
#Paramvir Bahl                          Paramvir Bahl     57
#Yuri Gurevich                          Yuri Gurevich     56
#Shipeng Li                                Shipeng Li     54
#David Heckerman                      David Heckerman     54
#Dinei Florencio                      Dinei Florencio     53
#Abigail Sellen                        Abigail Sellen     53
#Nachiappan Nagappan              Nachiappan Nagappan     53
#Xiaodong He                              Xiaodong He     53
#Xing Xie                                    Xing Xie     53
#Eric Horvitz                            Eric Horvitz     51
#Yi-Min Wang                              Yi-Min Wang     51

# What about collaborations per publication?
leader_counts["collaborations"] = ranked_collab[leader_counts.index]
collabs_perpub = leader_counts["collaborations"]/leader_counts["count"]
collabs_perpub.sort_values(inplace=True,ascending=False)

#Tammy Riklin Raviv       67
#Nuno Sousa               67
#D Louis Collins          67
#Christopher R Durst      67
#Raj Jena                 67
#Owen M Thomas            67
#Carlos A Silva           67
#Senan Doyle              67
#Raphael Meier            67
#Cagatay Demiralp         67
#Yuliya Burren            67
#Rol Wiest                67
#Brian B Avants           67
#Doina Precup             67
#Andac Hamamci            67
#Duygu Sarikaya           67
#Nigel M John             67
#Patricia Buendia         67
#Michael Ryan             67
#Danial Lashkari          67
#Flor Vasseur             67
#Marcel Prastawa          67
#Jason J Corso            67
#Nicolas Cordier          67
#Lawrence Schwartz        67
#Nicholas Ayache          67
#Elizabeth Gerstner       67
#Nagesh K Subbanna        67
#Gabor Szekely            67
#Dong Hye Ye              67

# One paper with 68 authors! cheating! We would need to redo the collaborations
# matrix, and not include these outlier papers.

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
