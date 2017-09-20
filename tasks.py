


#----------------------------------------Background worker process----------------------------------------#








#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
#                                               Important                                                  #

# if you have any questions about this code which aren't answered below, check the app.py file in this same
# repository which has more notes.

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#












#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Imports ---#
# Throughout this program we call the below imports for various actions
# failing to import one of these libraries, or importing the wrong one
# may be one reason for an app just failing mid-process


# All of these libraries need to be reflected in our requirements file
# which we upload as part of our app

import celery
from celery import Celery
app = celery.Celery('example')

import os


from slackclient import SlackClient

from flask import Flask, make_response, request

import gspread
import oauth2client
from datetime import datetime, time, date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import json

import os.path
import sys

import requests

import re

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
    import apiai
from collections import Counter
import time

import tasks

import psycopg2
from flask.ext.sqlalchemy import SQLAlchemy
#Thanks to http://blog.y3xz.com/blog/2012/08/16/flask-and-postgresql-on-heroku

import urllib.parse
#Thanks to https://stackoverflow.com/questions/45133831/heroku-cant-launch-python-flask-app-attributeerror-function-object-has-no


#--- End of imports ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Environment variables ---#

# For everything in this block, make sure you have created
# an environment variable with a name identical to the green
# quoted text (on heroku the REDIS ones will be done for you).

# Instructions for how to create environment variables in Heroku are at (https://devcenter.heroku.com/articles/config-vars)

# Environment variables are a way of protecting important
# pieces of information, particularly if you are sharing
# the code. Rather than writing out a bunch of passwords
# you save them elsewhere and you can refer to them here
# it can be a way of saving important information without
# having to create a database however if someone gets acess
# to your application and knows what they are called they will
# be able to get that information (though if they have got that
# far it's a bit of a problem anyway).



#Slack variables
#
# We set these variables based on information from our Slack bot
client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
#
#-#


# Celery variables
# Thanks to (https://devcenter.heroku.com/articles/celery-heroku, for another good resource on celery and flask, but which had to be modified due to clash with database, go to https://blog.miguelgrinberg.com/post/using-celery-with-flask)
app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])



# Authentication for sending message to API.AI
api_bearer = os.environ["API_BEARER"]

# The location of the google sheet (so the link isn't shared with everyone)

google_sheet_url= os.environ["GSHEET_ID"]

#--- End of environment variables ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- w1 add - async task caled by main process, testing call working ---#

@app.task
def add(app_code,location_code,x, y):
    print (app_code,location_code,"begun")
    print (app_code,location_code,"answer is", x+y)
    return x + y

#--- End of test ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#




#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
# w2 send_to_api - takes information from Slack message and converts it into a request to API.AI (not a response to an API.AI request)

