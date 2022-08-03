import sys
import time
import urllib
import requests
import colorama
import re
import numpy as np
import pandas as pd
import pickle as pkl
import matplotlib.pyplot as plt
import bs4 as bs
from datetime import datetime
from ObjectList import *

def IsValidURL(url):
	"""
	Checks whether `url` is a valid URL.
	"""
	parsed = urllib.parse.urlparse(url)
	return bool(parsed.netloc) and bool(parsed.scheme)

def GetAllWebsiteLinks(url):
	"""
	Returns all URLs that is found on `url` in which it belongs to the same website
	"""
	# all URLs of `url`
	urls = set()
	internal_urls=set()
	external_urls=set()
	# domain name of the URL without the protocol
	domain_name = urllib.parse.urlparse(url).netloc
	soup = bs.BeautifulSoup(requests.get(url).content, "html.parser")
	for a_tag in soup.findAll("a"):
		href = a_tag.attrs.get("href")
		if href == "" or href is None:
			# href empty tag
			continue
		href = urllib.parse.urljoin(url, href)
		parsed_href = urllib.parse.urlparse(href)
		# remove URL GET parameters, URL fragments, etc.
		href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
		if not IsValidURL(href):
			# not a valid URL
			continue
		if href in internal_urls:
			# already in the set
			continue
		if domain_name not in href:
			# external link
			if href not in external_urls:
				external_urls.add(href)
			continue
		urls.add(href)
		internal_urls.add(href)
	return list(urls),list(internal_urls)

def RacesYearURL(urls,year):
	race_urls=list()
	for url in urls:
		res=re.search('/{}/races/'.format(year),url)
		if res is not None:
			race_urls.append(url)
	return race_urls

def GetRaces(year,url='https://www.formula1.com/en/results.html',save=True,
	out_file_name='races.pkl',load_file_name=None):
	if load_file_name is not None:
		with open(load_file_name,'rb') as load_file:
			races=pkl.load(load_file)
	else:
		_,internal_urls=GetAllWebsiteLinks(url)
		races_year_urls=RacesYearURL(internal_urls,year)
		number_of_races=len(races_year_urls)
		races=[None]*number_of_races
		for idx,race_url in enumerate(races_year_urls):
			# print(race_url)
			print('Pulling data for race {} of {}'.format(idx+1,number_of_races),end='\r')
			races[idx]=Race(race_url)
		races=ObjectList(races)
		races=races.sort('datetime')
		if save:
			with open(out_file_name,'wb') as out_file:
				pkl.dump(races,out_file)
	return races

"""
Race Class - pulls and stores data from a race
Inputs
	1. url - url to race result from www.formula1.com
	ex: https://www.formula1.com/en/results.html/2022/races/1114/great-britain/race-result.html
"""
class Race():
	def __init__(self,url):
		self.url=url
		self.Populate() #Calls function that pulls data

	def Populate(self):
		#Finding the name of the race from the url
		res=re.search(r"[a-z-]{0,90}(?=/race-result)",self.url)
		self.name=res.group(0)
		if self.name=='abu-dhabi':
			self.title='United_Arab_Emirates'
			#F1s website forcing me to hard-code this
		else:
			self.title=self.name.replace('-','_').title()
		res=re.search(r"(?<=/results\.html/)[0-9-]{0,10}",self.url)
		self.year=res.group(0)
		_,internal_urls=GetAllWebsiteLinks(self.url)
		#Gets the date of the race and converts to datestring
		self.FindDate()
		#Finds urls for quali, fastest lap, and sprint results
		#These URLs only exist if these events have happened
		self.FindSprintResultsURL(internal_urls)
		self.FindQualificationResultsURL(internal_urls)
		self.FindFastestLapResultsURL(internal_urls)
		#Determining whether the race has happened
		if self.fastest_laps_url is not None:
			self.is_finished=True
		else:
			self.is_finished=False
		#Determining if the race weekend includes a sprint
		self.IsSprintWeekend()
		#Pulling results data
		if self.is_finished:
			self.race_results=self.PullResultsTable(self.url)
			self.qualification_results=self.PullResultsTable(self.qualification_url)
			self.fastest_lap_results=self.PullResultsTable(self.fastest_laps_url)
			if self.is_sprint_weekend:
				self.sprint_results=self.PullResultsTable(self.sprint_url)
			else:
				self.sprint_results=None
			#adds theoretical points for qualification and fastest lap
			self.PointTotals()
		else:
			self.race_results=None
			self.qualification_results=None
			self.fastest_lap_results=None
			self.sprint_results=None

	def PointTotals(self):
		#Adding theoretical points for qualification and fastest lap
		self.qualification_results['PTS']=self.race_results['PTS']
		self.fastest_lap_results['PTS']=self.race_results['PTS']

	def IsSprintWeekend(self):
		schedule_url='https://www.formula1.com/en/racing/{}/{}.html'.format(self.year,
			self.title)
		source=urllib.request.urlopen(schedule_url).read()
		soup=bs.BeautifulSoup(source,'lxml')
		tables=soup.find_all('p',{'class':'f1-timetable--title'})
		res=re.search('Sprint',str(tables))
		if res is not None:
			self.is_sprint_weekend=True
		else:
			self.is_sprint_weekend=False

	def FindDate(self):
		try:
			source=urllib.request.urlopen(self.url).read()
			soup=bs.BeautifulSoup(source,'lxml')
			date_str=soup.find_all('span',{'class':'full-date'})[0].get_text()
			self.datetime=datetime.strptime(date_str, "%d %b %Y")
		except:
			self.datetime=None

	def PullResultsTable(self,url):
		try:
			source=urllib.request.urlopen(url).read()
			soup=bs.BeautifulSoup(source,'lxml')
			tables=soup.find_all('table')
			return pd.read_html(str(tables[0]), flavor='bs4', header=[0])[0]
		except:
			return None


	def FindSprintResultsURL(self,urls):
		for url in urls:
			res=re.search("{}/sprint-result".format(self.name),url)
			if res is not None:
				self.sprint_url=url
				return
		self.sprint_url=None

	def FindQualificationResultsURL(self,urls):
		for url in urls:
			res=re.search("{}/qualifying".format(self.name),url)
			if res is not None:
				self.qualification_url=url
				return
		self.qualification_url=None

	def FindFastestLapResultsURL(self,urls):
		for url in urls:
			res=re.search("{}/fastest-laps".format(self.name),url)
			if res is not None:
				self.fastest_laps_url=url
				return
		self.fastest_laps_url=None



# class NotFoundException(Exception):
# 	print('Query not found in internal URLs')

