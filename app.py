#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Notes ---#
#
#



# 7 need to add "starting" print to all worker functions
# 9 need to copy database requirements block from initiate_database process to here
# 10 need to cut down initiate_database.py to just processes which are necessary and correct
# 16 Need to add in query and fulfillment columns to database through creation module, and set relevant value in this process
# 17 Need to add link to Moz blog post to Create API.AI step
# 18 Fill out lists of processes and definitions



# Slack token and challenge management resource: https://github.com/slackapi/Slack-Python-Onboarding-Tutorial
# Celery on Heroku resources (have used latter over the former here): to https://blog.miguelgrinberg.com/post/using-celery-with-flask and https://devcenter.heroku.com/articles/celery-heroku

#
#
#--- End of notes ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Steps to take before implementing this code ---#

# 1 Create an API.AI account and build your conversation
    # The important parts here are the intents which need to include phrases and actions, I give details of the variables I use in my Moz post


# 2 Create Heroku app: https://devcenter.heroku.com/articles/git
    # The above will take you through the steps needed to create a Heroku application
    # it looks complicated but the instructions are really easy to follow, it's one of
    # the first things I did



#--- End of steps to take before implementing this code ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Requirements for process in chronological order ---#
#
#


# 1  Receive Slack token and username and record in database for future identification and retrieval, use that initial information to send private message to user which gives basic instruction

# 2  Receive Slack challenge, respond (this allows the bot to receive notifications from Slack)

# 3  Receive message posted in either private Slack channel or a public channel which the bot has been added to, check to ensure the message is not a repeated message by checking that it is not exactly the same as the last message while being within ten minutes of the last message
#    (this is to account for the fact that users might send the same message time after time if they want the same order)

# 4  Check that message doesn't have a bot id - suggesting that it was sent by a bot (perhaps nambot) this is to avoid the program responding to itself

# 5  Whether the message is genuine, a repeat or a bot message, respond semi-immediately to prevent Slack resending the event notifications

# 6  Take all genuine messages and initially check database using user_id as unique key to determine whether we have a user name

# 7  Send message to API.AI to update API.AI contexts and to have message categorised by API.AI system

# 8  Receive response from API.AI and, depending on whether we have username, either send follow-up message to API.AI to create username request contexts

# 9  Depending on whether username is present, either start process_food process or ask for username, set username, and start process_food process

# 10 Connect to Google Sheet with GSpread library and select the correct sheet

# 11 Find the first empty row in the sheet by counting all the cells in the first column and subtracting those with None values

# 12 Add values of date, user name, and order food to the first empty row

# 13 Retrieve the current "top nammer" record for the team concerned (which is saved in the database from previous operations for speed of retrieval)

# 14 Calculate the number of orders that have been placed today by filtering recent results to only those which match the current date

# 15 Send appropriate follow-up message based on number of returned results matching minimum threshold and whether the current "top nammer" matches the one retrieved

# 16 Calulate the "top nammer" and update the database for quick retrieval in the next process


#
#
#--- End of process requirements ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- API integrations and limitations ---#
#
#

# 1 API.AI - natural language processing (https://api.ai/)
    # Key points of interaction are:
        # 1 Initial message which can be formatted to include information or trigger an event (either POST or GET request)
        # 2 Optional slot filling portion, where it sends a request and waits five seconds for a response (POST request)
        # 3 Point as which it responds to the initial message with key information about categorisation and actions set up in the API.AI interface accessible at API.AI

    # Limitations are:
        # 1 If using its built-in integrations with existing chat services, you must use the optional slot filling to do your processing
        # 2 Using the optional slot filling means you must respond within 5 seconds, if your app needs to pass information back it must be done in that time (should be no problem unless using a very slow API)
        # 3 When it receives a POST or GET request, it will only offer a response to that, it won't offer information by new POST or GET (meaning you can't send and forget, pretty standard operation of these requests)
        # 4 If you are using the optional slot filling, API.AI can NOT receive both the initial request AND the response to its slot filling request from the same place. This isn't a problem most of the time, if you are manually sending a request to API.AI you should do the processing before or after and avoid the slot filling option if possible)
        # 5 If your process is slower than the five second window you cannot use API.AI with platforms like Google Home because you HAVE to use the slot filling option in that case. This tight window and inability to push messages to spoken platforms is quite standard to avoid a confusing or invasive user experience (also applies to Alexa)
        # 6 Excellent platform but support team are slow to respond/ sometimes don't respond at all



