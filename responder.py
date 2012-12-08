import reddit
import time
import urllib
import urllib2
import base64
import json
import random
import numpy as np

#This module does the work of analyzing a user's posting history, generating a graph
#and a comment, and returning the text of that comment for the listener module to post.

#Process a PNG image for uploading to Imgur.
def encode_image(path_to_image):
	source = open(path_to_image, 'rb')
	picture = base64.b64encode(source.read())
	print('encoded')
	return picture

#Fetch the file "graph.png" and upload it to Imgur.
def upload_graph():
	picture = encode_image('graph.png')
	data = urllib.urlencode({"key":'8f38ccdcf3f63b6a06347a33f1d9f424',
							 "image":picture})
	site = urllib2.Request('http://imgur.com/api/upload.json', data)
	s = urllib2.urlopen(site)
	response = s.read()
	r = json.loads(response)
	imageURL = r['rsp']['image']['image_hash']
	return imageURL

#A list of quotes about time.
quotes = [ "Tempus neminem manet",
		   "Time is an illusion, lunchtime doubly so",
		   "Lente hora, celeriter anni",
		   "Observe the time and fly from evil",
		   "Ars longa, vita brevis",
		   "To hold Infinity in the palm of your hand, and Eternity in an hour",
		   "Because I could not stop for Death, he kindly stopped for me",
		   "The Sun is a harsh master",
		   "Omnes vulnerant, ultima necat",
		   "Hora fugit, ne tardes",
		   ]

#The template with which comments are generated.
message = """
/u/{0}: Analyzing {1} comments and submissions over the last {2} days

* Most active hour{8}: {3} UTC ({4} posts/hour)
* Least active hour{9}: {5} UTC ({6} posts/hour)
* [Complete hourly breakdown](http://i.imgur.com/{11}.png)

Hypothesized location: {10}

*{7}*"""

#Take a list of integers denoting hours, and convert that into a range.
#E.g., prettify([13,14,15,17,18]) -> "1-4pm, 5-7pm"
def prettify(hourlist):
	base = 0
	durations = []
	for i in range(1,len(hourlist)): #Start at 1, not zero
		if hourlist[i] == hourlist[i-1]+1:
			pass
		else:
			durations.append(hourlist[base:i])
			base = i
	durations.append(hourlist[base:])

	if durations[0][0] == 0 and durations[-1][-1] == 23:
		durations[-1].extend(durations[0])
		durations[0] = durations[-1]
		durations.pop()

	output = ""
	for i in range(len(durations)):
		d = durations[i]
		
		firstnum = d[0]
		lastnum = (d[-1]+1)%24
		firstmeridian = {True:'pm', False:'am'}[firstnum>=12]
		lastmeridian = {True:'pm', False:'am'}[lastnum>=12]
		
		if firstnum > 12:
			firstnum -= 12
		elif firstnum == 0:
			firstnum = 12
			
		if lastnum > 12:
			lastnum -= 12
		elif lastnum == 0:
			lastnum = 12

		if firstmeridian == lastmeridian: firstmeridian = ""
		
		output += ( str(firstnum) + firstmeridian + "-" + str(lastnum) + lastmeridian )
		if i != len(durations)-1: output += ", "
	return output
			
#Guess the location of the user based on their least active 8-hour interval
#(which is assumed to be when they're asleep).
def guess_location(data):
	data.extend(data[0:7])
	minact = None
	bedtime = 0
	for i in range(24):
		next8hours = sum(data[i:i+8])
		if minact == None or next8hours < minact:
			minact = next8hours
			bedtime = i
	#Apologies to South Americans and Africans!
	#But we're going to be wrong most of the time if we guess that.
	if bedtime <= 0: return "Central / Northern Europe"
	if bedtime <= 3: return "Western Europe"
	if bedtime <= 5: return "Eastern North America"
	if bedtime <= 7: return "Central North America"
	if bedtime <= 11: return "Western North America"
	if bedtime <= 13: return "Oceania / New Zealand"
	if bedtime <= 18: return "East Asia / Australia"
	if bedtime <= 20: return "Central / South Asia"
	if bedtime <= 22: return "Eastern Europe / Middle East"
	if bedtime <= 23: return "Central / Northern Europe"


#Generate the graph from a data array, and save it as "graph.png".
def graph(data, username):
	#In order for this to work on Windows, the matplotlib module has to be reimported
	#every time; otherwise the script will crash eventually. (Don't ask me why)
	import matplotlib.pyplot as plt
	from matplotlib import font_manager
	font_manager.findfont('Times New Roman')
	
	plt.clf()
	N = 24
	ind = np.arange(N)
	width = 1

	p1 = plt.bar(ind, data, width, color='#ccccff', linewidth=1.0)
	plt.xlim( 0, 24 )
	plt.ylim( 0.00000001, plt.ylim()[1] )
	chars = max([len(('%f' % t).rstrip('0').rstrip('.')) for t in plt.yticks()[0]])
	if chars > 4: adjustment = 0.019*(chars-4)
	else: adjustment = 0.0

	fig = plt.figure(figsize=(8,6) )
	ax = fig.add_subplot(1,1,1)
	ax.yaxis.grid(color='black', linestyle='solid',linewidth=1.5)
	ax.xaxis.grid(color='black', linestyle='solid',linewidth=1.5)

	p1 = plt.bar(ind, data, width, color='#ccccff', linewidth=1.0)
	plt.xlim( 0, 24 )
	plt.ylim( 0.00000001, plt.ylim()[1] )
	plt.gcf().subplots_adjust(left=0.125+adjustment)

	plt.xlabel('Time (UTC)')
	plt.ylabel('Posts / hour')
	plt.title('u/'+username.replace('_','$\_$'))
	plt.xticks(np.arange(25), ('12am','','6am','','12pm','','6pm','','12am') )
	plt.xticks(np.arange(0,25,3))
	plt.rcParams.update({'font.size': 22, 'font.style':'bold'})
	plt.rc('font', family='serif')
	plt.rc('font', serif='Times New Roman') 
	plt.gcf().subplots_adjust(bottom=0.12)
	plt.savefig("graph.png")

	
