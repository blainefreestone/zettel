{%- for loc, items in data.items() %}
### Loc {{ loc }}
{%- for item in items %}
{%- if item.type == 'highlight' %}
**Highlight** {{ item.content }}
{%- elif item.type == 'note' %}

**Note** {{ item.transcription.transcription }}
{%- endif %}
{%- endfor %}

---

{%- endfor %}