# 2 Slack - messaging platform (https://slack.com/)
    # Key points of interaction are:
        # 1 Slack sending "challenge" request to our service to make sure it is set up to receive events from Slack
        # 2 Slack sending user name and user token to our service, for us to save, as part of authentication
        # 3 Slack pushing events to our application whenever someone posts a message that our bot sees which meets our criteria

    # Limitations are:
        # 1 Slack requires a quick response to the messages it sends, and can send them multiple times which can result in repeated action from our app if it isn't deduped (particularly problematic as on Heroku free the app will take a while to respond, and all in all this process takes quite a while so we can't wait until we've finished to respond)
        # 2 Posting to Slack channels requires an appropriate user token which must be stored securely




# 3 GSpread - Google sheet interaction library
    # Key points of interaction are:
        # 1 Retrieving first empty row
        # 2 Putting order in first empty row
        # 3 Checking number of orders that match today's date
        # 4 Checking the most frequently occurring user in recent orders

    # Limitations are:
        # 1 Reading blocks of data from this are very slow (often longer than five seconds) meaning we cannot do this within API.AI's optional five second slot filling window, meaning we have to process either before or after API.AI has done it's process, so we have to manage Slack integrations and auth
        # 2 Empty cells don't return None value, but rather "" meaning we have to check for empty cells in a slightly different way


#--- End of APIs integrations and limitations ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Platforms used ---#

# 1 Heroku - free plan https://www.heroku.com/
    # Heroku Redis :: Redis (free)
    # Heroku Postgres :: Database (free)
    # LogDNA (paid)

#--- End of platforms used ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#




#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Requirements for database ---#

# 1 Must contain: id serial PRIMARY KEY, source varchar, user_id varchar, user_name varchar, user_token varchar, team_id varchar, team_name varchar, bot_token varchar, most_recent_user_channel varchar, most_recent_user_session_id varchar, most_recent_action_for_user varchar, most_recent_user_food varchar, most_recent_user_query varchar, most_recent_query_time TIME
# 2 Must be quick
# 3 readable from web and worker processes
# 3 Must allow read and overwrite

#Some of the columns in that database list are as-yet unused. For instance most_recent_user_food, however that will allow more easy rollout of features like easy repeat ordering

#--- End of database requirements ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- List of processes and definitions ---#




#--- End of list of processes and definitions ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Imports ---#
# Throughout this program we call the below imports for various actions
# failing to import one of these libraries, or importing the wrong one
# may be one reason for an app just failing mid-process


# All of these libraries need to be reflected in our requirements file
# which we upload as part of our app


import os
from flask import Flask, make_response, request
from slackclient import SlackClient

import gspread
import oauth2client
import datetime
from datetime import datetime, time, timedelta
import time

from oauth2client.service_account import ServiceAccountCredentials
import json

import os.path
import sys

import requests


try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
    import apiai

from collections import Counter


import psycopg2
from flask.ext.sqlalchemy import SQLAlchemy
#Thanks to http://blog.y3xz.com/blog/2012/08/16/flask-and-postgresql-on-heroku

import urllib.parse
#Thanks to https://stackoverflow.com/questions/45133831/heroku-cant-launch-python-flask-app-attributeerror-function-object-has-no

import tasks

app = Flask(__name__)

#--- End of imports ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Confirming asynchronous process is working ---#
# This is run when we are first starting up our application.
# It allows us to make sure that our asynchronous worker process
# is receiving commands correctly

tasks.add(1, 2)

#--- End of confirming asynchronous process is working ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Environment variables ---#

# These are pieces of information that any app in our program
# should be able to call. One reason to set them as environmental
# variables is that by sharing the code we aren't sharing confidential
# login information.


#Slack variables
#
# We set these variables based on information from our Slack bot
# instructions for how to create environment variables in Heroku are at (https://devcenter.heroku.com/articles/config-vars)
client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
#
#-#

#Database variables
#
# These variables are instructions to allow our program to connect to the
# database we set up
# instructions for how to create environment variables in Heroku are at (https://devcenter.heroku.com/articles/config-vars)
# setting database variables: http://blog.y3xz.com/blog/2012/08/16/flask-and-postgresql-on-heroku
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
#
#-#


