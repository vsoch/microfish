from flask import Flask, render_template, request
import random
import numpy
import pandas
import pickle

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
    pub_ids = app.authors.loc[author][authors.loc[author]!=0].index.tolist()
    pub_meta = app.meta.loc[[int(x) for x in pub_ids]].to_dict(orient="records")
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()
    return render_template("index.html",methods=methods,
                                        authors=authors)


if __name__ == "__main__":
    app.debug = True
    app.run()