@app.task
def send_to_api(event_id, user_id, channel, query):
    #Process for taking message and sending important info to API.AI

    #------------------------------------------------------------#
    # Setting location codes, these will be used in print commands
    # so we can easily keep track of where things are. The only
    # purpose of these is to be included in the print commands
    # however if they are removed the app will break at the first
    # print
    #------------------------------------------------------------#
    app_code="async "
    location_code="w1 (startup)"
    #------------------------------------------------------------#
    # End of setting location codes
    #------------------------------------------------------------#

    #Printing out all the information we have to confirm we've got everything
    print (app_code,location_code," activated with 'send_to_api' function")
    print (app_code,location_code," received event_id: ", event_id)
    print (app_code,location_code," received user: ", user_id)
    print (app_code,location_code," received channel: ", channel)
    print (app_code,location_code," received query: ", query)
    session_id=user_id
    print (app_code,location_code," received session_id: ", session_id)

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- w1.1 check to make sure the message we received isn't a duplicate of the last  ---#

    # Finding out whether the current query is within two minutes of the last one
    # (thanks to https://stackoverflow.com/questions/6205442/python-how-to-find-datetime-10-mins-after-current-time
    # and https://stackoverflow.com/questions/10048249/how-do-i-determine-if-current-time-is-within-a-specified-range-using-pythons-da

    location_code="w1.1 (deduplication)"

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

    print (app_code,location_code, user_id," most recent query is ", most_recent_query)

    # Retrieving the time it is now, then calculating what time
    # it would have been one minute ago
    now = datetime.now()
    print (app_code,location_code," now is ", now)

    one_minute_ago=datetime.now()-timedelta(minutes=1)
    print (app_code,location_code," one minute ago is: ", one_minute_ago)

    # Creating existing_query_list and duplicate_query variables now so that
    # program doesn't fall over when we check whether the value is "yes" or
    # "no" later. You'll see what these demark further on in the process.
    # We could potentially deal with this by instead checking whether the
    # variable exists further on but this seems more deliberate.
    within_last_query_window="no"
    existing_query_list="no"
    duplicate_query="no"

    if "||" in most_recent_query:
        # If there are no strings that contain the delimiters we
        # add when we receive a message it is the first message
        # so we don't need to worry about deduping
        print (app_code,location_code," query list contains ||")
        most_recent_query_list=most_recent_query.split("||")
        existing_query_list="yes"
        print (app_code,location_code," query list split: ", most_recent_query_list)
        list_position=0
        for x in most_recent_query_list:
            # The database will return up to 10 most recent queries
            if "--" in x:
                print (app_code,location_code," query contains --")
                query_pair=x.split("--")
                past_query=query_pair[0]
                print (app_code,location_code," query checking against is: ", past_query)
                print (app_code,location_code," query sent is: ", query)
                past_query_time_string=query_pair[1]
                print (app_code,location_code," time checking against is: ", past_query_time_string)
                print (app_code,location_code," threshold is: ", one_minute_ago)
                # converting datestamp string into queryable timestamp thanks to https://stackoverflow.com/questions/12672629/python-how-to-convert-string-into-datetime
                past_query_time_stamp=datetime.strptime(past_query_time_string, "%Y-%m-%d %H:%M:%S.%f")

                print (app_code,location_code," time converted to timestamp is: ", past_query_time_stamp)
                if one_minute_ago < past_query_time_stamp:
                    # If less than one minute have passed since
                    # last query it's more likely to be duplicate
                    print (app_code,location_code," less than one minute since last recorded action")
                    within_last_query_window='yes'
                    if query==past_query:
                        # If the current query is identical to the last query
                        # then it's a sign that we've had a repeated request
                        # from Slack
                        print (app_code,location_code," query is duplicate of last")
                        duplicate_query="yes"
                        # Here, regardless of whether the query is duplicate or not, we are updating
                        # our list of recent queries with the current time, this should mean that duplicate
                        # queries will always be removed (this is why we can keep the checked time period so short)
                        # we run the next section to remove the last query and replace it with this most recent one
                        if list_position==0:
                            print (app_code,location_code," list position==0")
                            # If the duplicate item is the first in the list then we replace that item
                            previous_queries=most_recent_query_list[-15:]
                            # Joining list elements into string (example here: https://stackoverflow.com/questions/12453580/concatenate-item-in-list-to-strings)
                            query_record=query+"--"+str(now)
                            new_query_list=query_record+"||"+("||".join(previous_queries))
                            print (app_code,location_code," new query list is: ", new_query_list)
                        else:
                            print (app_code,location_code," list position!=0")
                            # If the duplicate item is more than 0 we split the list to remove that item and
                            # replace it with the new one
                            query_record=query+"--"+str(now)
                            pre_duplicate=list_position-1
                            post_duplicate=len(most_recent_query_list)-(list_position+1)
                            print (app_code,location_code," position is ", post_duplicate, "before end of list")
                            previous_queries_pre=most_recent_query_list[0:pre_duplicate]
                            print (app_code,location_code," items before are ", previous_queries_pre)
                            previous_queries_post=most_recent_query_list[-post_duplicate:]
                            print (app_code,location_code," items after are ", previous_queries_post)
                            new_query_list=("||".join(previous_queries_pre))+"||"+query_record+"||"+("||".join(previous_queries_post))
                            print (app_code,location_code," new query list is: ", new_query_list)
                        # breaking out of for loop (thanks to https://www.tutorialspoint.com/python/python_break_statement.htm)
                        break
                    # We're using this to keep track of where we are in the list that we've saved
                    # if the item matches all of our conditions as above it won't hit this block to
                    # increase the value of list_position
                    list_position=list_position+1

                else:
                    # If more than one minute have passed we're
                    # assuming it's not a repeated send from Slack
                    # this allows a user to place exactly the same
                    # order without having to worry about varying
                    # their wording
                    print (app_code,location_code," more than one minute since last recorded action")
                    # We're using this to keep track of where we are in the list that we've saved
                    # if the item matches all of our conditions as above it won't hit this block to
                    # increase the value of list_position
                    list_position=list_position+1

    if existing_query_list!='yes':
        print (app_code,location_code," query list doesn't contain ||")
        print (app_code,location_code,"query is: ", query, " recalled query list is: ", most_recent_query)
        query_record=query+"--"+str(now)
        new_query_list=query_record+"||"
    else:
        if within_last_query_window!='yes' or duplicate_query!='yes':
            print (app_code,location_code,"not a duplicate query")
            # If EITHER there are no duplicate queries or the duplicate queries didn't occur within
            # our window then we just drop the earliest item from our list and add the newest query
            query_record=query+"--"+str(now)
            # Joining list elements into string (example here: https://stackoverflow.com/questions/12453580/concatenate-item-in-list-to-strings)
            new_query_list=("||".join(most_recent_query_list[1:15]))+"||"+query_record
            print (app_code,location_code," new query list is: ", new_query_list)

    if not new_query_list:
        print (app_code,location_code,"there is a problem - new_query_list hasn't been defined")

    # Using update_columns process to record most recent
    # query for future checks
    update_columns(app_code,location_code,['most_recent_user_query',new_query_list], user_id)


    if within_last_query_window=='yes':
        if duplicate_query=="yes":
            print (app_code,location_code," replaced duplicate query")

            close_db_connection(app_code,location_code)

        #------------------------------------------------------#
        #//////////////////////////////////////////////////////#
        #============  Database closed within if ==============#
        #//////////////////////////////////////////////////////#
        #------------------------------------------------------#

            return
            #----- Process ended because repeat message -----#



    location_code="w1.2 (genuine message)"
    print (app_code,location_code," recorded unique query")

    #--- End of w1.1 check to make sure the message we received isn't a duplicate of the last ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- w2 Check database for existing record data ---#



    location_code="w2 (check for record)"

    # Retrieving any saved user name for the user id that we have been given by the main process
    user_name=check_database(app_code,location_code,user_id, "user_name")
    print (app_code,location_code,"finished checking for user at ")

    # This ignored_value is to allow debugging, when you are testing and asked for your
    # username, set it to match this value, then every time you use the application you
    # will be asked again
    ignored_value="Sean"

    # When we create users through the Slack authorisation process (in our main app)
    # we save the user token in our database, now we use our check database process
    # to retrieve it, allowing us to post to any Slack channel they permiss
    user_token=check_database(app_code,location_code,user_id, 'user_token')

    bot_token=check_database(app_code,location_code,user_id, "bot_token")
    print (app_code,location_code," bot token is: ", bot_token)


    #--- End of w2 Check database for existing record data ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.0 start interaction with API.AI ---#
    location_code="w3.1 (contact api)"

    print (app_code,location_code,"web - user_name is ",user_name)

    if user_name!=None and user_name!=ignored_value:

        # Setting the information we're sending to API.AI if there IS a name (ignoring our ignored value)
        data="{'query':'"+query+"', 'lang':'en', 'contexts':[{ 'name': 'internal', 'parameters':{'moniker': '"+user_name+"'}, 'lifespan': 4}], 'sessionId':'"+session_id+"'}"

    else:
        # Setting the data we're sending to API.AI if there ISN'T a name
        data='{\'lang\':\'en\',\'sessionId\':'+session_id+',\'query\':\''+query+'\',\'originalRequest\':{\'source\':\'slack\',\'data\':{\'event\':{\'channel\':\''+channel+'\',\'user\':\''+user_id+'\'}}}}'

    # Activating process for sending query to API.AI (see "synchronous functions" section at bottom)
    response=send_query(app_code,location_code,data)


    #--- End of W3.0 start interaction with API.AI ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.1 receive response from API.AI ---#
    # We actually got the response at the end of the last step, we called for it when we wrote
    # "response=" so now we're just pulling out the information

    location_code="w3.2 (receive api response)"


    print (app_code,location_code,"Successfully posted to API.AI")

    # Processing pulling info from closed return response from API.AI
    # this closed loop means we don't need to worry so much about messages getting waylaid
    # this process only sends to Slack when it has received the correct message from
    # API.AI

    print (app_code,location_code," response from API.AI: ", response)
    print (app_code,location_code," response content: ", response.content)
    api_response = response.json()

    # Pulling out the portion of the response called "result" which
    # contains much of the information we need
    api_response_result=api_response.get("result")
    print (app_code,location_code," got result")

    # In API.Ai you can a response that it will give for certain inputs
    # so for example, when someone asks for food, our API.AI setup can
    # respond that it'll write that down. In this app we overwrite those
    # responses with our own text but if you don't want to you can just
    # find "speech" within "fulfillment" in the response (as below)
    fulfillment=api_response_result.get("fulfillment")
    speech_to_send=fulfillment.get("speech")
    print (app_code,location_code," speech to send: ",speech_to_send)

    # We set actions in API.AI as a shorthand for what should be done
    # in this application if the user is asking for food in the formatted
    # "I want food" we set "food" as action, so when we get a message with
    # the action "food" we know we need to run through the food process, whereas
    # if if we see that we've set the action "name-is" we know we need to run
    # through the process of setting a user name
    action=api_response_result.get("action")
    print (app_code,location_code," action is: ", action)


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- W3.2 action is food  ---#



    if action=="food":
        # If the user says "I want [food]" and isn't within another context we have set
        # API.AI will find the [food] value for us, save it in contexts and set the action "food"
        # so we know where to look

        #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
        #
        #--- W3.2.1 action is food and we don't have a user name ---#

        if user_name==None or user_name==ignored_value:
            location_code="w3.2.1 (food no-name)"
            # If the user hasn't used the application before we want them to set their username
            # as a first step. So if they have asked for food but we don't have a username, instead
            # of communicating with the user straight away we go back to API.AI and create an event
            # which tells it to expect a user name next, THEN we go back to the user and ask for
            # their name

            # Sending no-name event to API.AI (thanks to https://api.ai/docs/events#invoking_event_from_webhook)
            # this data is of a different format to the text we sent before - if you include an "event" as below
            # API.AI doesn't need text.

            data='{\'event\':{ \'name\': \'food-no-name\', \'data\': {\'source\': \'slack\'}}, \'lang\':\'en\', \'sessionId\':\''+user_id+'\'}'

            # Printing what we're sending for debugging
            print (app_code,location_code," data is: ",data)

            print (app_code,location_code,"sending message to API.AI")

            # Sending second consecutive message to API.AI to prepare it
            # for when the user gives their name

            # Activating process for sending query to API.AI (see "synchronous functions" section at bottom)
            response_2=send_query(app_code,location_code,data)


            # Gathering the data from the response the same way that
            # we did from the first response
            print (app_code,location_code,"response_2: ", response_2)
            print (app_code,location_code,"response_2 content: ", response_2.content)
            api_response_2 = response_2.json()

            # Getting the "result" the same way we did before
            api_response_result_2=api_response_2.get("result")
            print (app_code,location_code,"w3 - got result")

            # Getting fulfillment and API.AI's speech response
            # as we did before
            fulfillment_2=api_response_result_2.get("fulfillment")
            speech_to_send=fulfillment_2.get("speech")

            # This time we use the speech that API.AI has sent to us
            # we defined this speech in the API.AI platform in the response
            # section
            print (app_code,location_code,"speech to send",speech_to_send)

            # At this point getting the "action" isn't important for the function
            # of our program, because it should only ever reach this point if API.AI
            # is sending the response to the event we created above, which should
            # always be the same, we're getting it and printing it for debugging.
            action_2=api_response_result_2.get("action")
            print (app_code,location_code,"w speech_to_send - action_2 is ", action_2)

            # Sending message to slack which includes the defined speech from API.AI

            # The user token is what we got from our database earlier in the process
            # and will make Slack accept the messages we're sending.

            # This process is from https://api.slack.com/methods/chat.postMessage, there
            # is also a form-based message tester available on that page so you can test and debug

            params = (
            ('token', user_token),
            ('channel', channel),
            ('text', speech_to_send),
            ('username', 'vietnambot'),
            ('icon_emoji', ':rice:'),
            ('pretty', '1'),
            )

            requests.get('https://slack.com/api/chat.postMessage', params=params)

            print (app_code,location_code,"sent to Slack")

            close_db_connection(app_code,location_code)



        #------------------------------------------------------#
        #//////////////////////////////////////////////////////#
        #============  Database closed WITHIN IF ==============#
        #//////////////////////////////////////////////////////#
        #------------------------------------------------------#


            return

        #
        #
        #--- End of W3.2.1 action is food and we don't have a user name ---#
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#




        #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
        #
        #--- W3.2.2 action is food and we DO have a user name ---#
        #
        #

        if user_name!=None and user_name!=ignored_value:
            # This is for the eventuality that we have the user name saved

            location_code="w3.2.2 (food yes-name)"


            print (app_code,location_code,"user_id: ", user_id)
            print (app_code,location_code,"user_name: ", user_name)

            # The contexts is where API.AI saves the information for us
            contexts = api_response_result.get("contexts")
            print (app_code,location_code," contexts is: ", contexts)

            # Here we are running through all of the "contexts" one by one - essentially information API.AI has stored for us
            # 'name' does not mean user name, it means the name of the context we are accessing
            # the code means, for every item in the list called contexts, do the following things to that item
            for context in contexts:
                name=context.get("name")

                # Here we COULD access "food.original", this would work if we didn't have to ask for any other information,
                # however, we have set API.AI to save the food information in the "food-followup" context so this information is
                # there regardless of other information asked, this is basically making the application more robust
                if name == "food-followup":

                    # Accessing the information within the context
                    parameters=context.get("parameters")
                    # Finding the food field and naming it
                    food=parameters.get("food")
                    print (app_code,location_code,"web - food: ", food, datetime.utcnow())

                    # This is sending all the information we've gathered to a worker proces which can now update
                    # our Google sheet and update the user. We're doing this asynchronously because the GSheet api is
                    # too slow, we need to respond to API.AI in the short term and fortunately we can just send an
                    # extra update to Slack once that's done. If we were working with speech a platform like Google Home
                    # or Amazon Alexa this would not be possible

            # Getting the speech that has been sent back from API.AI
            api_response = response.json()
            api_response_result=api_response.get("result")
            print (app_code,location_code," got result")
            fulfillment=api_response_result.get("fulfillment")
            speech_to_send=fulfillment.get("speech")
            print (app_code,location_code," speech to send",speech_to_send)

            # The team_id is important because if multiple teams were using
            # this application, each updating their own order list, we would need
            # to calculate who is ordering most differently for each so we use team_id
            # to identify this teams top orderer (here called top_nommer)
            team_id=check_database(app_code,location_code,user_id, 'team_id')


            # Updating our database with the latest order so that it can be called
            # at other times
            update_columns(app_code,location_code,['most_recent_user_food',food],user_id)


            # Look in the synchronous functions section at the bottom of this code
            # for what this does
            process_food(app_code,location_code,food, channel, user_token, user_name, user_id, session_id, team_id, bot_token)

            close_db_connection(app_code,location_code)

        #------------------------------------------------------#
        #//////////////////////////////////////////////////////#
        #============  Database closed WITHIN IF ==============#
        #//////////////////////////////////////////////////////#
        #------------------------------------------------------#
            return

        #
        #
        #--- End of W3.2.2 action is food and we DO have a user name ---#
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #
    #
    #--- End of W3.2 action is food ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.3 action is food-fallback  ---#
    #


    # This is the case that the user hasn't said "I want [food]" or anything else that
    # matches our intents. Fallback is a catch all in API.AI that can have greater or lesser
    # scope to deal with statements that fall outside of what we have prepared for. We are assuming,
    # based on the narrow use of this app, that if a user just says something it will be the food
    # they want to order so we haven't put any necessary input contexts on this.
    # More complex applications will need more sophisticated fallback functions involving more contexts



    if action=="food-fallback":

        # Because this is a fallback intent with no context we can't trust that we've properly interpreted
        # the information so we have an instruction in API.AI asking user to give a food request that we're set up
        # to interpret (see the top of app.py for how we respond to food-fallback and how we interpret food)

        # Sending message to slack which includes the speech_to_send which we got from from API.AI before

        # The user token is what we got from our database earlier in the process
        # and will make Slack accept the messages we're sending.

        # This process is from https://api.slack.com/methods/chat.postMessage, there
        # is also a form-based message tester available on that page so you can test and debug

        params = (
        ('token', user_token),
        ('channel', channel),
        ('text', speech_to_send),
        ('username', 'vietnambot'),
        ('icon_emoji', ':rice:'),
        ('pretty', '1'),
        )
        requests.get('https://slack.com/api/chat.postMessage', params=params)


        close_db_connection(app_code,location_code)

    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database closed WITHIN IF ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#
        return


