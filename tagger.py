#!/usr/bin/python
#-*-coding:utf8-*-

import warnings
warnings.filterwarnings("ignore")

import sys
import os
reldir=os.path.dirname(os.path.abspath(__file__))

from train_tagger import extract_features_msd
from subprocess import Popen, PIPE
import cPickle as pickle
from StringIO import StringIO
import pycrfsuite

def tag_sent(sent):
  return tagger.tag(extract_features_msd(sent,trie,brown,normdict))

def read_and_write(istream,index,ostream):
  entry_list=[]
  sents=[]
  for line in istream:
    if line.strip()=='':
      totag=[]
      for token in [e[index] for e in entry_list]:
        if ' ' in token:
          if len(token)>1:
            totag.extend(token.split(' '))
        else:
          totag.append(token)
      tag_counter=0
      tags=tag_sent(totag)
      tags_proper=[]
      for token in [e[index] for e in entry_list]:
        if ' ' in token:
          if len(token)==1:
            tags_proper.append(' ')
          else:
            tags_proper.append(' '.join(tags[tag_counter:tag_counter+token.count(' ')+1]))
            tag_counter+=token.count(' ')+1
        else:
          tags_proper.append(tags[tag_counter])
          tag_counter+=1
      ostream.write(u''.join(['\t'.join(entry)+'\t'+tag+'\n' for entry,tag in zip(entry_list,tags_proper)])+'\n')
      entry_list=[]
    else:
      entry_list.append(line[:-1].decode('utf8').split('\t'))

def load_models(lang,dir=None):
  global trie
  global tagger
  global lemmatiser
  if dir!=None:
    reldir=dir
  trie=pickle.load(open(os.path.join(reldir,lang+'.marisa')))
  tagger=pycrfsuite.Tagger()
  tagger.open(os.path.join(reldir,lang+'.msd.model'))

if __name__=='__main__':
  import argparse
  parser=argparse.ArgumentParser(description='Tagger of non-standard Slovene (Croatian and Serbian to follow)')
  parser.add_argument('lang',help='language of the text',choices=['sl'])#,'hr','sr'])
  parser.add_argument('-i','--index',help='index of the column to be processed',type=int,default=0)
  args=parser.parse_args()
  trie=pickle.load(open(os.path.join(reldir,args.lang+'.marisa')))
  brown=dict([(e[1].decode('utf8'),e[0]) for e in [e.split('\t') for e in open('brown.janeslwac')]])
  normdict={}
  for orig,norm in zip(open('janesnorm.orig'),open('janesnorm.norm')):
    if orig==norm:
      continue
    orig=orig.decode('utf8').strip()
    norm=norm.decode('utf8').strip()
    if orig not in normdict:
      normdict[orig]=set()
    normdict[orig].add(norm)
  tagger=pycrfsuite.Tagger()
  tagger.open(os.path.join(reldir,args.lang+'.msd.model'))
  read_and_write(sys.stdin,args.index-1,sys.stdout)
