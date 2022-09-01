---
permalink: /publications/
title: "Publications"
---

{% assign posts = site.posts %}

{% for article in posts %}
{% if article.publication %}
### {{article.title}}
{% assign length = article.authors | size %}
{% assign i = 2 %}
{% for author in article.authors %}{{author}}{%if i < length%}, {%elsif i == length%}{%if length > 2%},{%endif%} and {%else%}{%endif%}{%assign i = i | plus: 1%}{% endfor %}

Published in {%if article.doi%}[*{{article.journal}}* {{article.citation}}](https://doi.org/{{article.doi}}){%else%}*{{article.journal}}* {{article.citation}}{%endif%}.

{% if article.pdbs %}
{% assign length = article.pdbs | size %}
PDB{%if length > 1%}s{%endif%}: {% for pdb in article.pdbs %} [{{pdb}}](https://doi.org/10.2210/pdb{{pdb}}/pdb){% endfor %}
{% endif %}
<hr>
{% endif %}
{% endfor %}

# All articles and reviews

[Pubmed](http://www.ncbi.nlm.nih.gov/pubmed/?term=aashish+manglik)