#
#
#--- End of W3.3 action is food-fallback ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    print (app_code,location_code,"action isn't food or food-fallback")

    if action=="name-is" or action=="name-confirmation":
        print (app_code,location_code,"action is defining name")
        # As part of the logic in our worker process if we don't already have the user's name, we ask for it
        # We have primed API.AI to wait for this name and when it comes, send it with the "name-is" action
        # There is also the possibility that users will say something other than their username so we have
        # included a fallback intent. That requires different processing so we haven't bundled it here, however
        # we HAVE bundled "name-confirmation" which occurs when the user confirms that what they said was their
        # username, because the processing is similar.


        #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
        #
        #--- W3.4 action is name-is  ---#
        #

        # This is the case where the user says something like "My name is [name]"
        # because we have put API.AI in the context where it's expecting a name
        # this is very easy for it to interpret and it saves the name for us in contexts

        if action == "name-is":
            location_code="w3.4 (name-is)"

            print (app_code,location_code," action is name-is ")


            # Contexts is where API.AI saves the information for us
            contexts = api_response_result.get ("contexts")

            # Here we are running through all of the "contexts" one by one - essentially information API.AI has stored for us
            # 'name' does not mean user name, it means the name of the context we are accessing
            # the code means, for every item in the list called contexts, do the following things to that item
            for context in contexts:
                name=context.get("name")

                # Because the user sent the food they want in their FIRST message, not the one we're
                # dealing with at the moment, we just need to check the context that API.AI saved at that point
                # and use that value. We could also have saved this value to our database then but that's unecessary
                # work as API.AI takes care of this for us.
                # As above, we can continue to use the food-followup context because this won't change too quickly
                if name == "food-followup":
                    parameters=context.get("parameters")
                    food=parameters.get("food")
                    print (app_code,location_code,"web - food:", food)

                # We called the context where we save the name in this instance 'name-is' so that is where
                # API.AI has put this information for us
                if name == "name-is":
                    parameters=context.get("parameters")
                    user_name=parameters.get("user_name")
                    print (app_code,location_code,"web - name to be set as: ", user_name)

            #Updating our database with the new information
            update_columns(app_code,location_code,['user_name',user_name,'most_recent_user_channel',channel,'most_recent_user_session_id',user_id,'most_recent_action_for_user','process_food','most_recent_user_food',food],user_id)

            #Notice we don't include "return" here - once we hit this point the code skips over "else" and keeps running until it gets to "return"
            # this is because we have the same information here regardless of whether it's "name-is" or "name-fallback" so doing it this way
            # means we only write the next bit of code once

        else:

        #--- End of W3.4 action is name-is ---#
        #
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


        #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
        #
        #--- W3.5 action is name-confirmation  ---#
        #




            if action=="name-confirmation":
                location_code="w3.5 (name-confirmation)"
                # Contexts is where API.AI saves all our information for us
                contexts = api_response_result.get ("contexts")
                print (app_code,location_code," contexts are: ", contexts)
                for context in contexts:
                    name=context.get("name")


                    # Because the user sent the food they want in their FIRST message, not the one we're
                    # dealing with at the moment, we just need to check the context that API.AI saved at that point
                    # and use that value. We could also have saved this value to our database then but that's unecessary
                    # work as API.AI takes care of this for us.
                    # As above, we can continue to use the food-followup context because this won't change too quickly
                    if name == "food-followup":
                        parameters=context.get("parameters")
                        food=parameters.get("food")
                        print (app_code,location_code,"food is", food)

                    # Here, because the user has confirmed that this is their name, we are retrieving the context
                    # that we set in the name-fallback response (in the if block directly above this). API.AI
                    # saved that information for us under the name we supplied.
                    if name == "potential-name":
                        parameters=context.get("parameters")
                        user_name=parameters.get("name")
                        print (app_code,location_code,"name is", user_name)

                # Updating our database with the confirmed name
                update_columns(app_code,location_code,['user_name',user_name,'most_recent_user_channel',channel,'most_recent_user_session_id',user_id,'most_recent_action_for_user','process_food','most_recent_user_food',food],user_id)

                print (app_code,location_code," finished adding user ")

                # Notice we don't include "return" here - once we hit this point the code just runs the next few lines it gets to "return"
                # this is because we have the same information here regardless of whether it's "name-is" or "name-fallback" so doing it this way
                # means we only write the next bit of code once


        # The team_id is important because if multiple teams were using
        # this application, each updating their own order list, we would need
        # to calculate who is ordering most differently for each so we use team_id
        # to identify this teams top orderer (here called top_nommer)
        print (app_code,location_code,"checking for team_id")
        team_id=check_database(app_code,location_code,user_id, 'team_id')

        # Starting the process of putting the order into the spreadsheet
        # the process_food includes sending messages to Slack so we don't
        # need to include any confirmation messages here
        print (app_code,location_code," got team_id, starting process_food process")
        process_food(app_code,location_code,food, channel, user_token, user_name, user_id, session_id, team_id, bot_token)


        close_db_connection(app_code,location_code)

    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database completely closed =============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#

        # HERE we include return, which ends our process
        return


    #--- End of W3.5 action is name-confirmation ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.6 action is name-fallback  ---#
    #



    # This is the case that the user hasn't said "I am [name]" or anything else that
    # matches our intents. Because we've just asked for a name it's quite likely that
    # they have just said it, however we need to check

    if action == "name-fallback":
        location_code="w3.6 (name-fallback)"

        print (app_code,location_code," action is name-fallback")

        # Because this is fallback we can't assume that the string given is
        # necessarily the users name so we need to save it to API.AI and check
        # with the user whether that is correct (importantly we don't save this
        # value to our database at this point because if the user doesn't respond
        # that it's incorrect in time the session might end and it would be harder
        # to set the proper name)

        user_name=api_response_result.get("resolvedQuery")
        print (app_code,location_code," potential user name is ", user_name)

        data = '[\n   {\n      "name": "potential-name",\n      "lifespan": 1,\n      "parameters": {\n         "name": "'+user_name+'"\n      }\n   }\n]'

        print (app_code,location_code," user_id is ", user_id, "data is", data)

        response_2=send_contexts(app_code,location_code,user_id,data)

        print (app_code,location_code," response is: ", response_2)

        print (app_code,location_code," response content: ", response_2.content)

        speech_to_send="I think you've asked me to create a user name of: "+user_name+" is that right?"

        params = (
        ('token', user_token),
        ('channel', channel),
        ('text', speech_to_send),
        ('username', 'vietnambot'),
        ('icon_emoji', ':rice:'),
        ('pretty', '1'),
        )
        requests.get('https://slack.com/api/chat.postMessage', params=params)


        close_db_connection(app_code,location_code)

    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database closed WITHIN IF ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#
        return

    #--- End of W3.6 action is name-fallback ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.7 action is name-incorrect  ---#

    # This is when the user responds to our name-fallback check by expressing in some way that
    # we got it wrong. We could have a complex process for managing this but for simplicity here
    # we just loop back to when we first asked for the user name. To do this, we use API.AI's contexts.
    # We make sure that this only outputs the food-followup and no-name contexts, and use the speech we've
    # set in API.AI as our response (see the top of app.py for how we set up API.AI)



    if action=="name-incorrect":

        location_code="w3.7 (name-incorrect)"

        # We use speech_to_send which is a variable we defined near the start of our code based on API.AI's
        # initial response
        print (app_code,location_code," speech_to_send is: ", speech_to_send)

        # We already retrieved the user_token and channel higher up in the process
        params = (
        ('token', user_token),
        ('channel', channel),
        ('text', speech_to_send),
        ('username', 'vietnambot'),
        ('icon_emoji', ':rice:'),
        ('pretty', '1'),
        )
        requests.get('https://slack.com/api/chat.postMessage', params=params)

        # Because we've set the name-incorrect intent in API.AI to only output
        # the food-followup and no-name contexts, we don't need to change that at all
        # now, when the user responds to our message we'll enter the loop just the same
        # as when we first sent them the message
        close_db_connection(app_code,location_code)

    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database closed WITHIN IF ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#
        return


    #--- End of W3.7 action is name-incorrect ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.8 action is give-deets  ---#
    #

    # When we've processed the number of orders we end up with a bunch
    # of potentially useful information about who has ordered today, and
    # what. However, it is a poor user experience to just dump all of that
    # information into a Slack message or spoken response so instead we record
    # that information in an API.AI context and give the user to ask for it or not



    if action=="give-deets":

        location_code="w3.8 (give-deets)"
        contexts = api_response_result.get ("contexts")
        print (app_code,location_code," contexts are: ", contexts)
        for context in contexts:
            name=context.get("name")

            # Because the user sent the food they want in their FIRST message, not the one we're
            # dealing with at the moment, we just need to check the context that API.AI saved at that point
            # and use that value. We could also have saved this value to our database then but that's unecessary
            # work as API.AI takes care of this for us.
            # As above, we can continue to use the food-followup context because this won't change too quickly
            if name == "order-list":
                print (app_code,location_code," order-list context: ", context)
                parameters=context.get("parameters")
                print (app_code,location_code," order-list parameters: ", parameters)
                orders=parameters.get("order-list")
                print (app_code,location_code,"order list is",orders)


        # Now we're deleting the contexts so that if our user sends any other messages they are part of a fresh session
        response=delete_contexts(app_code,location_code,user_id)

        print (app_code,location_code," response content: ", response.content)

        # Here the google sheet url is referencing an environment variable (set near the top) so we
        # aren't giving the url to everyone who reads this code
        speech_to_send="Ok, we have: "+orders+". If you'd like to order, go to https://caphehouse.orderswift.com/ and the link to the sheet is:"+str(google_sheet_url)

        print (app_code,location_code," message content: ", speech_to_send)
        print (app_code,location_code," message user token: ", user_token)
        print (app_code,location_code," message channel: ", channel)

        # We already retrieved the user_token and channel higher up in the process
        params = (
        ('token', user_token),
        ('channel', channel),
        ('text', speech_to_send),
        ('username', 'vietnambot'),
        ('icon_emoji', ':rice:'),
        ('pretty', '1'),
        )
        requests.get('https://slack.com/api/chat.postMessage', params=params)


        return

    #--- End of W3.8 action is give-me-deets ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.9 action is no-deets  ---#

    if action=="no-deets":

        location_code="w3.9 (no-deets)"

        response=delete_contexts(app_code,location_code,user_id)

        print (app_code,location_code," response content: ", response.content)

        speech_to_send="Ok great, if you'd like to order, go to https://caphehouse.orderswift.com/ and the link to the sheet is: "+str(google_sheet_url)

        # We already retrieved the user_token and channel higher up in the process
        params = (
        ('token', user_token),
        ('channel', channel),
        ('text', speech_to_send),
        ('username', 'vietnambot'),
        ('icon_emoji', ':rice:'),
        ('pretty', '1'),
        )
        requests.get('https://slack.com/api/chat.postMessage', params=params)


    #--- End of W3.9 action is no-deets ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.10 action is change-name  ---#
    #

    # Users may want to change the name that is used when they order,
    # this is a simple process to update the name associated with a specific
    # user ID


    if action=="change-name":

        location_code="w3.10 (change-name)"
        print (app_code, location_code, " user wants to change name")
        contexts = api_response_result.get ("contexts")
        print (app_code,location_code," contexts are: ", contexts)
        for context in contexts:
            name=context.get("name")

            # This request could come at any point, by selecting the context
            # called "new-name" we should be able to manage the response quite
            # easily, we also only currently accept requests of the form
            # "change my name to [new-name]" so we have all the information at
            # one time and don't need to worry about follow up questions or
            # fallback intents
            if name == "new-name":
                print (app_code,location_code," new-name context: ", context)
                parameters=context.get("parameters")
                print (app_code,location_code," new-name parameters: ", parameters)
                new_name=parameters.get("name")
                print (app_code,location_code," new name is",new_name)

        # Updating our database with the new name
        update_columns(app_code,location_code,['user_name',new_name,'most_recent_user_channel',channel,'most_recent_user_session_id',user_id,'most_recent_action_for_user','change-name'],user_id)

        # Confirming to the user that we made the change
        speech_to_send="Ok, I've changed your name to "+new_name

        print (app_code,location_code," message content: ", speech_to_send)
        print (app_code,location_code," message user token: ", user_token)
        print (app_code,location_code," message channel: ", channel)

        # We already retrieved the user_token and channel higher up in the process
        params = (
        ('token', user_token),
        ('channel', channel),
        ('text', speech_to_send),
        ('username', 'vietnambot'),
        ('icon_emoji', ':rice:'),
        ('pretty', '1'),
        )
        requests.get('https://slack.com/api/chat.postMessage', params=params)


        return

    #--- End of W3.10 action is change-name ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#




    # Future plans:
        # "my usual" which will save a food as their usual order so that they can just recall that again in future
        # "todays-orders" which will allow getting the information about today's orders without having to go through the ordering process

    # In the interests of getting this out we are putting off the above for now


    #|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
    #
    #--- W3.11 action is anything else  ---#

    location_code="w3.11 (any-other-action)"

    # Because everything above this is an IF statement which ends in a "return" (ending the process)
    # we can treat all of that as closed off. Here we write code that executes if NONE of the above
    # if statements are true - it's a way for us to easily pass through responses from API.AI that don't
    # require processing on this end, so we can add conversational back and forths easily


    # We're not interfering with the message here, we're just taking the response
    # that API.AI sent us initially, and passing that straight on to Slack
    print (app_code,location_code," speech_to_send is: ", speech_to_send)

    # We already retrieved the user_token and channel higher up in the process
    params = (
    ('token', user_token),
    ('channel', channel),
    ('text', speech_to_send),
    ('username', 'vietnambot'),
    ('icon_emoji', ':rice:'),
    ('pretty', '1'),
    )
    requests.get('https://slack.com/api/chat.postMessage', params=params)

    return

    #--- End of W3.11 action is anything else ---#
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



