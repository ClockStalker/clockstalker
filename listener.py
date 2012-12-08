import reddit
import time
import responder

MAX_COMMENTS_TO_FETCH = 500
delay = 60 * 60 * 12 #Wait at least 12 hours before doing a user on the todo list.

#Analyze a comment to see if we should reply to it.
def check_comment(comment):
	if str(comment.author) in usersdone: return False #Don't do the same user more than once.
	threaddone = (str(comment.link_id) in threadsdone) #Don't post in the same thread more than once.

	if (str(comment.author) in userstodo) and not threaddone: #If they've been on the todo list for longer than "delay", yes.
		if userstodo[str(comment.author)] + delay < time.mktime(time.localtime()):
			return True
	
	lc = comment.body.lower()

	if not threaddone: #Check for certain key phrases.
		if "time on reddit" in lc: return True
		if ("much time" in lc or "enough time" in lc) and "reddit" in lc: return True

	#If the comment was a reply to us, and is asking to be done,
	#then return False, but add the user to the todo list first.
	if comment.parent_id in mycomments:
		if ("do me" in lc or 
		"please?" in lc or
		"please!" in lc or
		("me" in lc and lc[-1]=="?") or
		(len(lc)>=4 and lc[-4:-1]==" me") or
		(len(lc)>=3 and lc[0:3]=="me ")	 ):
			userstodo[str(comment.author)] = int(comment.created_utc)
			f = open("userstodo.txt", "a")
			f.write(str(comment.author) + "\t" + str(int(comment.created_utc))+"\n")
			f.close()
			print "Do", str(comment.author), "later."
			return False
	#If none of these conditions are met, return False.
	return False

#Given a comment, create and post a reply.
def reply_to_comment(comment):
	if str(comment.author) in usersdone: return #Don't do the same user more than once (double-check)
	else:
		print "Found comment!", comment.permalink
		try:
			reply = responder.stalk(str(comment.author)) #Generate the reply text
		except:
			reply = None
		if reply:
			rep = comment.reply(reply) #Post the reply to Reddit
			
			#Add the user to the "usersdone" list
			usersdone.append(str(comment.author))
			f = open("usersdone.txt", "a")
			f.write(str(comment.author) + "\n")
			f.close()
			
			#Add the ID of the new comment to the "mycomments" list
			mycomments.append(str(rep.name))
			f = open("mycomments.txt", "a")
			f.write(str(rep.name) + "\n")
			f.close()
			
			#Add the ID of the top-level post to the "threadsdone" list
			threadsdone.append(str(comment.link_id))
			f = open("threadsdone.txt", "a")
			f.write(str(comment.link_id) + "\n")
			f.close()

		
#Continually track the comments on certain subreddits,
#looking for ones that pass the condition_function.
def track_comments(condition_function, action_function):
	r = reddit.Reddit(user_agent='clockstalker')
	r.login(username="ClockStalker", password="InsertPasswordHere")
	
	#For each of the four subreddits we're tracking
	#(AskReddit, AdviceAnmials, funny, WTF),
	#initialize a placeholder to tell us what was the most recent
	#comment we've already looked at (so we don't have to analyze
	#the same comment more than once).
	askreddit_ph = None
	adviceanimals_ph = None
	funny_ph = None
	wtf_ph = None
	
	#Initialize the subreddit objects (according to PRAW)
	askreddit = r.get_subreddit("AskReddit")
	adviceanimals = r.get_subreddit("AdviceAnimals")
	funny = r.get_subreddit("funny")
	wtf = r.get_subreddit("WTF")
	
	#Loop continuously:
	while True:
		try:
			#Get the comments from AskReddit since the last placeholder.
			commentsGen = None
			if askreddit_ph is None: commentsGen = askreddit.get_comments(limit=25)
			else: commentsGen = askreddit.get_comments(place_holder=askreddit_ph, limit=MAX_COMMENTS_TO_FETCH)
			askreddit_comments = []
			for c in commentsGen: askreddit_comments.append(c)
			if askreddit_ph: askreddit_comments.pop()
			if askreddit_comments: askreddit_ph = askreddit_comments[0].id
			
			#Get the comments from AdviceAnimals since the last placeholder.
			commentsGen = None
			if adviceanimals_ph is None: commentsGen = adviceanimals.get_comments(limit=25)
			else: commentsGen = adviceanimals.get_comments(place_holder=adviceanimals_ph, limit=MAX_COMMENTS_TO_FETCH)
			adviceanimals_comments = []
			for c in commentsGen: adviceanimals_comments.append(c)
			if adviceanimals_ph: adviceanimals_comments.pop()
			if adviceanimals_comments: adviceanimals_ph = adviceanimals_comments[0].id
	
			#Get the comments from funny since the last placeholder.
			commentsGen = None
			if funny_ph is None: commentsGen = funny.get_comments(limit=25)
			else: commentsGen = funny.get_comments(place_holder=funny_ph, limit=MAX_COMMENTS_TO_FETCH)
			funny_comments = []
			for c in commentsGen: funny_comments.append(c)
			if funny_ph: funny_comments.pop()
			if funny_comments: funny_ph = funny_comments[0].id
			
			#Get the comments from WTF since the last placeholder.
			commentsGen = None
			if wtf_ph is None: commentsGen = wtf.get_comments(limit=25)
			else: commentsGen = wtf.get_comments(place_holder=wtf_ph, limit=MAX_COMMENTS_TO_FETCH)
			wtf_comments = []
			for c in commentsGen: wtf_comments.append(c)
			if funny_ph: wtf_comments.pop()
			if funny_comments: wtf_ph = wtf_comments[0].id
	
			#Merge all the comment lists together
			comments = askreddit_comments + adviceanimals_comments + funny_comments + wtf_comments
			
			#How many comments did we get?
			print "got " + str(len(comments)) + " comments"
	
			#For each comment, if it passes condition_function, execute action_function.
			if len(comments) > 0:
				for comment in comments:
					if condition_function(comment):
						action_function(comment)
		except:
			#If at any point an error occurs, just wait until the next round.
			print "An error occurred. Trying again next time."

		#Wait approximately 75 seconds before checking again.
		print "sleeping",
		for i in range(30):
			time.sleep(2.5)
			print ".",





#Before we begin, we have to initialize all the lists into array objects for easy access.

usersdone = [] #The list of users that we've already done.
mycomments = [] #The list of comments that we've made.
threadsdone = [] #The list of threads that we've already commented in.

#These three lists are stored as txt files.
f = open('usersdone.txt')
usersdone = [line.strip() for line in f.readlines()]
f.close()

f = open('mycomments.txt')
mycomments = [line.strip() for line in f.readlines()]
f.close()

f = open('threadsdone.txt')
threadsdone = [line.strip() for line in f.readlines()]
f.close()

#The list of users who have asked the bot to do them.
#Also stores the time at which they make the request, so we can wait "delay" before answering.
def split_utd_line(line):
	arr = line.strip().split('\t')
	return [arr[0], int(arr[1])]
f = open('userstodo.txt')
userstodo = {split_utd_line(line)[0]:split_utd_line(line)[1] for line in f.readlines()}
f.close()




def go():
	track_comments(check_comment, reply_to_comment)


#Ready, set...
go()