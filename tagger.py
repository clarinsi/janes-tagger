#!/usr/bin/python
#-*-coding:utf8-*-

import warnings
warnings.filterwarnings("ignore")

import sys
import os
reldir=os.path.dirname(os.path.abspath(__file__))

from train_tagger import extract_features_msd
from train_lemmatiser import extract_features_lemma
from subprocess import Popen, PIPE
import cPickle as pickle
from StringIO import StringIO
import pycrfsuite
from sklearn.feature_extraction import DictVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

def tag_sent(sent):
  return tagger.tag(extract_features_msd(sent,trie,brown,normdict))

def tag_lemmatise_sent(sent1,sent2):
  return [(a,get_lemma(b,c,a)) for a,b,c in zip(tag_sent(sent1),sent1,sent2)]

def get_lemma(token1,token2,msd):
  lexicon=lemmatiser['lexicon']
  token1=token1.split(' ')
  token2=token2.split(' ')
  msd=msd.split(' ')
  for token in (token1,token2):
    out=[]
    if len(token)==len(msd):
      for t,m in zip(token,msd):
        key=t.lower()+'_'+m
        if unicode(key) in lexicon:
          out.append(lexicon[key][0].decode('utf8'))
      if len(token)==len(out):
        return ' '.join(out)
  
  #key1=token1.lower()+'_'+msd
  #key2=token2.lower()+'_'+msd
  #for key in (key1,key2):
  #  if key in lexicon:
  #    return lexicon[key][0].decode('utf8')
  #if msd[:2]!='Np':
  #  for i in range(len(msd)-1):
  #    for key in lexicon.keys(key1[:-(i+1)]):
  #      return lexicon[key][0].decode('utf8')
  return guess_lemma(' '.join(token1),' '.join(msd))

def guess_lemma(token,msd):
  if len(token)<3:
    return apply_rule(token,"(0,'',0,'')",msd)
  model=lemmatiser['model']
  if msd not in model:
    return token
  else:
    lemma=apply_rule(token,model[msd].predict(extract_features_lemma(token))[0],msd)
    if len(lemma)>0:
      return lemma
    else:
      return token

def suffix(token,n):
  if len(token)>n:
    return token[-n:]
      
def apply_rule(token,rule,msd):
  rule=list(eval(rule))
  if msd:
    if msd[:2]=='Np':
      lemma=token
    else:
      lemma=token.lower()	
  else:
    lemma=token.lower()
  rule[2]=len(token)-rule[2]
  lemma=rule[1]+lemma[rule[0]:rule[2]]+rule[3]
  return lemma

def read_and_write(istream,index1,index2,ostream):
  entry_list=[]
  sents=[]
  for line in istream:
    if line.strip()=='':
      totag=[]
      tonorm=[]
      for token,norm in [(e[index1],e[index2]) for e in entry_list]:
        if ' ' in token:
          if len(token)>1:
            totag.extend(token.split(' '))
            if len(token.split(' '))==len(norm.split(' ')):
              tonorm.extend(norm.split(' '))
            else:
              tonorm.append(norm)
              for i in range(len(token.split(' '))-1):
                tonorm.append('')
        else:
          totag.append(token)
          tonorm.append(norm)
      tag_counter=0
      if lemmatiser==None:
        tags=tag_sent(totag)
        tags_proper=[]
        for token in [e[index1] for e in entry_list]:
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
      else:
        tags=tag_lemmatise_sent(totag,tonorm)
        tags_proper=[]
        for token in [e[index1] for e in entry_list]:
          if ' ' in token:
            if len(token)==1:
              tags_proper.append([' ',' '])
            else:
              tags_temp=tags[tag_counter:tag_counter+token.count(' ')+1]
              tag=' '.join([e[0] for e in tags_temp])
              lemma=' '.join([e[1] for e in tags_temp])
              tags_proper.append([tag,lemma])
              tag_counter+=token.count(' ')+1
          else:
            tags_proper.append(tags[tag_counter])
            tag_counter+=1
        ostream.write(''.join(['\t'.join(entry)+'\t'+tag[0]+'\t'+tag[1]+'\n' for entry,tag in zip(entry_list,tags_proper)])+'\n')
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
  lemmatiser={'model':pickle.load(open(os.path.join(reldir,lang+'.lexicon.guesser'))),'lexicon':pickle.load(open(os.path.join(reldir,lang+'.lexicon')))}

if __name__=='__main__':
  import argparse
  parser=argparse.ArgumentParser(description='Tagger and lemmatiser of non-standard Slovene (Croatian and Serbian to follow)')
  parser.add_argument('lang',help='language of the text',choices=['sl'])#,'hr','sr'])
  parser.add_argument('-l','--lemmatise',help='perform lemmatisation as well',action='store_true')
  parser.add_argument('-i1','--index1',help='index of the column containing the original form',type=int,default=1)
  parser.add_argument('-i2','--index2',help='index of the column containing the normalised form',type=int,default=2)
  args=parser.parse_args()
  trie=pickle.load(open(os.path.join(reldir,args.lang+'.marisa')))
  brown=dict([(e[1].decode('utf8'),e[0]) for e in [e.split('\t') for e in open(args.lang+'.brown')]])
  normdict={}
  for orig,norm in zip(open(args.lang+'.orig'),open(args.lang+'.norm')):
    if orig==norm:
      continue
    orig=orig.decode('utf8').strip()
    norm=norm.decode('utf8').strip()
    if orig not in normdict:
      normdict[orig]=set()
    normdict[orig].add(norm)
  tagger=pycrfsuite.Tagger()
  tagger.open(os.path.join(reldir,args.lang+'.msd.model'))
  if args.lemmatise:
    lemmatiser={'model':pickle.load(open(os.path.join(reldir,args.lang+'.lexicon.guesser'))),'lexicon':pickle.load(open(os.path.join(reldir,args.lang+'.lexicon')))}
  else:
    lemmatiser=None
  read_and_write(sys.stdin,args.index1-1,args.index2-1,sys.stdout)