#--- End of environment variables ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- 1 Start application ---#

print ("""
#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#
""")

@app.route('/', methods=["GET", "POST"])
def webhook():

    #------------------------------------------------------------#
    # Setting location codes, these will be used in print commands
    # so we can easily keep track of where things are. The only
    # purpose of these is to be included in the print commands
    # however if they are removed the app will break at the first
    # print
    #------------------------------------------------------------#
    app_code="web "
    location_code="1 (startup)"
    #------------------------------------------------------------#
    # End of setting location codes
    #------------------------------------------------------------#

    #------------------------------------------------------------#
    # Printing initial startup information, sharing the request
    # that activated the app_code
    #------------------------------------------------------------#
    print (app_code,location_code, "starting at ", datetime.utcnow())
    print(app_code,location_code, "request", request)
    print(app_code,location_code, "request method", request.method)
    #------------------------------------------------------------#
    # End of printing initial startup info
    #------------------------------------------------------------#


#--- End of start application ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- 2 Receive Slack token and record in database ---#
#
# Thanks to https://github.com/slackapi/Slack-Python-Onboarding-Tutorial

    if request.method == 'GET':
        location_code="2 (slack token)"
        print (app_code,location_code, "method is GET at ", datetime.utcnow())
        #Only 'GET' requests come from Slack when user is authorising app and giving user token
        print (app_code,location_code, "received get request, starting get process")

        open_db_connection(app_code,location_code)
        # In order to read or make any changes to the
        # database we need to open the connetion and
        # set up the relevant variables. We want to
        # minimise the number of concurrent connections
        # so we use our open and close connection functions
        # the notice below is for easy reading of whether it's
        # accessible

#------------------------------------------------------#
#//////////////////////////////////////////////////////#
#============  Database connection open  ==============#
#//////////////////////////////////////////////////////#
#------------------------------------------------------#

        # Calling action from python onboarding tutorial which retrieves
        # the appropriate tokens and authentication
        auth_complete=get_token(app_code,location_code)


        # Closing the connection with the database
        close_db_connection(app_code,location_code)

#------------------------------------------------------#
#//////////////////////////////////////////////////////#
#============  Database connection closed =============#
#//////////////////////////////////////////////////////#
#------------------------------------------------------#


        print (app_code,location_code,"successfully got token, finishing process and shutting down")


        # This is the message we send to the Slack user, this is very plain
        # but instead we could send HTML for a richer page

        return auth_complete
        #----- Process ended because responded to auth -----#


#--- End of 2 receive Slack token and record in database ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- 3 Respond to Slack Challenge request ---#
#
# Thanks to https://github.com/slackapi/Slack-Python-Onboarding-Tutorial

    if request.method == 'POST':
        # If the request isn't 'Get' we need to start working out what it IS
        # The first test is whether it contains "challenge", if so it's part of the Slack authorisation setup
        location_code="3 (received POST)"
        print (app_code,location_code," method is POST at ", datetime.utcnow()," post process started")

        # Getting the information from the 'Post' request, whatever it may be
        post_request = request.get_json(silent=True, force=True)

        #Printing the value of the post request for debugging
        print (app_code,location_code," got json")
        print (app_code,location_code,"post_request: ", post_request)

        # As mentioned above, if it contains 'challenge' that's an easy way to see it's part of Slack auth so this is
        # dealing with that eventuality first so we can cater to other scenarios further down

        if "challenge" in post_request:
            # We are using the presence of a challenge value
            # as a way of identifying a challenge request
            # from Slack
            location_code="3.1 (Slack challenge)"
            print (app_code,location_code," challenge detected")

            # Calling function from Slack-Python-Onboarding-Tutorial which creates an
            # appropriate response to the challenge request (https://github.com/slackapi/Slack-Python-Onboarding-Tutorial)
            response_to_challenge=challenge_response(app_code,location_code,post_request)

            print (app_code,location_code," response_to_challenge: ",response_to_challenge )

            print (app_code,location_code,"success, sending challenge response")

            # Sending the response to Slack, it's important that this is
            # right otherwise Slack won't accept it and send us notifications
            # when people post

            return response_to_challenge
            #----- Process ended because responded to challenge -----#




