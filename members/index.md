---
title: Members
layout: single
---

{% for member in site.members %}
{% if member.current %}
## {{ member.name }}

{% if member.image %}
![Photograph of {{member.name}}]({{member.image}}){:style="float: left;width: 250px;margin-right: 10px;"}
{% endif %}

{% if member.position %}
**{{ member.position }}**
{% endif %}

{% if member.email %}
[{{ member.email }}](mailto:{{ member.email }})
{% endif %}

{% if member.twitter %}
[@{{ member.twitter }}](https://twitter.com/{{ member.twitter }})
{% endif %}

{{ member.content }}

{% endif %}
{% endfor %}


# Former members

{% for member in site.members %}
{% unless member.current %}
## {{ member.name }}

{% if member.image %}
![Photograph of {{member.name}}]({{member.image}}){:style="float: left;width: 250px;margin-right: 10px;"}
{% endif %}

{% if member.position %}
**{{ member.position }}**
{% endif %}

{% if member.email %}
[{{ member.email }}](mailto:{{ member.email }})
{% endif %}

{% if member.twitter %}
[@{{ member.twitter }}](https://twitter.com/{{ member.twitter }})
{% endif %}

{{ member.content }}

{% endunless %}
{% endfor %}

