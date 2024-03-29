from tweepy import OAuthHandler
from tweepy import API, error
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import sys
import os
import time
import json
from datetime import datetime
import pandas as pd
import random
#import config
import streamlit as st
from streamlit_tags import st_tags
#import streamlit_analytics
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from df2gspread import df2gspread as d2g
from googleapiclient import discovery

#st.markdown(f"""<head><!-- Global site tag (gtag.js) - Google Analytics -->
#<script async src="https://www.googletagmanager.com/gtag/js?id={st.secrets['TRACKING_ID']}"></script>
#<script>
  #window.dataLayer = window.dataLayer || [];
  #function gtag(){{dataLayer.push(arguments);}}
  #gtag('js', new Date());
  #gtag('config', '{st.secrets['TRACKING_ID']}');
#</script></head>""", unsafe_allow_html=True)
#import streamlit.components.v1 as components
#from config.py import CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN_KEY, ACCESS_TOKEN_SCRET

#streamlit_analytics.start_tracking()
#streamlit_analytics.track(save_to_json="/Users/simonpastor/Documents/Github/twittlist/file.json")

#APP_NAME = "TwittList"
#icon = [":fr:",":champagne:",":crown:","old_key",":computer:",":desktop_computer:",":robot_face:"]
st.set_page_config(page_title="TwittList", layout="centered")
primaryColor = '#1DA1F2'

st.markdown("<h1 style='text-align: center; color: #1DA1F2;'>TwittList</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: black;'>TwittList allows you to find the most relevant Twitter Accounts on a given topic</h2>", unsafe_allow_html=True)

#st.markdown("<h3> First input the username of the Twitter accounts similar to the ones you are looking for <em>(Example: If you are looking for climate activists enter GretaThunberg)</em>", unsafe_allow_html=True)
#st.markdown("<h3> Then enter the topics or keywords you want to focus on <em>(Example: climate)</em></h3>", unsafe_allow_html=True)
#st.write("As you can see here, we're looking for accounts similar to that of Greta Thunberg and the WWF. We're focusing on the climate and sustainability")

def set_api():
    random_number = random.randrange(1, 8)
    consumer_key=st.secrets[f"CONSUMER_KEY{random_number}"]
    consumer_secret=st.secrets[f"CONSUMER_SECRET{random_number}"]
    access_token_key=st.secrets[f"ACCESS_TOKEN_KEY{random_number}"]
    access_token_secret=st.secrets[f"ACCESS_TOKEN_SECRET{random_number}"]
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token_key, access_token_secret)
    api = API(auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True)
    return api

def most_common(lst):
        return max(set(lst), key=lst.count)

api = set_api()

random_topic = random.randrange(0, 8)
suggested_texts = []

search_values = [['GretaThunberg', 'Greenpeace'], ['ycombinator','a16z'], ['nytimes','CNN','BBCWorld'], ['POTUS','EmmanuelMacron','narendramodi'],['NASA','SpaceX','esa'],['KingJames','KDTrey5','JHarden13'], ['Cristiano','neymarjr','KMbappe'],['rihanna','Drake','taylorswift13']]
search_texts = [['Climate', 'COP26','Environment'], ['vc', 'startup','tech'], ['news'],['leaders','presidents'],['space','astronomy','mars'], ['nba','sports','bastketball'],['soccer', 'football','sports'],['music','hip hop','culture']]

search = st_tags(
    label='## Enter the Username of Twitter Accounts similar to the ones you are looking for:',
    text='Press enter to add more',
    value=search_values[random_topic],
    suggestions=['BarackObama', 'EmmanuelMacron', "narendramodi","elonmusk","billgates","nytimes","POTUS","richardbranson","NASA","JoeBiden","AOC","Forbes","guardian","AP","latimes","TIME","NewYorker","politico","WSJ","nytimes","CNN","EmmaWatson","Disney","Harvard","FBI","Princeton","nybooks","Twitter"],
    maxtags = 4,
    key='1')

text = st_tags(
    label='## Enter Topics or Keywords you want to focus on:',
    text='Press enter to add more',
    value= search_texts[random_topic],
    suggestions=['finance', 'civic', 'gov', 'tech', 'crypto', 'politics', 'democracy', 'vegan', 'philosophy',"cars","coffee","photography","aliens","money","comedy","fruits","vegetables","Europe","dogs","animals","artists","nature","boats","travel","tourism","football","soccer","newspapers","adventure","ngos","sports","currency","coin","military","beer","wine","cocktails","royalty","geography","history","singer","biotech","Africa","Asia","Oceania","Middle East","Maghreb","cooking","literature","poetry","fiction","dance","film","music","opera","theatre","architecture","drawing","painting","sculpture","culture","health","exercise","nutrition","fitness","antiquity","middle age","renaissance","mathematics","algebra","calculus","geometry","logic","statistics","biology","biochemistry","botany","ecology","zoology","astronomy","sciences","chemistry","earth sciences","physics","psychology","relationships","love","humanism","theology","religion","economics","linguistics","languages","american","indian","australian", "spanish","italian","french","german","swiss","swedish","austrian","canadian","pakistani","chinese","japanese","brazilian","political science","law","legal","sociology","anthropology","criminal justice","justice","crime","education","public affairs","business","vc","venture capital","finance","marketing","social media","management","influencer","artificial intelligence","machine learning","deep learning","data science","agriculture","aerospace","biotechnology","communication","neuroscience","quantum mechanics","energy","oil","industry","retail","library","books","machines","fashion","manufacturing","army","navy","permaculture","robotics","nuclear","sustainable development","space exploration","space","telecommunication","internet of things","iot","transport","vehicles","autonomous vehicles"],
    maxtags = 9,
    key='2')