#--- End of all main code ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#============================================= Synchronous functions =======================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


# These are the functions we call in the main code


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#w-A process_food


def process_food(app_code,location_code,food, channel, user_token, user_name, user_id, session_id, team_id, bot_token):
    # This function takes the user name and adds their order and name
    # to the shared order spreadsheet. It then calculates who has ordered
    # today, gets the value of who has ordered most, and messages the user
    # in the channel that they made their original request in (meaning that
    # this process will also work properly in shared channels, not just direct ones)


    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database connection open  ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#

    sublocation= "A (process_food) - "

    print (app_code,location_code,sublocation,"w4 process_food - user_id: ", user_id)
    print (app_code,location_code,sublocation,"w4 process_food - user_name: ", user_name)
    print (app_code,location_code,sublocation,"w4 process_food - user_token: ", user_token)
    print (app_code,location_code,sublocation,"w4 process_food - session_id: ", session_id)
    print (app_code,location_code,sublocation,"w4 process_food - channel: ", channel)
    print (app_code,location_code,sublocation,"w4 process_food - food: ", food)
    print (app_code,location_code,sublocation,"w4 process_food - team_id: ", team_id)

    #Sending message to slack confirming order and signalling that will update with order status

    # The user token is what we got from our database earlier in the process
    # and will make Slack accept the messages we're sending.

    # This process is from https://api.slack.com/methods/chat.postMessage, there
    # is also a form-based message tester available on that page so you can test and debug
    params = (
    ('token', user_token),
    ('channel', channel),
    ('text', 'Ok '+food+' for '+user_name+'. Got it, I\'ll just update the sheet now and I\'ll let you know when I\'m done. :rice:'),
    ('username', 'vietnambot'),
    ('icon_emoji', ':rice:'),
    ('pretty', '1'),
    )
    requests.get('https://slack.com/api/chat.postMessage', params=params)

    #---------------------------------------#


    # Authorising access to gsheet the below is for when using in the app (thanks to http://gspread.readthedocs.io/en/latest/oauth2.html)

    # You will need to create the json file referenced below (starting My Project) and upload it to wherever you are
    # hosting this code. You will also need to find the url of your Google sheet, and set it as an ENVIRONMENTAL variable
    # instructions for how to create an environmental variable on Heroku are here: https://devcenter.heroku.com/articles/config-vars#setting-up-config-vars-for-a-deployed-application

    # If you consistently can't access the sheet you may have not set up the permissions properly
    # Try sharing the sheet with your SERVICE ACCOUNT email address and see what happens

    # Printing for debugging
    json_key = json.load(open('vietnambot-2017-77539de66304.json'))
    print (app_code,location_code,sublocation, "json key is: ", json_key)

    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('vietnambot-2017-77539de66304.json', scope)

    # Opening the relevant google sheet by name (can also open by URL)
    gc = gspread.authorize(credentials)
    print (app_code,location_code,sublocation,"authorised, gc is: ",gc)
    vietnam = gc.open("Vietnamese orders")
    print ("sheet is ", vietnam)
    orders1 = vietnam.get_worksheet(0)
    print (app_code,location_code,sublocation," have called sheet 'orders1' ")

    #running the update_sheet program which takes the user information and adds them to the first empty row in the order sheet

    row=update_sheet(app_code,location_code,orders1,user_name,food)

    #-----------#

    # Sending message to slack confirming order and signalling that will update with order status
    # (see above for source and reasoning) of the process
    params = (
    ('token', user_token),
    ('channel', channel),
    ('text', 'Ok thanks '+user_name+' I\'ve ordered '+food+' for you. Hang on a sec and I\'ll let you know how we\'re doing for today\'s orders.'),
    ('username', 'vietnambot'),
    ('icon_emoji', ':rice:'),
    ('pretty', '1'),
    )
    requests.get('https://slack.com/api/chat.postMessage', params=params)

    #---------------------------------------#

    print (app_code,location_code,sublocation," have posted to Slack, starting check_order_numbers")


    #---------------------------------------#

    # Running the process that checks how many orders we've had and lets the user know how we're doing
    # This process also returns the variable "exists" which is a yes/no check of whether we've already
    # Created the top_nommer record, that's mainly to prevent us having to check again in the
    # calculating_top_nommer process

    exists=check_order_numbers(app_code,location_code,orders1, row, channel, session_id, user_token, user_name, user_id, team_id, bot_token)


    #-----#


    # Running the process that checks last 60 orders and updates the top nommer as the person who has ordered the most
    # For speed, our process doesn't use this value (as it won't change too quickly) it just gets the value from our
    # database and THEN runs through this process to update the database value for the next user. This just means we
    # are always one session behind with this value
    calculating_top_nommer(app_code,location_code,orders1, row, team_id, exists)

    #-----#
    print (app_code,location_code,sublocation," finishing process ")

    return