#--- End of 3 respond to Slack Challenge request ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- 4 Receive Slack message - send response immediately and have worker send message on to API.AI ---#

        else:
            # Now that we know the request ISN'T either the challenge or token Slack authorisation we can manage the
            # scenario where it is an actual message passed to our bot from Slack

            # Slack needs a quick response otherwise it will keep sending the
            # message so we have to use our asynchronous background process
            # to do most of the work while this main process just triages and
            # sends a quick 200 "I've got it" type response

            location_code="4.1 (Slack user message)"
            print (app_code,location_code," know it isn't challange at ", datetime.utcnow())

            if "event" in post_request:
                # When our Slack integration is activated by a user the
                # Post request includes an 'event' field

                print (app_code,location_code," slack event")

                # Peeling out information from Slack event
                post_request_data=post_request.get("event")
                print (app_code,location_code," have got event")

                # Printing out the data for debugging
                print (app_code,location_code," post_request_data", post_request_data)


                #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
                #
                #--- 4.1.1 check to make sure bot doesn't respond to messages from bots  ---#

                # Asking for bot_id from the message, if it doesn't exist the value will be
                # None so we'll skip over the next "if bot_id" step
                bot_id=post_request_data.get("bot_id")
                if bot_id:
                    location_code="4.1.1 (bot message)"
                    print (app_code,location_code," picking up bot message, id: ", bot_id)
                    # If a bot has posted the message (including us)
                    # the message will have a bot_id, we want to ignore those
                    print (app_code, location_code, "shutting down")
                    return make_response("Bot message", 200)
                    #----- Process ended because bot message -----#


                #--- End of 4.1.1 check to make sure bot doesn't respond to messages from bots ---#
                #
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


                # Getting the unique Slack user ID, we also use this
                # unique number in our database to identify and update
                # user records
                user_id=post_request_data.get("user")
                print (app_code,location_code," user_id: ", user_id)

                # Getting what user has said in the message
                query=post_request_data.get("text")
                print (app_code,location_code," query: ", query)



                #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
                #
                #--- 4.1.2 check to make sure the message we received isn't a duplicate of the last  ---#

                # Finding out whether the current query is within ten minutes of the last one
                # (thanks to https://stackoverflow.com/questions/6205442/python-how-to-find-datetime-10-mins-after-current-time
                # and https://stackoverflow.com/questions/10048249/how-do-i-determine-if-current-time-is-within-a-specified-range-using-pythons-da

                location_code="4.1.2 (deduplication)"

                open_db_connection(app_code,location_code)


