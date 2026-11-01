Getting started
===============

 1. Install all [prerequisites](https://jekyllrb.com/docs/installation/)
 1. Install the jekyll and bundler gems
    ```
    gem install jekyll bundler
    ```
 1. Clone this repository
    ```
    git clone git@github.com:mangliklab/mangliklab.github.io.git
    ```
 1. Change into your new directory
    ```
    cd mangliklab.github.io
    ```
 1. Build the site and make it available on a local server
    ```
    bundle exec jekyll serve
    ```
 1. Browse to `http://localhost:4000`


Please test your changes locally before pushing.

See lab manual for instructions on how to add yourself to the website!

Publications
============

The Publications page is built from `_data/publications.json`, which is generated
from PubMed, with preprints also from Europe PMC; don't edit it by hand. On the 1st of each month a GitHub Action opens
a pull request with any new papers. Merge it to publish them. To update sooner,
open the Actions tab and run "Refresh publications".

Curation lives in `_data/publication_overrides.yml`: leave papers off, add ones the
search misses, list extra spellings of lab members' names, and adjust per-paper
details. Authors are bolded when they match someone in `_data/authors.yml`. PDB codes
are looked up automatically from RCSB, using each entry's primary citation.
