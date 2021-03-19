---
title: Publications
layout: single
---

{% assign articles = site.publications | reverse %}

{% for article in articles %}
## {{article.title}}

*{{article.journal}}* {{article.citation}}

{{article.authors}}

{% if article.doi %}
DOI: [{{article.doi}}](https://doi.org/{{article.doi}})
{% endif %}

{% if article.pdbs %}
PDB: {% for pdb in article.pdbs %} [{{pdb}}](https://doi.org/10.2210/pdb{{pdb}}/pdb) {% endfor %}
{% endif %}

{{article.content}}
{% endfor %}

# All articles and reviews

[Pubmed](http://www.ncbi.nlm.nih.gov/pubmed/?term=aashish+manglik)
