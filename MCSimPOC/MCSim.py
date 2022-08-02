import sys
import time
import warnings
import numpy as np
import pandas as pd
import pickle as pkl
import matplotlib.pyplot as plt
import scipy.stats as st

def Normalize(data):
	max_val=data.max()
	min_val=data.min()
	data=(data-min_val)/(max_val-min_val)
	return data,max_val,min_val

def ReScale(data,max_val,min_val):
	return data*(max_val-min_val)+min_val

#Simulates a race by produing array with all possibilities
def SimulateRace(initial_possibilities,samples,points_available_discrete_values):
	#Sampling the possibilities vector for points at start of race
	values=np.random.choice(initial_possibilities,size=samples)
	#Creating meshes of initial points and race results
	values_mg,padv_mg=np.meshgrid(values,points_available_discrete_values)
	#Adding possible results from race to initial points
	possibilities=(values_mg+padv_mg).flatten()
	return possibilities

#Simulates a season by recursively simulating races
def SimulateSeason(possibilities,samples,races_remaining,points_available_discrete_values):
	#Gets points possibilities after race
	possibilities=SimulateRace(possibilities,samples,points_available_discrete_values)
	#Recursive logic
	if races_remaining==0:
		return np.unique(possibilities,return_counts=True),possibilities
	else:
		races_remaining-=1
	return SimulateSeason(possibilities,samples,races_remaining,points_available_discrete_values)

def FitBestDist(data,bins=200,dist_names=['alpha','beta','gamma','logistic','norm','erlang']):
	densities,bin_edges=np.histogram(data,bins,density=True)
	bin_edges = (bin_edges + np.roll(bin_edges, -1))[:-1] / 2.0
	fig=plt.figure(figsize=(8,8))
	plt.plot(bin_edges,densities,label='densities')
	sse=np.empty(len(dist_names))
	run_times=np.empty(len(dist_names))
	for idx,dname in enumerate(dist_names):
		dist=getattr(st,dname)
		try:
			with warnings.catch_warnings():
				warnings.filterwarnings('ignore')
				t0=time.time()
				params=dist.fit(data)
				run_times[idx]=time.time()-t0
				arg = params[:-2]
				loc = params[-2]
				scale = params[-1]
				y=dist.pdf(bin_edges,loc=loc,scale=scale,*arg)
				sse[idx]=((y-densities)**2).sum()
				plt.plot(bin_edges,y,label='{}: SSE={:.4f}, run time={:.4f}'.format(dname,
					sse[idx],run_times[idx]))
		except Exception as e:
			print(e)
			sse[idx]=sys.maxsize
	plt.legend()
	return sse,run_times,dist_names