#--- End of w-A process_food ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#w-B update_sheet


def update_sheet(app_code,location_code,worksheet,user_name,food):

    # This takes the worksheet we got in process_food, finds the empty row to update, gets the date
    # and puts the date, food, and user name in there

    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database connection open  ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#

    sublocation= "B (update_sheet) - "

    #Proess for updating the first empty row in the sheet thanks to (https://gspread.readthedocs.io/en/latest/)
    print (app_code,location_code,sublocation," started update_sheet action ")

    #finding row of first empty cell
    print (app_code,location_code,sublocation," calling available_row function ")
    row_val=next_available_row(app_code,location_code,worksheet)

    print (app_code,location_code,sublocation," row val is: ", row_val)

    # Selecting the first cell in our row by using row_val and column 1 (this is the cell we want to update with the date)
    date_cell=gspread.utils.rowcol_to_a1(row_val, 1)
    print (app_code,location_code,sublocation,"date cell is ", date_cell)

    # This gets today's date
    today=str(date.today())
    print (app_code,location_code,sublocation,"today is ", today)

    # This formats today's date to be easily readable by humans
    today_formatted=datetime.strptime(today, '%Y-%m-%d').strftime('%d/%m/%Y')
    print (app_code,location_code,sublocation,"today formatted is ", today_formatted)

    # This updates the cell we selected
    worksheet.update_acell(date_cell, today_formatted)
    print (app_code,location_code,sublocation," added today's date: ", today)


    # Updating name on sheet using name value passed in function

    # Getting the second cell in our row
    moniker_cell=gspread.utils.rowcol_to_a1(row_val, 2)
    print (app_code,location_code,sublocation,"moniker_cell is", moniker_cell)

    # Using the value we got from our database as the name to put here
    worksheet.update_acell(moniker_cell, user_name)
    print (app_code,location_code,sublocation," added user_name: ", user_name)


    # Updating food cell in sheet using food value passed in function

    # Getting the third cell
    food_cell=gspread.utils.rowcol_to_a1(row_val, 3)

    # Putting in the food value we got from API.AI in this session
    worksheet.update_acell(food_cell, food)
    print (app_code,location_code,sublocation," added food: ", food)

    # Updating time cell in sheet using current time

    # Getting the fifth cell as where we'll put the time
    time_cell=gspread.utils.rowcol_to_a1(row_val, 5)

    # Getting the current time with datetime.now().time() and putting that value in the cell we selected
    worksheet.update_acell(time_cell, datetime.now().time())

    print (app_code,location_code,sublocation," added time: ", datetime.now().time())

    # We give back the row value because that's later used to calculate things like
    # the most prolific orderer of late
    return row_val


#--- End of w-B update_sheet ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#w-C check_order_numbers

def check_order_numbers(app_code,location_code,orders1, row, channel, session_id, user_token, user_name, user_id, team_id, bot_token):

    # Process for checking how many orders there have been so far today - this is longer because of lots of ifs
    # It takes the row number calculated in the update_sheet process, along with the data needed to contact our
    # user to message them

    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database connection open  ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#

    sublocation= "C (check_order_numbers) - "

    # Checking existing orders to give idea of current order state

    # Creating range of last 30 and next two rows to check recent orders (the next two being a failsafe in case someone ordered at the same time)
    print (app_code,location_code,sublocation," started order number check")

    # Current row number plus two
    row_plus_2=int(row)+2
    print (app_code,location_code,sublocation,"row_plus_2 is: ", row_plus_2)

    # Current row number minus 30
    row_minus_30=int(row)-30
    print (app_code,location_code,sublocation,"row_minus_30 is: ", row_minus_30)

    # Getting the first cell in the row-30
    past_30=gspread.utils.rowcol_to_a1(row_minus_30, 1)
    print (app_code,location_code,sublocation,"past_30 is: ", past_30)

    # Getting the first cell in the row+2
    next_2=gspread.utils.rowcol_to_a1(row_plus_2, 1)
    print (app_code,location_code,sublocation,"next_2 is: ", next_2)

    # Creating our range within the first column from row-30 to row+2
    dates=past_30+":"+next_2
    # Returns a list of everything in the date column in that range
    dates_range=orders1.range(dates)
    print (app_code,location_code,sublocation,"dates_range is: ", dates_range)

    #Getting today's date
    today=str(date.today())
    print (app_code,location_code,sublocation,"today is: ", today)

    # Formatting today's date to match the dates in the sheet
    today_formatted=datetime.strptime(today, '%Y-%m-%d').strftime('%d/%m/%Y')
    print (app_code,location_code,sublocation,"today_formatted is: ", today_formatted)
    #-----#

    # Getting top_nommer from our database (the person who has ordered the most in the last 60 orders)
    # after this we'll calculate that value again to refresh
    top_nommer=top_nommer_check(app_code,location_code,team_id)
    print (app_code,location_code,sublocation,"finished top nommer process, top_nommer is: ", top_nommer)


    # The very first time this app is used the top_nommer value won't have been calculated so the user could get a nonsensical response
    # a quick patch to handle that is just giving the current user the honourary title of "top_nommer" until we calculate the actual name
    # afterwards

    if top_nommer:
        exists="yes"
        print (app_code,location_code,sublocation,"top_nommer exists")
        print (app_code,location_code,sublocation,"top_nommer is: ", top_nommer)

    if not top_nommer:
        print (app_code,location_code,sublocation,"top_nommer is None")
        exists="no"
        top_nommer=user_name
    #-----#

    # Getting orders for today and creating a list of them
    # First creating an empty list to populate (otherwise Python gets confused)
    order_names=[]
    print (app_code,location_code,sublocation," order_names ", order_names)

    # We create two lists because one will just have names, the other will
    # have full details of the orders
    order_details=[]
    print (app_code,location_code,sublocation," order_details ", order_details)

    # Opening every row in the date range and getting the value from the date column. Where the date column
    # matches today's date (meaning the order is today's order) going to the second column (where names are saved)
    # then adding all of those names to the empty list we created
    for sheet_date in dates_range:
        # If the date in the cell matches today's date
        if today_formatted in sheet_date.value:
            # .row returns the row number
            date_row=str(sheet_date.row)

            # this uses the row number to get the food cell
            food_row="C"+date_row

            # this uses the row number to get the next cell along (name)
            name_row="B"+date_row

            # .value gets what is in the cell (otherwise is gets a cell object which is harder to use)
            order_names.append(orders1.acell(name_row).value)

            this_order=orders1.acell(food_row).value+" for "+orders1.acell(name_row).value

            order_details.append(this_order)

            # This will result in first printing one order, then two orders, then three orders, up to the full list (it'll print again
            # every time it adds another record) this can be useful to see the list being added together but can make for
            # messy logs, to fix that just unindent this line the following line
            print (app_code,location_code,sublocation," check_order_numbers - printing order names list as built:", order_details)

    #-----#


    # Checking length of order list to see if it meets minimum -
    # We don't bother checking if there have been no orders because getting to
    # this point should mean that there's at least one

    # If only one order (the length of the list of order names for today is less than 2)
    if len(order_names) <2:
        print (app_code,location_code,sublocation," one order")
        full_order_list=order_names
        # If the top_nommer is not that one order
        # This uses a python check to see if the value we have
        # for top_nommer appears in the list we have
        if top_nommer not in full_order_list:

            # Sending message to Slack - see other Slack messages for commented info
            params = (
                ('token', user_token),
                ('channel', channel),
                ('text', 'This is the first order, you should ask around to try to reach the three order daily minimum. I see that our current top nommer, '+top_nommer+' hasn\'t ordered yet. Maybe you should ask them.'),
                ('username', 'vietnambot'),
                ('icon_emoji', ':rice:'),
                ('pretty', '1'),
            )
            requests.get('https://slack.com/api/chat.postMessage', params=params)

            return exists

            #-----#


        # If we have only one order and it is from the current top nommer (this is the alternative to the if statement directly above)
        # if the order number is less than 2 and top_nommer IS in the list that means they are the one we're talking to
        else:
            #Sending message to Slack, the ":the_horns:" is slack specific markup that adds an image, as is :rice:
            params = (
                ('token', user_token),
                ('channel', channel),
                ('text', 'Unfortunately there is only one Vietnamese order which I can see so far, you should ask around to hit the three order minimum. Congratulations though, you\'re the current top nommer! :the_horns:'),
                ('username', 'vietnambot'),
                ('icon_emoji', ':rice:'),
                ('pretty', '1'),
            )
            requests.get('https://slack.com/api/chat.postMessage', params=params)

            return exists
            #-----#
        #----------#

    #If the number of orders is NOT under 2

    else:
        #If the number of orders IS under 3
        if len(order_names) <3:
            print (app_code,location_code,sublocation," two orders")

            # This joins the elements in our list, there should only be two so it makes sense to join them with an "and" in between them
            full_order_list=" and ".join(order_names)

            print (app_code,location_code,sublocation," order names are: ", full_order_list)

            # Sending the order_details to API.AI as a context, this allows us to ask the user whether they want more information and then, if they
            # say they do, provide it to them

            full_order_details=" and ".join(order_details)

            print (app_code,location_code,sublocation," order details are: ", full_order_details)


            data='[\n   {\n      "name": "order-list",\n      "lifespan": 3,\n      "parameters": {\n         "order-list": "'+full_order_details+'"\n      }\n   }\n]'

            print (app_code,location_code," user_id is ", user_id, "data is", data)

            print (app_code, location_code, "preparing to send order list as string to API.AI")
            response=send_contexts(app_code,location_code,user_id,data)


            print (app_code,location_code,sublocation," response from API.AI: ", response)
            print (app_code,location_code,sublocation," response content: ", response.content)


            #If the top nommer record doesn't appear in one of those two orders
            if top_nommer not in full_order_list:
                print (app_code,location_code,sublocation," top nommer not in list, sending to Slack")
                #Sending message to Slack
                params = (
                    ('token', user_token),
                    ('channel', channel),
                    ('text', 'Unfortunately we only have two Vietnamese orders so far, '+full_order_list+', you should ask the current Top Nommer, '+top_nommer+' to see if they would like to join.'),
                    ('username', 'vietnambot'),
                    ('icon_emoji', ':rice:'),
                    ('pretty', '1'),
                )
                requests.get('https://slack.com/api/chat.postMessage', params=params)
                #-----#

                # If the top nommer IS one of those two orders
            else:
                print (app_code,location_code,sublocation," top nommer not is in list")
                # If we're talking to the top_nommer (the name with the most orders matches the username for this user)
                if top_nommer==user_name:
                    print (app_code,location_code,sublocation," user is top_nommer")
                    # We're constructing this part of the message and will add it on afterward
                    signoff=". Congratulations by the way - you're the top nommer! :the_horns:"

                #If we're NOT talking to the top_nommer
                else:
                    # Constructing this end part of the message to add afterwards
                    print (app_code,location_code,sublocation," user isn't top_nommer")
                    signoff=" or ask the current top nommer "+top_nommer+ "."

                speech_to_send='Unfortunately we only have two Vietnamese orders so far, '+full_order_list+'. We need a minimum of three. You should ask around, maybe post in the London channel'+signoff
                #Sending message to Slack
                params = (
                    ('token', user_token),
                    ('channel', channel),
                    ('text', speech_to_send),
                    ('username', 'vietnambot'),
                    ('icon_emoji', ':rice:'),
                    ('pretty', '1'),
                )
                requests.get('https://slack.com/api/chat.postMessage', params=params)
                #-----#

        #----------#

        #If we have more than two orders (meaning we'll hit the three order minimum)
        else:
            if len(order_names) > 2:
                order_list_lenght=str(len(order_names))
                print (app_code,location_code,sublocation," three or more orders: ", order_list_lenght, " orders.")
                # Creating a string of the multiple orders, all apart from one are joined with a comma, the last is joined with an ", and" for grammatical accuracy

                # Getting all items in the list except the last one
                order_list=', '.join(order_names[:-1])

                # Getting only the last item in the list and joining that to the others using and instead
                full_order_list=order_list+", and "+order_names[-1]

                # Having more than three orders could result in a large dump of text to the user, this can be quite
                # jarring for the user and is poor user experience in text (even more so if working in speech) so instead
                # of just putting them all in, we offer our user the option to request details of who has ordered what

                # Getting all items in the list except the last one
                order_details_minus_1=', '.join(order_details[:-1])

                # Getting only the last item in the list and joining that to the others using and instead
                full_order_details=order_details_minus_1+", and "+order_details[-1]

                data = '[\n   {\n      "name": "order-list",\n      "lifespan": 3,\n      "parameters": {\n         "order-list": "'+full_order_details+'"\n      }\n   }\n]'

                print (app_code,location_code,sublocation," user_id is ", user_id, "data is", data)

                print (app_code, location_code, sublocation,"preparing to send order list as string to API.AI")
                response=send_contexts(app_code,location_code,user_id,data)

                print (app_code,location_code,sublocation," response from API.AI: ", response)
                print (app_code,location_code,sublocation," response content: ", response.content)

                #-----#



                #If the top nommer doesn't appear in one of the orders
                if top_nommer not in full_order_list:
                    print (app_code,location_code,sublocation," top nommer not in list, messaging Slack")
                    #Sending message to Slack celebrating hitting minimum and suggesting nudging top Nommer

                    speech_to_send='Great! We\'ve hit our three order minimum for today. Today we have '+str(order_list_lenght)+' orders. Although our current Top Nommer, '+top_nommer+', hasn\'t ordered yet. You could give them a nudge, or not, they\'ve had enough. Would you like the full order details?'
                    print (app_code,location_code,sublocation," speech to send is: ", speech_to_send)

                    #-----#

                else:
                    #Sending message to Slack celebrating hitting minimum but not suggesting top nommer as they have already ordered
                    #If we're talking to the top_nommer
                    if top_nommer==user_name:
                        print (app_code,location_code,sublocation," user is top nommer")
                        # Creating portion of text to add to the middle of our response
                        top_nommer_phrase=' Congratulations by the way - you\'re the top nommer! :the_horns:'

                    #If we're NOT talking to the top_nommer
                    else:
                        print (app_code,location_code,sublocation," user is not top nommer")
                        # Creating portion of text to add to the middle of our response
                        top_nommer_phrase=' Our top nommer, '+top_nommer+' has already ordered, of course they have'

                    speech_to_send='Great! We\'ve hit our three order minimum for today. So far we have '+str(order_list_lenght)+' orders today.'+top_nommer_phrase+'. Would you like the full order details?'

                    print (app_code,location_code,sublocation," sending speech: ", speech_to_send)

                # Process for sending option buttons to the user thanks to https://github.com/slackapi/python-message-menu-example/blob/master/example.py
                # This in part helps our deduplication program run without there being
                # problems that it will raise false flags

                slack_client = SlackClient(bot_token)

                attachments_json = [{
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "attachment_type": "default",
                "callback_id": "more info",
                "actions": [
                        {
                            "name": "more info",
                            "text": "sure",
                            "type": "button",
                            "value": "give me more info"
                        },
                        {
                            "name": "no thanks",
                            "text": "no thanks",
                            "type": "button",
                            "value": "no more info"
                        }

                    ]
            }
        ]


                print (app_code,location_code,sublocation," sending attachments: ", attachments_json)
                slack_client.api_call(
                  "chat.postMessage",
                  channel=channel,
                  text=speech_to_send,
                  icon_emoji=':rice:',
                  attachments=attachments_json
                )
        #---------------------------------------------------------------------#
    # Here were returning the value "exists" so that when we go to their create or update our top_nommer record we don't
    # need to check for existence again
    print (app_code,location_code," messaged Slack, returning 'exists' value")
    return exists


