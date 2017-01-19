# janes-tagger

Tool for tagging non-standard Slovene (Croatian and Serbian to follow).

For now only using the pretrained model is possible. The input text should be verticalised with empty lines as sentence separators.

```
$ python tagger.py sl < example.txt
Jst	Pp1-sn
nevem	Q Vmpr1s
kva	Pq-nsa
boš	Va-f2s-n
naredu	Vmep-sm
,	Z
pizda	Ncfsn
.	Z
```
