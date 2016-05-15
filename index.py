from flask import Flask, render_template, request
from random import choice
import itertools
import random
import numpy
import pandas
import pickle
import re

# SERVER CONFIGURATION ##############################################
class MicroServer(Flask):

    def __init__(self, *args, **kwargs):
            super(MicroServer, self).__init__(*args, **kwargs)

            # load data on start of application
            self.authors = pandas.read_csv("data/author_lookup.tsv",sep="\t",index_col=0)
            self.pubs = pandas.read_csv("data/microsoft_pubs.tsv",sep="\t",index_col=0)
            self.meta = pandas.read_csv("data/microsoft_meta.tsv",sep="\t",index_col=0)
            self.pubs.columns = [x.decode('utf-8').encode('ascii',errors='replace').replace('?',' ') for x in self.pubs.columns.tolist()]
            self.authors.index = [x.decode('utf-8').encode('ascii',errors='replace').replace('?',' ') for x in self.authors.index.tolist()]

            # D3 specific variables
            self.width = 1500
            self.height = 600
            self.padding = 12
            self.maxRadius = 12
          
app = MicroServer(__name__)

# Global variables and functions

def parse_unicode(meta):
    '''parse_unicode: decodes to utf-8 and encodes in ascii, replacing weird characters with empty space.
    :param meta: a dictionary or list of dictionaries to parse
    '''
    if not isinstance(meta,list):
        meta = [meta]

    parsed = []
    for entry in meta:
        new_entry = dict()
        for key,value in entry.iteritems():
            if key == "authors":
                authors = value.decode('utf-8').encode('ascii',errors='replace').replace('?',' ')
                new_entry[key] = ", ".join(parse_authors(authors))
            elif key == "url": # Don't want to replace ? with space
                new_entry[key] = value.decode('utf-8').encode('ascii',errors='replace')                 
            else:
                new_entry[key] = value.decode('utf-8').encode('ascii',errors='replace').replace('?',' ')
        parsed.append(new_entry)
    return parsed


def parse_authors(entry):
    '''parse_authors: takes a meta entry, and removes date from the last author name, along with
    empty entries
    :param entry: a string of author names
    '''
    author_list = [x.replace("and","").strip() for x in entry.split(',')]   
    # The last author has a date appended!
    author_list[-1] = re.sub("[0-9]+","",author_list[-1])
    author_list[-1] = "".join(re.findall('[A-Z][^A-Z]*', author_list[-1])[:-1])
    author_list = list(itertools.chain(*[x.split("  ") for x in author_list]))
    # Don't include authors that are just a first initial or ''
    return [x.replace(".","").strip(" ") for x in author_list if len(x.strip(" ")) > 2] 


def flatten(df,column_names=["article_id","method","score"]):
    '''flatten flattens a data frame - NOT IN USE - too slow
    :param df: the data frame to flatten
    '''
    count = 0
    flat = pandas.DataFrame(columns=column_names)
    for rowid,row in df.iterrows():
        for method,value in row.iteritems():
            flat.loc[count] = [rowid,method,value]
            count+=1
    return flat

def random_colors(concepts):
    '''Generate N random colors'''
    colors = {}
    for x in range(len(concepts)):
        concept = concepts[x]
        r = lambda: random.randint(0,255)
        colors[concept] = '#%02X%02X%02X' % (r(),r(),r())
    return colors


@app.route("/")
def index():
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()
    # For now, select a random author
    author = choice(authors)
    return base_author(author)
    #return render_template("index.html",methods=methods,
    #                                    authors=authors)

@app.route("/summary")
def summary_view():
    # What methods are being used?
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()
    return render_template("index.html",methods=methods,
                                        authors=authors)    

@app.route("/method",methods=['POST'])
def view_method():
    method = request.form["method"]
    print "Method is %s" %(method)
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()
    return render_template("index.html",methods=methods,
                                        authors=authors)


@app.route("/author",methods=['POST'])
def view_author():
    author = request.form["author"]
    print "Author is %s" %(author)

    return base_author(author)

def base_author(author):
    '''base_author is the base view to see an author, for temporary use while methods
    view isn't developed and we don't have this selection for the index
    '''
    # Prepare meta data about papers
    pub_ids = app.authors.loc[author][app.authors.loc[author]!=0].index.tolist()
    pub_meta = app.meta.loc[[int(x) for x in pub_ids]].to_dict(orient="records")
    pub_meta = parse_unicode(pub_meta)
    publications = app.pubs.loc[[int(x) for x in pub_ids]]
    publications.isnull()

    # What methods does the author most strongly match to?
    ranked_methods = publications.mean()
    ranked_methods.sort_values(inplace=True,ascending=False)
    ranked_methods = ranked_methods[ranked_methods.isnull()==False]
    ranked_methods = ranked_methods.to_dict()

    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()
    return render_template("author.html",methods=methods,
                                         author=author,
                                         authors=authors,
                                         ranked_methods=ranked_methods,
                                         pubs_meta=pub_meta,
                                         publications=publications.to_dict(orient="records"))


if __name__ == "__main__":
    app.debug = True
    app.run()