#--- End of w-B update_sheet ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#w-D calculating_top_nommer

#Process for finding who has ordered the most over the last sixty orders and updating the cell which records that
def calculating_top_nommer(app_code,location_code,orders1, row, team_id, exists):
#------------------------------------------------------#
#//////////////////////////////////////////////////////#
#============  Database connection open  ==============#
#//////////////////////////////////////////////////////#
#------------------------------------------------------#

    sublocation= "D (calculating_top_nommer) - "

    print (app_code,location_code,sublocation,"w8 - started top nommer check")
    # This process checks the last 60 order names, then selects the most repeated name and writes it into our database
    # for quick retrieval in future. The reason we do it this way around is that we don't want the user to be waiting too
    # long for a response so we get them a quick (if slightly less accurate) answer and update our records afterwards.

    #Creating range of last 60 to calculate top nommer

    #Getting current row, then the row 60 above and setting column two (the names column) as the column for each
    row_int=int(row)
    row_minus_60=int(row)-60
    past_60=gspread.utils.rowcol_to_a1(row_minus_60, 2)
    current_row=gspread.utils.rowcol_to_a1(row_int, 2)

    # Getting the range of names between 60 ago and now
    past_names=past_60+":"+current_row

    # Returns a list of al the names in that range
    last_60_names=orders1.range(past_names)
    print (app_code,location_code,sublocation,"last 60 names are: ",last_60_names)

    #This is just creating a list that we can populate with relevant items (the program needs a list to add things to, even if it's an empty one)
    order_history=[]
    for record in last_60_names:
        # Value gets the contents of the cell
        record_value=record.value
        print (app_code,location_code,sublocation,"record_value :", record_value)
        if record_value is record_value:
            # (If it is an actual value and not blank add it to the list)
            order_history.append(record.value)
            cleaned_history = [elem for elem in order_history if elem.strip()]

    # Getting most occurring name (thanks to https://stackoverflow.com/questions/1518522/python-most-common-element-in-a-list)
    data=Counter(cleaned_history)
    print (app_code,location_code,sublocation,"name occurences is: ", data)

    # Selecting the most occurring item in based on our count
    new_top_nommer=data.most_common(1)[0][0]
    print (app_code,location_code,sublocation,"new top nommer is", new_top_nommer)

    if exists=="yes":
        # If it exists, update it
        print (app_code,location_code,sublocation,"top nommer already recorded")
        update_top_nommer(app_code,location_code,team_id, new_top_nommer)
    else:
        # If it doesn't exist, create it
        print (app_code,location_code,sublocation,"top nommer not already recorded")
        top_nommer_creator(app_code,location_code,team_id, new_top_nommer)

#----------#


#------------------#

#--- End of w-D calculating_top_nommer ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#w-E next_available_row

# quick process for finding the first empty row in the spreadsheets
# Thanks to https://stackoverflow.com/questions/40781295/how-to-find-the-first-empty-row-of-a-google-spread-sheet-using-python-gspread and https://stackoverflow.com/questions/3845423/remove-empty-strings-from-a-list-of-strings
# with some modifications to account for missed cells and avoid accidental overwriting

