#!/usr/bin/python
#-*-coding:utf8-*-

import sys
import re
import codecs
import cPickle as pickle
import pycrfsuite

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

def conll_iter(stream):
  sent=[]
  for line in stream:
    if line.strip()=='':
      yield sent
      sent=[]
    else:
      sent.append(line.decode('utf8').strip().split('\t'))

def packed_shape(token,index):
  packed=''
  for char in token:
    if char.isupper():
      packed+='u'
    elif char.islower():
      packed+='l'
    elif char.isdigit():
      packed+='d'
    else:
      packed+='x'
  if index==0:
    packed+='_START'
  return re.sub(r'(.)\1{2,}',r'\1\1',packed)

def islcase(token):
  return token.lower()==token

def isnum(token):
  import re
  return re.search(r'\d',token)!=None

def transnum(token):
  import re
  return re.sub(r'\d','D',token)

def remrep(token):
  import re
  return re.sub(r'(.)\1\1+',r'\1\1',token)

def wpos(sent,index):
  if index>=0 and index<len(sent):
    return remrep(transnum(sent[index].lower()))

def wsuf(token,length):
  if token==None:
    return
  if len(token)>length:
    token=transnum(token.lower())
    return token[-length:]

def decode(s):  
  return ''.join(s).strip('0')

def reverse(s):
  t=''
  for u in s:
    t=u+t
  return t

def search_full(token,trie):
  token=reverse(u'_'+token)
  if token in trie:
    return [decode(e) for e in trie[token]]

def escape_colon(text):
  return text.replace('\\','\\\\').replace(':','\\:')

def extract_features_msd(sent,trie,brown,normdict):
  full_sent=[]
  suffix_sent=[]
  for index,token in enumerate(sent):
    full_sent.append(search_full(wpos(sent,index),trie))
  features=[]
  for index,token in enumerate(sent):
    tfeat=[]
    tfeat.append('w[0]='+wpos(sent,index))
    tfeat.append('packed_shape='+packed_shape(token,index))
    for i in range(3): #w[-1] w[1]
      if wpos(sent,index-i-1)!=None:
        tfeat.append('w['+str(-i-1)+']='+wpos(sent,index-i-1))
      if wpos(sent,index+i+1)!=None:
        tfeat.append('w['+str(i+1)+']='+wpos(sent,index+i+1))
    for i in range(4): #w[0] suffix
      if wsuf(wpos(sent,index),i+1)!=None:
        tfeat.append('s['+str(i+1)+']='+wsuf(wpos(sent,index),i+1))
    if full_sent[index]!=None:
      for msd in full_sent[index]:
        tfeat.append('msd='+msd)
    if full_sent[index]!=None:
      tfeat.append('inlexicon=True')
    else:
      tfeat.append('inlexicon=False')
    """
    if wpos(sent,index).startswith('http:'):
      tfeat.append('link=True')
    if wpos(sent,index).startswith('#'):
      tfeat.append('hash=True')
    if wpos(sent,index).startswith('@'):
      tfeat.append('mention=True')
    """
    for i in range(2):
      if wpos(sent,index-i-1)!=None:
        msds=full_sent[index-i-1]
        if msds!=None:
          for msd in msds:
            tfeat.append('msd[-'+str(i+1)+']='+msd)#+':'+str(float(msds[msd])/sum(msds.values())))
      if wpos(sent,index+i+1)!=None:
        msds=full_sent[index+i+1]
        if msds!=None:
          for msd in msds:
            tfeat.append('msd['+str(i+1)+']='+msd)#+':'+str(float(msds[msd])/sum(msds.values())))
    if wpos(sent,index) in brown:
      path=brown[wpos(sent,index)]
      for end in range(2,len(path)+1,2):
        tfeat.append('brown['+str(end)+']='+path[:end])
    if wpos(sent,index) in normdict:
      msds=[]
      for norm in normdict[wpos(sent,index)]:
        normsds=search_full(norm,trie)
        if normsds!=None:
          msds.extend(normsds)
      if msds!=[]:
        for msd in set(msds):
          tfeat.append('msdnorm[0]='+msd)
    if index==0:
      tfeat.append('__BOS__')
    elif index+1==len(sent):
      tfeat.append('__EOS__')
    features.append(tfeat)
  return features

if __name__=='__main__':
  lang=sys.argv[1]
  trie=pickle.load(open('sl.marisa'))
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
  trainer=pycrfsuite.Trainer(algorithm='pa',verbose=True)
  trainer.set_params({'max_iterations':10})
  for sent in conll_iter(open(lang+'.conll')):
    tokens=[e[1] for e in sent]
    try:
      labels=[e[4] for e in sent]
    except:
      print tokens
    feats=extract_features_msd(tokens,trie,brown,normdict)
    trainer.append(feats,labels)
  trainer.train(lang+'.msd.model')