iterations = st.number_input(label='Number of Iterations (Default=2) The more iterations, the more accurate the results, yet the longer the computation time!',min_value=1,max_value=4,value=2,step=1)

agree = st.checkbox('Display images and last tweets of top 10 results')

submit_button = st.button('Submit', key="search_submit")

#streamlit_analytics.stop_tracking(unsafe_password=st.secrets["ANALYTICS_KEY"])

civic_lists = []
civic_lists_history = []
civic_name = []
civic_dates = []
civic_followers = []
civic_members = []
all_members = []

new_civic_lists = []
dict_with_people_list = []

cool_people = {}
cool_followers = {}

def initial_function(dict_with_people):
    #Use this function at the very beginning and after each successful final_members() function
    for peoples in dict_with_people.keys():
        dict_with_people_list.append(peoples)
    return dict_with_people_list

def members_to_lists(dict_with_people,looking_for,count_number):
    for people in dict_with_people_list:
        try :
            for i in api.lists_memberships(people, count=count_number):
                if i.id not in civic_lists and i.id not in civic_lists_history:
                    for j in looking_for:
                        if j in i.name.lower():
                            civic_lists.append(i.id)
                            civic_lists_history.append(i.id)
                            civic_name.append(i.name)
                            civic_dates.append(i.created_at)
                            civic_followers.append(i.subscriber_count)
                            civic_members.append(i.member_count)
                            if len(dict_with_people_list) % 10 == 0:
                                print(len(dict_with_people_list))
        except error.TweepError:
            pass
        dict_with_people_list.remove(people)
    return civic_lists


def list_to_members(dict_with_people,looking_for,count_number):
    for i in members_to_lists(dict_with_people,looking_for,count_number):
        try :
            all_members.append(api.list_members(list_id=i))
        except error.TweepError:
            pass
        civic_lists.remove(i)
    return all_members

def final_members(dict_with_people,looking_for,count_number):
    for members in list_to_members(dict_with_people,looking_for,count_number):
        for i in members:
            if i.screen_name in cool_people.keys():
                cool_people[i.screen_name] += 1
            else:
                cool_people[i.screen_name] = 1
    return cool_people

def top5(dict_with_people,looking_for,count_number):
    ranking = []
    number = []
    for i,j in final_members(dict_with_people,looking_for,count_number).items():
        if len(ranking) < 300:
            ranking.append(i)
            number.append(j)
        else:
            if j > min(number):
                ranking.pop(number.index(min(number)))
                number.pop(number.index(min(number)))
                ranking.append(i)
                number.append(j)
            else:
                continue

    x = list(zip(ranking,number))
    return x

def run(iterations):
    set_iterations = iterations
    initial_function(cool_people)
    if iterations == 2:
        count_number = 15
    elif iterations == 1:
        count_number = 20
    elif iterations == 3:
        count_number = 10
    elif iterations == 4:
        count_number = 8
    top5(cool_people,looking_for_list,count_number)
    st.write(f"Iteration #{abs(iterations-set_iterations-1)} successful")
    while iterations > 1:
        iterations = iterations - 1
        count_number = max(count_number - 4, 2)
        initial_function(cool_people)
        top5(cool_people,looking_for_list,count_number)
        st.write(f"Iteration #{abs(iterations-set_iterations-1)} successful")
    final_results = end(cool_people)
    return final_results

def end(results):
    results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    values = []
    accounts = []
    links = []
    followers = []
    following = []
    protected = []
    verified = []
    location = []
    for i in results:
        y = api.get_user(i[0])
        link = f"https://twitter.com/{i[0]}"
        links.append(link)
        accounts.append(i[0])
        values.append(i[1])
        followers.append(y.followers_count)
        following.append(y.friends_count)
        protected.append(y.protected)
        verified.append(y.verified)
        location.append(y.location)
    final_results = pd.DataFrame.from_dict({"Accounts":accounts,"Verified":verified,"Followers":followers,"Following":following,"Location":location,"Links":links,"Counts":values, "Protected":protected})
    return final_results