def next_available_row(app_code,location_code,worksheet):
    sublocation= "E (next_available_row) - "
    print (app_code,location_code,sublocation," starting next_available_row process")

    # Listing all the values in the first column of the worksheet, but dropping any that have a value of "None"
    # This seems to be one of the few GSpread functions where empty cells return "None" in other functions they return
    # "" which is why you'll see I've dealth with empty cells differently further down
    str_list = list(filter(None, worksheet.col_values(1)))  # fastest

    # Getting the length of the list of full cells+1 (suggesting the first cell after that should be empty)
    str_list_length=len(str_list)+1

    # Getting the legnth of the whole column, not dropping "None" values
    full_column=worksheet.col_values(1)  # fastest
    print (app_code,location_code,sublocation,"got full column values")


    print (app_code,location_code,sublocation," number of full cells:", str_list_length)

    # Selecting the first clear cell based on the length of the full list
    first_clear_cell="A"+str(str_list_length)

    # Getting the value to check if it is clear
    supposedly_clear_cell=worksheet.acell(first_clear_cell)
    supposedly_clear_cell_value=supposedly_clear_cell.value

    # Setting tries=1 so we can automatically cut off this process if it gets caught in a loop
    tries=1

    # Setting the list we're checking as the list we were given to start with, the reason we
    # copy this is so that we don't overwrite the original
    working_list_length=str_list_length
    while supposedly_clear_cell_value!="":
        # While the value of the cell we think is clear ISN'T just ""

        # Tell us the cell isn't empty
        print (app_code,location_code,sublocation,"isn't empty cell")

        # Get the portion of the full column which is as long as all the cells we've been TOLD we should skip
        sublist_of_full_column=full_column[:working_list_length]
        print (app_code,location_code,sublocation,"sublist we're checking is: ", len(sublist_of_full_column))
        # This prints out ALL the values for debugging, I've commented it out because it's messy
        #print (app_code,location_code,sublocation,sublist_of_full_column)

        # Getting our sublist and performing the same filtering process - removing "None" values
        # this shouldn't have any impact if the cells are all actually full
        sublist_without_none=list(filter(None, sublist_of_full_column))
        print (app_code,location_code,sublocation,"sublist without none values is: ", len(sublist_without_none))

        # Finding out how many empty cells there are in our supposedly full list by subtracting the list without
        # empty cells, from the list with empty cells
        difference_between_lists=len(sublist_of_full_column)-len(sublist_without_none)
        print (app_code,location_code,sublocation,"difference_between_lists is; ", difference_between_lists)

        # Adding the number of empty cells, to our original list, to give a potential new full list
        working_list_length=str_list_length+difference_between_lists
        print (app_code,location_code,sublocation,"new list length is", working_list_length)

        # Setting a new first_clear_cell and getting its contents to check whether it's actually empty
        first_clear_cell="A"+str(working_list_length)
        supposedly_clear_cell=worksheet.acell(first_clear_cell)
        supposedly_clear_cell_value=supposedly_clear_cell.value
        print (app_code,location_code,sublocation,"supposedly_clear_cell_value is: ", supposedly_clear_cell_value)

        # Adding one try onto our current count (after the first time we attempt this sectioin it'll be two, if
        # this fails we'll do this again and add another one onto our number of tries)
        tries=tries+1
        if supposedly_clear_cell_value=="":
            # If the cell we land on is infact empty
            print (app_code,location_code,sublocation,"cell is clear")
            print (app_code,location_code,sublocation,"checking rows: ", working_list_length, "to", working_list_length+20)
            # Perform the same check on the next 20 cells to make sure we haven't landed in a cell that happens to be
            # empty half way down the list
            checking_next_20_are_clear=list(filter(None, full_column[working_list_length:(working_list_length+20)]))
            if len(checking_next_20_are_clear)==0:
                # If by filtering out all the "None" values we end up with a list of nothing, we're clear
                print (app_code,location_code,sublocation,checking_next_10_are_clear)
                print (app_code,location_code,sublocation,"remaining cells are clear")
                # End these repeated tries
                break

        if tries==50:
            # If we keep trying to find an empty cell and after 50 attempts can't, give up
            print (app_code,location_code,sublocation,"reached retry limit")
            break

    # As the result, return the actual list length we have calculated
    return str(working_list_length)

#--- w-E next_available_row---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- w-F open_db_connection ---#
# Thanks to: https://devcenter.heroku.com/articles/heroku-postgresql#connecting-in-python

def open_db_connection(app_code,location_code):
    sublocation= "F (open_db_connection) - "

    print (app_code,location_code,sublocation," starting setting up database connection")
    #Thanks to https://stackoverflow.com/questions/45133831/heroku-cant-launch-python-flask-app-attributeerror-function-object-has-no {
    urllib.parse.uses_netloc.append("postgres")
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    #}
    print (app_code,location_code,sublocation,"W11 open_db_connection - ", url)

    # This is because we will be referencing this in a few functions so it's important to be
    # able to access it and not worry about causing errors by forgetting to include it from
    # one function to the next
    global conn

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

    print (app_code,location_code,sublocation," finishing setting up database connection")


    # See reasoning for including conn as global variable above
    global cur
    cur = conn.cursor()


#--- End of w-F open_db_connection ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#

#--- W-G close_db_connection ---#

def close_db_connection(app_code,location_code):
        sublocation= "G (close_db_connection) - "

        print (app_code,location_code,sublocation," starting connection shut down")


        cur.close()
        print (app_code,location_code,sublocation," closed cursor")
        conn.close()
        print (app_code,location_code,sublocation," closed connection")

        print (app_code,location_code,sublocation," finished connection shut down")

#--- End of W12 closing psycopg2 connection ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- w-H check_database ---#

def check_database(app_code,location_code,user_id, column):
    # This takes a unique user_id and checks the column we tell it to check, then it
    # returns the value in that column.

    sublocation= "H (check_database) - "
    print (app_code,location_code,sublocation," starting check_database process")
    print (app_code,location_code,sublocation,"user_id is: ", user_id)

    # cur is our cursor, it is what we use to select and change parts of our database
    # here we're selecting the value of column from our database users_and_actions where the user_id matches user_id
    # the bit in orange references the bit immediately after it in green. The bit in green is a label for the bit after
    # that in white
    cur.execute("SELECT "+column+" FROM users_and_actions WHERE user_id = %(current_uid)s",{"current_uid": user_id})

    # Get the first value that matches the SELECT we just ran
    value=cur.fetchone()


    # It returns these values as a list so we have to run a for loop, essentially saying check every item in this "list"
    # then for every single item, call it "item_to_use", because there's only one, we end up with our item
    # we could also have said "just give us the first element"
    for item in value:
        #Unpacking items (thanks to https://stackoverflow.com/questions/34178172/psycopg2-selecting-timestamp-returns-datetime-datetime-wrapped-in-tuple-how-to)\
        item_to_use=item

    # Confirming the item we retrieved
    print (app_code,location_code,sublocation,column+" is: ", item_to_use)

    # Confirming the end of the process
    print (app_code,location_code,sublocation," ending check_database process")

    # Passing the relevant item back to the main process for it to use
    return item_to_use

#--- End of w-H check_database ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- w-I top_nommer_check ---#


# This process takes a team_id and returns the top_nommer record (the person who ordered most in the last 60) for the
# main process to use

def top_nommer_check(app_code,location_code,team_id):
        sublocation= "I (top_nommer_check) - "
        # This isn't the start of a long-winded speech, we're just listing by letter

        #------------------------------------------------------#
        #//////////////////////////////////////////////////////#
        #============  Database connection open  ==============#
        #//////////////////////////////////////////////////////#
        #------------------------------------------------------#

        # This function takes our team_id and finds the top_nommer for that team
        # We aways set the top_nommer ID as the same so the unique value becomes the team
        # ID, that allows us to retrieve the name saved there.

        print (app_code,location_code,sublocation," starting top_nommer_check process")

        # Finding the user name we saved in our database (users_and_actions) where the user_id matches the string
        # "top_nommer_id" and the team_id matches the team_id we have for this team (which should only intersect at one
        # point if the top_nommer has been saved and not intersect at all if we haven't saved this value yet)
        cur.execute("SELECT user_name FROM users_and_actions WHERE user_id = %s AND team_id = %s", ("top_nommer_id", team_id));
        print (app_code,location_code,sublocation,"w13 top_nommer_check - top_nommer is: ", cur.fetchone())

        value=cur.fetchone()

        # If we don't have a value for it, we return None so our main process knows that and can respond appropriately
        if value==None:
            return

        # Even for one result it returns a list so we just do this to pull that result out
        for item in value:
            #Unpacking items (thanks to https://stackoverflow.com/questions/34178172/psycopg2-selecting-timestamp-returns-datetime-datetime-wrapped-in-tuple-how-to)\
            item_to_use=item

        # Confirming the value
        print (app_code,location_code,sublocation," top_nommer_name is: ", item_to_use)

        # Confirming ending the process and passing the value back to the main process for it to use
        print (app_code,location_code,sublocation," ending check_database process")
        return item_to_use


#--- End of w-I top_nommer_check ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- w-J update_top_nommer ---#

# A process for when the top_nommer exists, finding that value and updating it with the
# most recent value


def update_top_nommer(app_code,location_code,team_id, top_nommer):
    sublocation= "J (update_top_nommer) - "
    #------------------------------------------------------#
    #//////////////////////////////////////////////////////#
    #============  Database connection open  ==============#
    #//////////////////////////////////////////////////////#
    #------------------------------------------------------#



    # Here we're selecting based on team_id because there will only be one top orderer
    # per team so we set the user_id as "top_nommer_id" for each, differentiate by
    # team and then just change the user name

    # we start off by printing the value as it exists, this is helpful in debugging
    # to make sure the value is there and also to make sure we're changing it
    print (app_code,location_code,sublocation," retrieving current top_nommer")
    cur.execute("SELECT user_name FROM users_and_actions WHERE user_id = %s AND team_id = %s", ("top_nommer_id", team_id));
    print (app_code,location_code,sublocation," top_nommer before update: ", cur.fetchone())

    # then we select the same record but instead change the user_name to the new one we've calculated
    # we have to use this format to add and retrieve data with databases through psycopg for security reasons
    # the first %s corresponds to the first item in the following brackets, the second, is filled in by the second,
    # and so on.
    print (app_code,location_code,sublocation," updating top_nommer")
    cur.execute("UPDATE users_and_actions SET user_name=%s WHERE user_id=%s AND team_id=%s", (top_nommer, "top_nommer_id",  team_id));

    # getting the number of updated rows - this also confirms we've made a change
    updated_rows = cur.rowcount
    print (app_code,location_code,sublocation," number of rows updated = ", updated_rows)
    conn.commit()
    print (app_code,location_code,sublocation," committed data")

    # Confirming the change we've made
    print (app_code,location_code,sublocation," executed change, updated user_name to be: ", top_nommer ," where user_id is 'top_nommer_id' and team_id is ", team_id)
    cur.execute("SELECT user_name FROM users_and_actions WHERE user_id = %s AND team_id = %s", ("top_nommer_id", team_id));
    print (app_code,location_code,sublocation,"w13 update_top_nommer - value after most recent change: ", cur.fetchone())

    return

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- W14 top_nommer_creator  ---#

