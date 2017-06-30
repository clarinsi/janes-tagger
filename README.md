# janes-tagger

Tool for tagging and lemmatising non-standard Slovene (Croatian and Serbian to follow).

For now only using the pretrained model is possible.

The input text should be pairs of original and normalised forms separated by tab (additional attributes allowed), with empty lines as sentence separators. You can control for the position of the original and normalised token in the tab-separated format by setting the ```index1``` and ```index2``` parameters.

You can add lemmatisation via the ```-l``` flag.

```
$ python tagger.py -l --index1 2 --index2 1 sl < example.txt
jaz	Jst	Pp1-sn	jaz
ne vem	nevem	Q Vmpr1s	ne vedeti
kaj	kva	Pq-nsa	kaj
boš	boš	Va-f2s-n	biti
naredil	naredu	Vmep-sm	narediti
,	,	Z	,
pizda	pizda	Ncfsn	pizda
.	.	Z	.
```
