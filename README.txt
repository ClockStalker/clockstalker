This repository contains the code for the "ClockStalker" bot on Reddit. The bot selects certain users on Reddit, analyzes their posting history, generates a graph of this data, and guesses the user's time zone based on it. It then posts the graph as a reply to one of the user's comments.

The bot is started by invoking the file listener.py on the command line:

python listener.py

Then, assuming you have Python installed, the script will then run continuously until it is manually stopped.

Required Python packages:
-Python Reddit API Wrapper, AKA PRAW ("import reddit")
-urllib
-urllib2
-base64
-json
-numpy
-matplotlib

Note: If you have trouble running the script, it's almost certainly due to MatPlotLib. I've run this on Windows, Mac, and Linux machines, and each OS requires a slightly different configuration of MatPlotLib, and each presents different obstacles to installing it. Even if it does work, the graphs will often look different depending on which exact version is installed. I cannot guarantee that the graph generation code will work with all versions of MatPlotLib (or even the most recent version, since updates can break previously functional code).

~ClockStalker-creator