def google_sheets():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

    x = {"type": st.secrets['type'],
    "project_id": st.secrets['project_id'],
    "private_key_id": st.secrets['private_key_id'],
    "private_key": st.secrets['private_key'],
    "client_email": st.secrets['client_email'],
    "client_id": st.secrets['client_id'],
    "auth_uri": st.secrets['auth_uri'],
    "token_uri": st.secrets['token_uri'],
    "auth_provider_x509_cert_url": st.secrets['auth_provider_x509_cert_url'],
    "client_x509_cert_url": st.secrets['client_x509_cert_url']}

    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_dict(x, scope)

    # authorize the clientsheet
    client = gspread.authorize(creds)

    spreadsheet_key = st.secrets["spreadsheet_key"]
    sheet = client.open_by_key(spreadsheet_key)

    wks_name = "Sheet1"
    next_free_line = len(sheet.values_get('A1:J1000')["values"]) + 1
    cell_of_start_df = f"A{next_free_line}"

    return spreadsheet_key, wks_name, creds, cell_of_start_df

def update_google_sheets(final,spreadsheet_key,wks_name, creds, cell_of_start_df):
    d2g.upload(final,
        spreadsheet_key,
        wks_name,
        credentials=creds,
        col_names=False,
        row_names=False,
        start_cell = cell_of_start_df,
        clean=False)

if submit_button:
    for i in search_values[random_topic]:
        for j in api.lists_memberships(screen_name=i, count=10):
            list_id2 = j.full_name.split("/")[1]
            #list_name = api.get_list(list_id = list_id2).name
            #suggested_texts.append(list_name)

    #if suggested_texts[0] not in search_texts[random_topic]:
        #st.write(f"Here's another keyword you could try:, {suggested_texts[0]}")
    #suggestions = most_common(suggested_texts)
    #st.write("Better Topics: ", suggested_texts[0])

    looking_for_list = []

    for i in text:
        looking_for_list.append(i.lower())

    for j in search:
        cool_people[j] = 1

    spreadsheet_key, wks_name, creds, cell_of_start_df = google_sheets()
    final = pd.DataFrame({"Date & Time":datetime.now().strftime("%d/%m/%Y %H:%M:%S"),f"Twitter Accounts":' '.join(search), "Key terms":' '.join(text), "Results":""}, index=[0])
    update_google_sheets(final,spreadsheet_key,wks_name, creds, cell_of_start_df)

    final_results = run(iterations)
    st.write(f"{len(final_results)} results found")

    if agree:

        if len(final_results) >= 10:
            st.title("Top 10 Results")
            for k in range(0,10):
                x = api.get_user(final_results["Accounts"][k])
                st.title(x.name)
                if len(x.profile_image_url) > 3:
                    st.image(x.profile_image_url, width=120)
                st.write(x.screen_name)
                if len(x.description) > 3:
                    st.write(x.description)
                st.write(f"Last Tweet: {x.status.text}")
                st.write(f"Followers Count: {x.followers_count}")
                st.write(f"Following: {x.friends_count}")
        else:
            st.title(f"Top {len(final_results)} Results")
            for k in range(0,len(final_results)):
                x = api.get_user(final_results["Accounts"][k])
                st.title(x.name)
                if len(x.profile_image_url) > 3:
                    st.image(x.profile_image_url, width=120)
                st.write(x.screen_name)
                if len(x.description) > 3:
                    st.write(x.description)
                st.write(f"Last Tweet: {x.status.text}")
                st.write(f"Followers Count: {x.followers_count}")
                st.write(f"Following: {x.friends_count}")

        #st.markdown(f"""<h3 style='text-align: center'><img src={x.profile_image_url}></img>{x.name}<br>{x.screen_name}<br>{x.description}<br>Followers Count: {x.followers_count}<br>Subscribers: {x.friends_count}</h3>""",unsafe_allow_html=True)

    #def make_clickable(link):
        # target _blank to open new window
        # extract clickable text to display for your link
        #text = link.split('=')[1]
        #return f'<a target="_blank" href="{link}">{text}</a>'

    st.title("All Results")
    # link is the column with hyperlinks
    #final_results['Links'] = final_results['Links'].apply(make_clickable)
    #final_results = final_results.to_html(escape=False)
    #st.write(final_results, unsafe_allow_html=True)

    st.write(final_results)

    final = pd.DataFrame({"Date & Time":datetime.now().strftime("%d/%m/%Y %H:%M:%S"),f"Twitter Accounts":' '.join(search), "Key terms":' '.join(text), "Results":' '.join(list(final_results["Accounts"]))}, index=[0])
    update_google_sheets(final,spreadsheet_key,wks_name, creds, cell_of_start_df)

    # #st.download_button(label="Download data as CSV",data=final_results,file_name=f'{looking_for_list[0]}_results.csv')