#------------------------------------------------------#
#//////////////////////////////////////////////////////#
#============  Database connection open  ==============#
#//////////////////////////////////////////////////////#
#------------------------------------------------------#

                # Checking our database to find the variables we save each time
                # the last exact message received, the last action saved for a user_id
                # and the last time we received a message from that user
                most_recent_query=check_database(app_code,location_code,user_id, 'most_recent_user_query')
                most_recent_action=check_database(app_code,location_code,user_id, 'most_recent_action_for_user')
                last_query_time=check_database(app_code,location_code,user_id, 'most_recent_query_time')



                # Retrieving the time it is now, then calculating what time
                # it would have been ten minutes ago
                now = datetime.now()
                print (app_code,location_code," now is ", now)

                ten_minutes_ago=datetime.now()-timedelta(minutes=5)
                print (app_code,location_code," ten minutes ago is: ", ten_minutes_ago)

                # Catching error for if the user hasn't used the nambot
                # in which case the last_query_time wouldn't exist
                if last_query_time==None:
                    print (app_code,location_code," first query or unable to call last query time")
                else:
                    # Checking whether more than ten minutes have
                    # passed since the last query
                    if ten_minutes_ago < last_query_time:
                        # If less than ten minutes have passed since
                        # last query it's more likely to be duplicate
                        print (app_code,location_code," less than ten minutes since last recorded action")
                        within_last_query_window='yes'
                    else:
                        # If more than ten minutes have passed we're
                        # assuming it's not a repeated send from Slack
                        # this allows a user to place exactly the same
                        # order without having to worry about varying
                        # their wording
                        print (app_code,location_code," more than ten minutes since last recorded action")


                print (app_code,location_code,"updating columns")
                # Using our update_columns process to put the time of THIS query
                # in our database, so we can read it next time
                update_columns(app_code,location_code,['most_recent_query_time',now], user_id)

                if query==most_recent_query:
                    # If the current query is identical to the last query
                    # then it's a sign that we've had a repeated request
                    # from Slack
                    print (app_code,location_code," query is duplicate of last")
                    if within_last_query_window=='yes':
                        print (app_code,location_code," duplicate query shortly after last - shutting down")

                        close_db_connection(app_code,location_code)

                    #------------------------------------------------------#
                    #//////////////////////////////////////////////////////#
                    #============  Database closed within if ==============#
                    #//////////////////////////////////////////////////////#
                    #------------------------------------------------------#

                        return make_response("Repeat message", 200)
                        #----- Process ended because repeat message -----#

                #--- End of 4.1.2 check to make sure bot doesn't respond to messages from bots ---#
                #
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


                #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
                #
                #--- 4.2 Getting location information to direct response  ---#

                location_code="4.2 genuine message"
                print (app_code,location_code," not repeated query from Slack, saving latest query to prevent repeated action")

                # Using update_columns process to record most recent
                # query for future checks
                update_columns(app_code,location_code,['most_recent_user_query',query], user_id)

                #Getting event_id from function argument
                event_id=post_request.get("event_id")
                print (app_code,location_code," event id: ", event_id)

                #getting source that user is messaging from (to direct message back)
                channel=post_request_data.get("channel")
                print (app_code,location_code," channel: ", channel)


                #--- End of 4.2 getting location information to direct response ---#
                #
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


                #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
                #
                #--- 4.3 Sending genuine message to asynchronous process  ---#


                #Sending to async thanks https://devcenter.heroku.com/articles/celery-heroku
                # Unfortunately sending Slack messages to the API.AI process, then processing the response
                # and calculating information using the Google Sheets integration takes too long
                # we are using asynchronous processing to manage our longer process so we can
                # send Slack the "quick and confident" 200 response mentioned here: https://api.slack.com/events-api

                print (app_code,location_code," sending to worker")
                tasks.send_to_api(event_id, user_id, channel, query)

                #--- End of 4.3 Sending genuine message to asynchronous process ---#
                #
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

                #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
                #
                #--- 4.4 make quick 200 response to Slack to confirm we've received the message to stop it sending again ---#

                # Finally closing off database
                close_db_connection(app_code,location_code)

#------------------------------------------------------#
#//////////////////////////////////////////////////////#
#============  Database connection closed =============#
#//////////////////////////////////////////////////////#
#------------------------------------------------------#


                #Sending quick response to Slack to confirm we have received the message
                return make_response("Passed to API", 200)

                #--- End of 4.4 make quick 200 response to Slack to confirm we've received the message to stop it sending again ---#
                #
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#--- End of 4 Receive Slack message - send response immediately and have worker send message on to API.AI ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#============================================= Synchronous functions =======================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- (A) getting Slack token ---#

