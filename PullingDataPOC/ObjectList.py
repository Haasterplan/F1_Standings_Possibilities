import numpy as np
import random
from math import sqrt

class ObjectList(list):
	#Class which allows for iteration through a list of custom objects
	def __init__(self,Vals=list()):
		self.Vals=Vals
	def __getitem__(self,items):
		if hasattr(items, '__iter__'):
			return list(self.Vals[item] for item in items)
		else:
			return self.Vals[items]
	def __getslice__(self,i,j):
		return ObjectList(list.__getslice__(self, i, j))
	def __repr__(self):
		return str('ObjectList {}'.format(self.Vals))
	def AddVal(self,val):
		self.Vals+=val
	def __iter__(self):
		return ObjectListIterator(self.Vals)
	def pull(self,attr):
		vals_list=[None]*len(self.Vals)
		ObjectListIterator=iter(self)
		i=0
		while True:
			try:
				vals_list[i]=getattr(next(ObjectListIterator),attr)
				i+=1
			except StopIteration:
				break
		return vals_list
	def sum(self,attr):
		ObjectListIterator=iter(self)
		res=0
		while True:
			try:
				res+=getattr(next(ObjectListIterator),attr)
			except StopIteration:
				break
		return res
	def mean(self,attr):
		return self.sum(attr)/len(self.Vals)
	def std(self,attr):
		mu=self.mean(attr)
		ObjectListIterator=iter(self)
		res=0
		while True:
			try:
				res+=(getattr(next(ObjectListIterator),attr)-mu)**2
			except StopIteration:
				break
		return sqrt(res/len(self.Vals))
	def med(self,attr):
		vals_list=[None]*len(self.Vals)
		ObjectListIterator=iter(self)
		i=0
		while True:
			try:
				vals_list[i]=getattr(next(ObjectListIterator),attr)
				i+=1
			except StopIteration:
				break
		return quickselect_median(vals_list)
	def sort(self,attr):
		sorted_order=self.argsort(attr)
		return ObjectList(ObjectList(self.Vals).__getitem__(sorted_order))
	def argsort(self,attr):
		sort_by=self.pull(attr)
		return sorted(range(len(sort_by)), key=sort_by.__getitem__)

class ObjectListIterator():
	def __init__(self,Expr):
		self.obj=Expr
		self.ind=-1
	def __next__(self):
		if self.ind<len(self.obj)-1:
			self.ind+=1
			return self.obj[self.ind]
		raise StopIteration


def quickselect_median(l, pivot_fn=random.choice):
	if len(l) % 2 == 1:
		return quickselect(l, len(l) // 2, pivot_fn)
	else:
		return 0.5 * (quickselect(l, len(l) / 2 - 1, pivot_fn) +
					  quickselect(l, len(l) / 2, pivot_fn))

def quickselect(l, k, pivot_fn):
	"""
	Select the kth element in l (0 based)
	:param l: List of numerics
	:param k: Index
	:param pivot_fn: Function to choose a pivot, defaults to random.choice
	:return: The kth element of l
	"""
	if len(l) == 1:
		assert k == 0
		return l[0]

	pivot = pivot_fn(l)

	lows = [el for el in l if el < pivot]
	highs = [el for el in l if el > pivot]
	pivots = [el for el in l if el == pivot]

	if k < len(lows):
		return quickselect(lows, k, pivot_fn)
	elif k < len(lows) + len(pivots):
		# We got lucky and guessed the median
		return pivots[0]
	else:
		return quickselect(highs, k - len(lows) - len(pivots), pivot_fn)