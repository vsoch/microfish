from repofish.nlp import processText, unicode2str
from repofish.utils import save_txt, save_json
from BeautifulSoup import BeautifulSoup
from glob import glob
import requests
import tempfile
import pandas
import pickle
import numpy
import json
import sys
import os
import re

page_number = sys.argv[1]
output_dir = sys.argv[2]
words_vectors = sys.argv[3]
methods_vectors = sys.argv[4]

base_url = "http://research.microsoft.com/apps/catalog/default.aspx?p=%s&sb=no&ps=25&t=publications"

# This is a data frame of methods vectors, derived from word2vec model
methods = pandas.read_csv(methods_vectors,sep="\t",index_col=0)
embeddings = pandas.read_csv(words_vectors,sep="\t",index_col=0)

# We will save a data frame of methods and similarity scores for each xml text, with PMID as index
sim = pandas.DataFrame(columns=methods.index)

### FUNCTIONS ########################################################################

def text2mean_vector(paragraph,vectors):
    '''text2mean_vector maps a new text (paragraph) onto vectors (a word2vec word embeddings model) by taking a mean of the vectors that are words in the text
    :param text: the text to parse
    :param vectors: a pandas data frame of vectors, index should be words in model
    '''
    words = processText(paragraph)
    words = [unicode2str(w) for w in words]
    words = [w for w in words if w in vectors.index.tolist()]
    if len(words) != 0:
        return vectors.loc[words].mean().tolist()
    return None


### ANALYSIS ##########################################################################

url = base_url %page_number
text = requests.get(url).text
soup = BeautifulSoup(text)
papers = soup.findAll("div", {"class": "name"})

output_file = "%s/page_%s_methods_match.tsv" %(output_dir,page_number)
output_meta = "%s/page_%s_methods_meta.json" %(output_dir,page_number)

meta_data = dict()

if not os.path.exists(output_file):

    for p in range(len(papers)):
        paper = papers[p]
        try:
            print "Parsing paper %s" %(p)
            link = paper.findChild()
            link = link.get('href')
            article_id = int(link.split("=")[-1])
            full_url = "http://research.microsoft.com%s" %link
            page = BeautifulSoup(requests.get(full_url).text)
            # Parse page into abstract, title, authors, date
            authors = page.find("div",{'id':'pubDeTop'}).find("p").text
            title = page.find("div",{'class':'title'}).text
            date = page.find("span",{"class":"byLine"}).text
            abstract = " ".join([x.text for x in page.find("div",{"class":"fl"}).findAll("p")]).encode('utf-8')
            # Save meta data for article
            meta_data[article_id] = {"abstract":abstract,
                                     "authors":authors,
                                     "title":title,
                                     "date":date,
                                     "url":full_url}
            vector = text2mean_vector(abstract,embeddings)
            if vector != None:
                # Compare vector to all methods
                comparison = methods.copy()
                comparison.loc["COMPARATOR"] = vector
                comparison = comparison.T.corr()     
                result = comparison.loc["COMPARATOR"]       
                result = result.drop(["COMPARATOR"])
                # Save scores to df
                sim.loc[article_id,result.index] = result
        except:
            print "Error with %s" %(p)
            pass

    # Save to output folder based on the page number
    if sim.shape[0] > 0:
        sim.to_csv(output_file,sep="\t")
        save_json(meta_data,output_meta)