def get_token(app_code,location_code):

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Sending information to Slack API and getting authorisation token in response---#

    # Thanks to (https://github.com/slackapi/Slack-Python-Onboarding-Tutorial/blob/master/app.py)
    sublocation="A (get_token) - "
    print(app_code,location_code,sublocation,"token received")
    print(app_code,location_code,sublocation," request referrer: ",request.headers.get("Referer"))
    print(app_code,location_code,sublocation," starting post install")


    # Retrieve the auth code from the request params
    auth_code = request.args['code']
    print (app_code,location_code,sublocation," auth code: ", auth_code)

    # An empty string is a valid token for this request
    sc = SlackClient("")

    # Request the auth tokens from Slack
    auth_response = sc.api_call(
    "oauth.access",
    client_id=client_id,
    client_secret=client_secret,
    code=auth_code
    )

    # Printing off the authorisation response from Slack
    # for debugging
    print(app_code,location_code,sublocation,"auth response: ",auth_response)
    print(app_code,location_code,sublocation,"app access token",auth_response['access_token'])
    print(app_code,location_code,sublocation,"bot access token",auth_response['bot']['bot_access_token'])

    #--- End of Sending information to Slack API and getting authorisation token in response ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Adding information to database ---#

    # If you haven't got your database set up yet or you're testing this process regardless of the database
    # then comment out the lines from here until "End of adding information to database" and remove the comments
    # from the "Adding information to environmental variables" block



    print(app_code,location_code,sublocation," printing authorisation response: ", auth_response)


    source="Slack" #This is hard coded for now but could be changed based on where the authorisation request comes from
    user_id=auth_response['user_id']
    user_token= auth_response['access_token']
    bot_token= auth_response['bot']['bot_access_token']
    team_id= auth_response['team_id']
    team_name= auth_response['team_name']
    channel=auth_response['incoming_webhook']['channel_id']

    # user_creator process takes information and puts it in the database
    # we use the user_id as our unique identifier when calling and updating
    # information, we also use the user_token as authorisation to post to Slack
    user_creator(app_code,location_code,source, user_id, user_token, bot_token, team_id, team_name)


    #--- End of Adding information to database ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Adding information to environmental variables ---#
    #
    #os.environ["SLACK_USER_TOKEN"] = auth_response['access_token']
    #os.environ["SLACK_BOT_TOKEN"] = auth_response['bot']['bot_access_token']
    #
    #--- End of Adding information to environmental variables ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    print (app_code,location_code,sublocation," done user_creator process")

    #Sending message to slack which includes the defined speech from API.AI (thanks to https://api.slack.com/methods/chat.postMessage)
    params = (
    ('token', user_token),
    ('channel', channel),
    ('text', 'Hi, thanks for adding Nambot! If you ever want to add an order to the Vietnamese sheet just write that food in this channel or say "I want to order [food]" and I\'ll add it. For reference the sheet is located at: https://docs.google.com/spreadsheets/d/1kyRxXtXBhZsJwPLNydQNgqU2o1hXRIJbOFqvgaLyTTU/edit#gid=0'),
    ('username', 'nambot-the-third'),
    ('icon_emoji', ':ramen:'),
    ('pretty', '1'),
    )
    requests.get('https://slack.com/api/chat.postMessage', params=params)

    print (app_code,location_code,sublocation,"sent to Slack, finishing process")

    #----------#

    # Don't forget to let the user know that auth has succeeded!
    return "Auth complete!"

#--- End of (A) Getting slack token ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- (B) responding to challenge request ---#

def challenge_response(app_code,location_code,post_request):
    #Taken from https://github.com/slackapi/Slack-Python-Onboarding-Tutorial/blob/master/app.py
    #This route listens for incoming events from Slack and uses the event
    sublocation="B (challenge_response) - "
    print (app_code,location_code,sublocation,"post_request is", post_request)

    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification

    print(app_code,location_code,sublocation," challenge in slack event, creating response")
    return make_response(post_request["challenge"], 200, {"content_type":"application/json"})

#--- End of Web responding to challenge request ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- C Setting up psycopg2 connection ---#
# Thanks to: https://devcenter.heroku.com/articles/heroku-postgresql#connecting-in-python

def open_db_connection(app_code,location_code):
    sublocation="C (open_db_connection) - "
    print (app_code,location_code,sublocation," starting setting up database connection")
    #Thanks to https://stackoverflow.com/questions/45133831/heroku-cant-launch-python-flask-app-attributeerror-function-object-has-no
    urllib.parse.uses_netloc.append("postgres")
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    #}
    print (app_code,location_code,sublocation," url: ", url)

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Setting conn as a global variable ---#

    # We are setting conn as a global variable which means it doesn't
    # have to be included when we call a new function, we will be referencing
    # it in a few functions so it's important to be able to access it
    # without causing errors by forgetting to include it from one function to the next
    global conn

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )



    #--- End of Setting conn as a global variable ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Setting cur as a global variable ---#

    # See reasoning for including conn as global variable above
    global cur
    cur = conn.cursor()

    #--- End of Setting cur as a global variable ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    print (app_code,location_code,sublocation," finishing setting up database connection")

    return

#--- End of Web Setting up psycopg2 connection ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- D Web closing psycopg2 connection ---#

def close_db_connection(app_code,location_code):
        sublocation="D (close_db_connection) - "

        print (app_code,location_code,sublocation," starting connection shut down")

        #Closing connection with database
        cur.close()
        print (app_code,location_code,sublocation," closed cursor")
        conn.close()
        print (app_code,location_code,sublocation," closed connection")

        print (app_code,location_code,sublocation," finished connection shut down")
        return


#--- D End of Web closing connection with database ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- E Web creating user  ---#