#Analyze a user, upload a graph, and return the text of a comment for the bot to post.
#(If for any reason the user can't be analyze, return None.)
#If passive==True, then generate, the graph, but don't upload it
#(useful for debugging or general stalking).
def stalk(username, passive=False):
	r = reddit.Reddit(user_agent='clockstalker')

	#if the user is less than 7 days old, stop the analysis, because there won't be enough data.
	if (time.mktime(time.localtime()) - r.get_redditor(username).created_utc) < 7*24*60*60:
		return None

	#Get the list of comments by the user
	last = None
	comlist = []
	while True:
		if last: submissions = r.get_redditor(username).get_comments(limit=100, url_data={'after':last})
		else: submissions = r.get_redditor(username).get_comments(limit=100)
		comlist.extend(submissions)
		if comlist == [] or last == comlist[-1].name:
			print "DONE"
			break
		else:
			last = comlist[-1].name
			print last
			time.sleep(2.1)

	#Get the list of submissions by the user
	last = None
	postlist = []
	while True:
		if last: submissions = r.get_redditor(username).get_submitted(limit=100, url_data={'after':last})
		else: submissions = r.get_redditor(username).get_submitted(limit=100)
		postlist.extend(submissions)
		if postlist == [] or last == postlist[-1].name:
			print "DONE"
			break
		else:
			last = postlist[-1].name
			print last
			time.sleep(2.1)

	# Determine the latest post
	if postlist and comlist:
		latest = max(comlist[0].created_utc, postlist[0].created_utc)
	elif postlist:
		latest = postlist[0].created_utc
	elif comlist:
		latest = comlist[0].created_utc

	#Now, in order not to bias the data, we have to trim the lists by setting a cutoff
	#time which is a whole number of days since the most recent post. Find the most
	#distant cutoff time such that there are still posts older than that.
	
	#Trim the comment list
	if comlist:
		earliestcom = comlist[-1].created_utc
		daysoldC = int((latest - earliestcom)/86400)
		cutoff = daysoldC * 86400
		while latest - comlist[-1].created_utc < cutoff:
			comlist.pop()
	else: daysoldC = 0
	   
	#Trim the submission list
	if postlist:
		earliestpost = postlist[-1].created_utc
		daysoldP = int((latest - earliestpost)/86400)
		cutoff = daysoldP * 86400
		while latest - postlist[-1].created_utc < cutoff:
			postlist.pop()
	else: daysoldP = 0

	#Now, we must further trim the lists so that each list has the same cutoff time.
	if len(comlist) < len(postlist): daysold = daysoldP
	else: daysold = daysoldC

	# Trim the comment list again
	if comlist:
		while latest - comlist[-1].created_utc > daysold * 86400:
			comlist.pop()

	# Trim the submission list again
	if postlist:
		while latest - postlist[-1].created_utc > daysold * 86400:
			postlist.pop()	 

	#if the user has less than 20 comments/submissions, stop the analysis
	if len(postlist) + len(comlist) < 20:
		return None

	#Now, start collecting the data into a histogram.
	histogram = [0]*24
	for x in comlist:
		t = time.gmtime(x.created_utc)
		histogram[t.tm_hour] += 1
	for x in postlist:
		t = time.gmtime(x.created_utc)
		histogram[t.tm_hour] += 1
	quantity = len(postlist) + len(comlist)

	scaledhistogram = [0]*24
	for i in range(24):
		scaledhistogram[i] = float(histogram[i]) / daysold
	
	#Find the most and least active hour(s)
	maximum = max(scaledhistogram)
	minimum = min(scaledhistogram)
	maxlist = []
	for i in range(24):
		if scaledhistogram[i] == maximum: maxlist.append(i)
	minlist = []
	for i in range(24):
		if scaledhistogram[i] == minimum: minlist.append(i)
	maxlistplural = {True:'s', False:''}[len(maxlist) > 1]
	minlistplural = {True:'s', False:''}[len(minlist) > 1]

	#Choose a random quote
	quote = random.choice(quotes)

	if maximum == 0.0:
		maximum = 0
	else:
		maximum = round(maximum, 3)

	if minimum == 0.0:
		minimum = 0
	else:
		minimum = round(minimum, 3)

	#Generate the graph
	graph(scaledhistogram, username)

	if passive: #Upload the graph unless passive==True
		imageURL = '___'
	else:
		imageURL = upload_graph()

	#Generate the comment from the template
	output = message.format(username, quantity, daysold,
						 prettify(maxlist), maximum,
						 prettify(minlist), minimum,
						 quote, maxlistplural, minlistplural,
						 guess_location(scaledhistogram), imageURL)
	print output
	print ""
	print ""
	return output


