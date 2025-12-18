---
date_created: {{ date_created }}
tags:
links:
---
{{ content }}
#### References
*{{ source_title }}*, locs {% for loc in locations %}[[{{ source_title }}#Loc {{ loc }}|Page {{ loc }}]]{{ ", " if not loop.last else "" }}{% endfor %}