def user_creator(app_code,location_code,source, user_id, user_token, bot_token, team_id, team_name):

    sublocation="E (user_creator)"

    print (app_code,location_code,sublocation," creating user process")
    print (app_code,location_code,sublocation, " source: ", source, " user_id: ", user_id, " user_token: ", user_token, " bot_token: ", bot_token," team_id: ", team_id," team_name: ", team_name)

    #--- Web creating user ---#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Listing all table names as part of debug ---#

    print (app_code,location_code,sublocation," trying to fetch all tables")
    cur.execute("""SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'""")
    for table in cur.fetchall():
        print (app_code,location_code,sublocation,table)

    #--- End of Listing all table names as part of debug ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Listing all column names as part of debug ---#

    # Fetching all column names in named table, as part of debugging process
    print (app_code,location_code,sublocation,"success, trying to fetch all rows in users_and_actions")
    cur.execute("SELECT * FROM users_and_actions LIMIT 0")
    print (app_code,location_code,sublocation," successful fetch")
    colnames = [desc[0] for desc in cur.description]
    print (app_code,location_code,sublocation," columns in table are: ", colnames)

    #--- End of Listing all column names as part of debug ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Checking if user already exists ---#

    cur.execute("SELECT user_token FROM users_and_actions WHERE user_id = %(uid)s",{"uid": user_id})
    existing_token=cur.fetchone()

    print (app_code,location_code,sublocation," existing_token is ", existing_token)



    if existing_token!=None:
        # If user is not None, then it exists and we shouldn't repeat the creation process
        print (app_code,location_code,sublocation," user already created")
        cur.execute("SELECT * FROM users_and_actions WHERE user_id = %(uid)s",
                   {"uid": user_id})
        print (app_code,location_code,sublocation," web user_creator - fetching one result: ", cur.fetchone())
        print (app_code,location_code,sublocation," web user_creator - end of function")
        return

        #--- End of Checking if user already exists ---#
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Adding user ---#

    cur.execute("INSERT INTO users_and_actions (source, user_id, user_token, bot_token, team_id, team_name) VALUES (%s, %s, %s, %s, %s, %s);", (source, user_id, user_token, bot_token, team_id, team_name))

    print (app_code,location_code,sublocation," added ", user_id, " to users_and_actions")
    #Saving the data to the table
    conn.commit()
    print (app_code,location_code,sublocation," committed ",user_id," data")

    #--- End of Adding user ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Checking user record just added ---#

    #A process for retrieving records (thanks to https://stackoverflow.com/questions/1466741/parameterized-queries-with-psycopg2-python-db-api-and-postgresql)
    print (app_code,location_code,sublocation," recalling ", user_id, " only")
    cur.execute("SELECT user_id FROM users_and_actions WHERE user_id = %(uid)s",
               {"uid": user_id})
    print (app_code,location_code,sublocation," fetching new user ID: ", cur.fetchone())
    print (app_code,location_code,sublocation," recalling whole record")
    cur.execute("SELECT * FROM users_and_actions WHERE user_id = %(uid)s",
               {"uid": user_id})
    print (app_code,location_code,sublocation," fetching one result: ", cur.fetchone())
    print (app_code,location_code,sublocation," end of function")

    return

    #--- End of Checking user record just added ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#--- End of Web creating user ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- F updating columns  ---#


