# Microfish

**under development!**

### Large File Storage
**Important** This repo uses Github Large File Storage (lfs) for some of the data! You may need to [install and configure](https://git-lfs.github.com/) for the clone to work properly.

### Running

Without Docker

      cd microfish
      python index.py


With Docker

      git clone http://www.github.com/vsoch/microfish
      cd microfish
      docker-compose up -d


Then go to http://127.0.0.1:5000/ in your browser.


### About the Visualization
I parsed ~5000 publications and associated authors from the Microsoft Research site, and mapped each abstract into a [vector space](models/methods_word2vec.tsv) derived from [descriptions of methods](https://github.com/vsoch/repofish/tree/master/analysis/wikipedia#step-1-develop-vector-representations-of-methods). I could then calculate similarity of each paper to the [methods themselves](models/method_vectors.tsv) based on the context and words in the paper text and methods descriptions, respectively. While it would have been ideal to use the DOI associated with the papers to obtain full text, I only had an afternoon to put this together, and opted for this quicker method.
