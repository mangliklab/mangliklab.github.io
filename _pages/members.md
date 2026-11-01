---
title: Members
permalink: /members/
layout: single
---

{% comment %}
  Current members are grouped by their "bio" field in _data/authors.yml:
  it mentions a professor, a postdoc, or a graduate student; anyone else is Staff.
{% endcomment %}
{% assign groups = "PI,Postdocs,Graduate students,Staff" | split: "," %}

{% for group in groups %}
{% capture cards %}
{% for author in site.data.authors %}
{% assign member = author[1] %}
{% if member.member %}
{% if member.current %}

{% assign role = member.bio | downcase %}
{% assign member_group = "Staff" %}
{% if role contains "professor" %}
{% assign member_group = "PI" %}
{% elsif role contains "postdoc" %}
{% assign member_group = "Postdocs" %}
{% elsif role contains "graduate" %}
{% unless role contains "undergraduate" %}
{% assign member_group = "Graduate students" %}
{% endunless %}
{% endif %}

{% if member_group == group %}

## {{ member.name }}

{% if member.avatar %}
![Photograph of {{member.name}}]({{member.avatar}}){:style="float: left; object-fit: contain; object-position: left top; width: 30%; max-height: 12em; margin: 0 1.5em 1em 0;"}
{% endif %}

{% if member.bio %}
**{{ member.bio }}**
{% endif %}

{% capture links %}
{%- if member.email %} · Email: <a href="mailto:{{ member.email }}">{{ member.email }}</a>{% endif -%}
{%- if member.website %} · <a href="{{ member.website }}">Personal website</a>{% endif -%}
{%- if member.twitter %} · Twitter: <a href="https://twitter.com/{{ member.twitter }}">@{{ member.twitter }}</a>{% endif -%}
{%- if member.gscholar %} · <a href="{{ member.gscholar }}">Google Scholar</a>{% endif -%}
{% endcapture %}
{% assign links = links | strip | remove_first: "· " %}
{% if links != "" %}<p>{{ links }}</p>{% endif %}

{{ member.fullbio }}

<div style="clear: both;"></div>

{% endif %}

{% endif %}
{% endif %}
{% endfor %}
{% endcapture %}

{% assign cards = cards | strip %}
{% if cards != "" %}
{% unless group == "PI" %}
# {{ group }}
{% endunless %}

{{ cards }}
{% endif %}
{% endfor %}

# Former members


{% for author in site.data.authors %}
{% assign member = author[1] %}
{% if member.member %}
{% unless member.current %}

### {{ member.name }}

**{{ member.bio }}**{% if member.start %} ({{ member.start }}{% if member.end %}&ndash;{{ member.end }}{% endif %}){% elsif member.end %} (until {{ member.end }}){% endif %}{% if member.next %}<br>Next: {{ member.next }}{% endif %}
{% endunless %}
{% endif %}
{% endfor %}

# Joining

We are actively recruiting highly motivated graduate students and postdoctoral fellows interested in problems at the intersection of transmembrane signaling, protein biophysics, and human disease.

Interested graduate students should apply to one of the UCSF graduate programs.

Postdoctoral fellows should contact Aashish directly with a CV, research proposal, and three references.
