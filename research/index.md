---
title: Research
layout: single
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

![{{interest.image_alt}}]({{interest.image}}){:style="float: {{alignment}};width: 300px;"}

{{ interest.content }}
{% endfor %}