def update_columns(app_code,location_code,list_of_pairs, user_id):
    # Our update_columns process takes information and puts it
    # into our database the first two  arguments are just the application
    # and process portion, to offer more informative printouts within
    # the process. Within the square brackets, we give information
    # in pairs, first the column to update, then the information
    # to put in it, this means if we want to give lots of columns to
    # update we can just pass [column, value, column, value] etc.
    # the final argument is the unique user_id we use to identify
    # which record we're reading and updating from

    sublocation="F (update_columns)"

    print (app_code,location_code,sublocation," starting update_columns process")
    print (app_code,location_code,sublocation," defining column is user_id")
    print (app_code,location_code,sublocation," defining value is: ", user_id)


    #Process for updating records in the database (thanks to https://stackoverflow.com/questions/7458749/psycopg2-insert-update-writing-problem)


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Retrieving values before change ---#
    print (app_code,location_code,sublocation," retrieving values before change")
    # A process for retrieving records (thanks to https://stackoverflow.com/questions/1466741/parameterized-queries-with-psycopg2-python-db-api-and-postgresql)
    cur.execute("SELECT * FROM users_and_actions WHERE user_id = %s", (user_id,));

    print (app_code,location_code,sublocation," values as they are: ", cur.fetchone())

    #--- End of Retrieving values before change ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Changing values ---#

    #Creating a loop to go through all of the column value pairs that have been passed
    # As an FYI, the name of the table cannot be passed as a parameter, that has to be hard coded (https://stackoverflow.com/questions/13793399/passing-table-name-as-a-parameter-in-psycopg2)

    print (app_code,location_code,sublocation,"splitting list_of_pairs into update_pairs")

    #Process for splitting one list into list of lists (thanks to https://stackoverflow.com/questions/9671224/split-a-python-list-into-other-sublists-i-e-smaller-lists)
    update_pairs = [list_of_pairs[x:x+2] for x in range(0, len(list_of_pairs), 2)]
    print (app_code,location_code,sublocation,"list split into update_pairs")

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- Looping through pairs to make change ---#

    for pair in update_pairs:
        print (app_code,location_code,sublocation," splitting the column, value pair to acess column and value separately")
        print (app_code,location_code,sublocation," first pair is: ", pair)

        #Selecting the first item of the pair (which should always be the column)
        column=pair[0]
        print (app_code,location_code,sublocation," column to update is ", column)

        #Selecting the second item (which should always be the value)
        values_to_add= pair[1]
        print (app_code,location_code,sublocation," value to add to ", column, " is ", values_to_add)

        # In this part of the for loop - adding the value (thanks to http://initd.org/psycopg/docs/sql.html)
        # IMPORTANT, the only reason we can use string concatenation here (injecting the column value with a plus) is that
        # we are defining the column, user input cannot define what value that is, if users could define the column name
        # this would be at risk of sql injection.

        cur.execute("UPDATE users_and_actions SET "+column+"=%s WHERE user_id=%s", (values_to_add, user_id));

        # getting the number of updated rows
        updated_rows = cur.rowcount
        print (app_code,location_code,sublocation," number of rows updated = ", updated_rows)
        conn.commit()
        print (app_code,location_code,sublocation," committed data")
        print (app_code,location_code,sublocation," executed change, updated users_and_actions column: ", column, "to be ", values_to_add ," where user_id is ", user_id)
        cur.execute("SELECT "+ column +" FROM users_and_actions WHERE user_id= %s", (user_id,));
        print(app_code,location_code,sublocation," value after most recent change: ", cur.fetchone())

        #--- End of Looping through pairs to make change ---#
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

        #--- End of Changing values ---#
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    print(app_code,location_code,sublocation," retrieving values after change")
    cur.execute("SELECT * FROM users_and_actions WHERE user_id= %s", (user_id,));
    print(app_code,location_code,sublocation," values as they are post change: ", cur.fetchone())
    print(app_code,location_code,sublocation," end of function")

    print(app_code,location_code,sublocation," ending update_columns process")

    return

#--- End of F updating columns  ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- G checking database for a value  ---#

def check_database(app_code,location_code,user_id, column):
    # This takes a user_id and a column and returns the
    # column value where that user_id exists, the app_code
    # and location_code are just for print functions

    sublocation="G (check_database)"

    print (app_code,location_code,sublocation,"starting check_database process, user_id is: ", user_id)

    # A process for retrieving records (thanks to https://stackoverflow.com/questions/1466741/parameterized-queries-with-psycopg2-python-db-api-and-postgresql)
    # IMPORTANT, the only reason we can use string concatenation here (injecting the column value with a plus) is that
    # we are defining the column, user input cannot define what value that is, if users could define the column name
    # this would be at risk of sql injection.
    cur.execute("SELECT "+column+" FROM users_and_actions WHERE user_id = %(current_uid)s",{"current_uid": user_id})
    value=cur.fetchone()

    print (app_code,location_code,sublocation," ending check_database process")

    for item in value:
        # Unpacking items (thanks to https://stackoverflow.com/questions/34178172/psycopg2-selecting-timestamp-returns-datetime-datetime-wrapped-in-tuple-how-to)\
        item_to_use=item

    print (app_code,location_code,sublocation," ",column," is: ", item_to_use)

    # Returning the item we have retrieved
    return item_to_use

#--- End of G checking database for a value  ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#============================================= End Synchronous functions ===================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Process to activate app ---#

#This is necessary for any function to activate rather than app exiting with code 0

#----------#

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')


#-----------------------------------#

#--- End of process activating app ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
