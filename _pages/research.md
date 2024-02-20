---
permalink: /research/
title: "Research"
---

{% assign interests = site.research | sort: "index" %}

{% for interest in interests %}
## {{ interest.name }}

{% assign parity = interest.index | modulo:2 %}
{% if parity == 0 %}
{% assign alignment = "right" %}
{% else %}
{% assign alignment = "left" %}
{% endif %}

![{{interest.image_alt}}]({{interest.image}}){:style="float: {{alignment}}; object-fit: contain; width: 30%; max-height: 8em; margin-left: 1em; margin-right: 1em;"}

{{ interest.content }}
{% endfor %}