# A process where the top_nommer doesn't exist for that team and so we need to create one
# this is similar to the last process except we're using INSERT INTO instead and we have to
# put all the values in

def top_nommer_creator(app_code,location_code,team_id, top_nommer):
    sublocation= "K (top_nommer_creator) - "

    print (app_code,location_code,sublocation," creating user process")

    # Using INSERT INTO to add values to columns, the first brackets define the columns
    # we're adding to, the second brackets give the values we're adding (but the values
    # we're adding are put into that second brackets from the third brackets). May seem
    # roundabout but it's more secure. http://initd.org/psycopg/docs/sql.html
    cur.execute("INSERT INTO users_and_actions (user_id, user_name, team_id) VALUES (%s, %s, %s);", ('top_nommer_id', top_nommer, team_id,));

    # Confirming what we think we've done
    print (app_code,location_code,sublocation," added top_nommer_id, ", top_nommer,"team_id:", team_id, " to users_and_actions")

    # Saving the data to the table
    conn.commit()
    print (app_code,location_code,sublocation," committed data")

    # Retrieving the same record to check whether we have done what we think
    # A process for retrieving records (thanks to https://stackoverflow.com/questions/1466741/parameterized-queries-with-psycopg2-python-db-api-and-postgresql)

    # At first only recalling the new username so we can check at a glance
    print (app_code,location_code,sublocation," recalling new user_name only")
    cur.execute("SELECT user_name FROM users_and_actions WHERE user_id = %s AND team_id = %s", ("top_nommer_id", team_id));
    print (app_code,location_code,sublocation," fetching new user name: ", cur.fetchone())

    # And then recalling the whole record in case the glance isn't enough, we could cut
    # this out if we wanted to speed up the program
    print (app_code,location_code,sublocation,"w14 top_nommer_creator - recalling whole record")
    cur.execute("SELECT * FROM users_and_actions WHERE user_id = %s AND team_id = %s", ("top_nommer_id", team_id));
    print (app_code,location_code,sublocation,"w14 top_nommer_creator - fetching one result: ", cur.fetchone())
    print (app_code,location_code,sublocation,"w14 top_nommer_creator - end of function")

    return

#--- End of Web creating user ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Web retrieving user name from database ---#

# Process for checking whether user exists

def check_for_user(app_code,location_code,user_id):
    sublocation= "L (check_for_user) - "

    print (app_code,location_code,sublocation," starting check_for_user process")


    # Finding user based on the current user id we're working with. Here you can see
    # we can also add values to our psycopg2 queries by naming them, %(current_uid)s
    # is being filled out by the value of "current_uid" in the curly brackets
    cur.execute("SELECT user_name FROM users_and_actions WHERE user_id = %(current_uid)s",
               {"current_uid": user_id})
    print (app_code,location_code,sublocation," user_name is: ", cur.fetchone())
    value=cur.fetchone()

    # Fetching values gives a list so we have to run through it to get the data
    for item in value:
        #Unpacking items (thanks to https://stackoverflow.com/questions/34178172/psycopg2-selecting-timestamp-returns-datetime-datetime-wrapped-in-tuple-how-to)\
        print (app_code,location_code,sublocation,item)
        user_name=item

    print (app_code,location_code,sublocation," user_name is: ", user_name)

    print (app_code,location_code,sublocation,"web check_for_user - ending check_for_user process")


    # By returning the user_name we can do further checks. For instance, if there ISN'T a user name
    # we can check whether it exists outside this process by checking if the returned value is None
    return user_name


#--- End of Web retrieving user name from database ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- Web updating columns  ---#

# A generalised process for updating columns  based on lists of pairs
# you can see how these pairs have to be formatted where we have called this function
# importantly you will see a warning below that I have cut corners in terms of building
# this query. It is OK here but what users can change should be CLOSELY monitored if you
# are adapting this


def update_columns(app_code,location_code,list_of_pairs, user_id):
    sublocation= "M (update_columns) - "
    print (app_code,location_code,sublocation," starting update_columns process, finding by unique user_id")
    print (app_code,location_code,sublocation,"defining value is: ", user_id)


    # Process for updating records in the database (thanks to https://stackoverflow.com/questions/7458749/psycopg2-insert-update-writing-problem)
    print (app_code,location_code,sublocation," retrieving values before change")
    # A process for retrieving records (thanks to https://stackoverflow.com/questions/1466741/parameterized-queries-with-psycopg2-python-db-api-and-postgresql)
    # Bear in mind with this that even if you are only putting in one value (see user_id below)
    # we STILL have to finish with a comma for this process to understand
    cur.execute("SELECT * FROM users_and_actions WHERE user_id = %s", (user_id,));
    print (app_code,location_code,sublocation," values as they are: ", cur.fetchone())

    #Creating a loop to go through all of the column value pairs that have been passed
    # As an FYI, the name of the table cannot be passed as a parameter, that has to be hard coded (https://stackoverflow.com/questions/13793399/passing-table-name-as-a-parameter-in-psycopg2)
    print (app_code,location_code,sublocation,"splitting list_of_pairs into update_pairs")
    #Process for splitting one list into list of lists (thanks to https://stackoverflow.com/questions/9671224/split-a-python-list-into-other-sublists-i-e-smaller-lists)
    update_pairs = [list_of_pairs[x:x+2] for x in range(0, len(list_of_pairs), 2)]
    print (app_code,location_code,sublocation,"list split into update_pairs")
    for pair in update_pairs:
        print (app_code,location_code,sublocation,"web update_columns - for column loop start")
        print (app_code,location_code,sublocation,"web update_columns - splitting the column, value pair to acess column and value separately")
        print (app_code,location_code,sublocation,"first pair is: ", pair)
        #Selecting the first item of the pair (which should always be the column)
        column=pair[0]
        print (app_code,location_code,sublocation," column to update is ", column)
        #Selecting the second item (which should always be the value)
        values_to_add= pair[1]
        print (app_code,location_code,sublocation," value to add to ", column, " is ", values_to_add)

        # In this part of the for loop - adding the value (thanks to http://initd.org/psycopg/docs/sql.html)
        # IMPORTANT, the only reason we can use string concatenation here (injecting the column value with a plus) is that
        # we are defining the column, user input cannot define what value that is, if users could define the column name
        # this would be at risk of sql injection

        cur.execute("UPDATE users_and_actions SET "+column+"=%s WHERE user_id=%s", (values_to_add, user_id));

        # getting the number of updated rows
        updated_rows = cur.rowcount
        print (app_code,location_code,sublocation,"number of rows updated = ", updated_rows)
        conn.commit()
        print (app_code,location_code,sublocation," committed data")
        print (app_code,location_code,sublocation," executed change, updated users_and_actions column: ", column, "to be ", values_to_add ," where user_id is ", user_id)
        cur.execute("SELECT "+ column +" FROM users_and_actions WHERE user_id= %s", (user_id,));
        print (app_code,location_code,sublocation," value after most recent change: ", cur.fetchone())


    print (app_code,location_code,sublocation," retrieving values after change")
    cur.execute("SELECT * FROM users_and_actions WHERE user_id= %s", (user_id,));
    print (app_code,location_code,sublocation," values as they are post change: ", cur.fetchone())
    print (app_code,location_code,sublocation, " end of function")


#--- End of Web updating columns  ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- W-N sending contexts  ---#

# This is a process for setting a new context in API.Ai, this allows us to send information
# and retrieve it at a later date, and also to interpret users' incoming messages differently
# based on the context we set, the data has to be defined before this is called

def send_contexts(app_code,location_code,user_id,data):
    sublocation= "N (send_contexts) - "

    # API.AI requires proper authorization headers or it won't accept the input
    # You need to have created the api_bearer environment variable (see section at the top)

    # Printing what we're sending for debugging
    print (app_code,location_code,sublocation," data is: ",data)


    headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+api_bearer,
    }

    print (app_code,location_code,sublocation," headers are: ", headers)

    # We set the sessionId so API.AI knows which user this is being applied to
    params = (
    ('sessionId', user_id),
    )

    print (app_code,location_code,sublocation," sessionId set as: ", user_id)



    # Sending contexts message to api.ai, this adds contextual information for
    # future interaction, in this case, it allows us to trigger either the name-confirmation
    # or name-incorrect intents AND allows us to retrieve the value of name from future messages
    # from API.AI
    # Format thanks to https://api.ai/docs/reference/agent/contexts and https://curl.trillworks.com/

    print (app_code,location_code,sublocation,"sending message to API.AI")


    response=requests.post('https://api.api.ai/v1/contexts', headers=headers, params=params, data=data)

    return response


#--- End of W-N sending contexts  ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- W-O deleting contexts  ---#

# This is a process for deleting contexts that are currently set in this session
# by using this we can make sure that users can start with a fresh page even if they
# haven't waited the 30 minutes or so it takes for the session to expire

def delete_contexts(app_code,location_code,user_id):

    sublocation= "O (delete_contexts) - "

    #Posting to API.AI service to clear contexts
    # You need to have created the api_bearer environment variable (see section at the top)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+api_bearer,
        }
    params = (
        ('sessionId', user_id),
        )

    print (app_code,location_code,sublocation,"sending message to API.AI")

    response=requests.delete('https://api.api.ai/v1/contexts', headers=headers, params=params)

    return response

#--- End of W-O deleting contexts  ---#
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#===========================================================================================================================#
#---------------------------------------------------------------------------------------------------------------------------#
#===========================================================================================================================#

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#
#--- W-P sending query  ---#

# Process for sending the query to API.AI, data must be defined before this is called
# Thanks to https://api.ai/docs/reference/agent/query
# You need to have created the api_bearer environment variable (see section at the top)

def send_query(app_code,location_code,data):

    sublocation= "P (send_query) - "

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer '+api_bearer,
    }

    print (app_code,location_code,sublocation,"data is: ", data)

    print (app_code,location_code,sublocation,"web - sending message to API.AI")

    response=requests.post('https://api.api.ai/v1/query?v=20150910', headers=headers, data=data)

    return response
