---
permalink: /publications/
title: "Publications"
---

{% comment %}
  _data/publications.json is generated from PubMed by scripts/fetch_publications.py
  (monthly, via a pull request). Don't edit it by hand: curate in
  _data/publication_overrides.yml instead.
{% endcomment %}
{% assign by_year = site.data.publications | group_by: "year" %}

<p class="pub-intro">Lab members are shown in bold. Papers are also listed on <a href="https://pubmed.ncbi.nlm.nih.gov/?term=%22Manglik%2C+Aashish%22%5BFull+Author+Name%5D">PubMed</a>.</p>

<nav class="pub-years" aria-label="Jump to year">
{%- for group in by_year %}<a data-scroll-ignore href="#{{ group.name }}">{{ group.name }}</a>{% endfor -%}
</nav>

{% for group in by_year %}
<h2 class="pub-year" id="{{ group.name }}">{{ group.name }}</h2>

{% for pub in group.items %}{% include publication.html pub=pub %}{% endfor %}
{% endfor %}
