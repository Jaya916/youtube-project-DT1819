from googleapiclient.discovery import build
from pymongo.mongo_client import MongoClient
import pymongo
import psycopg2
import pandas as pd
import streamlit as st

def Api_connect():
    Api_id="AIzaSyAo3Sv2AUAoUOrSIImrT7K5s--PvZtg6SM"
    
    api_service_name="youtube"
    api_version="v3"

    youtube=build(api_service_name,api_version,developerKey=Api_id)

    return youtube
youtube=Api_connect()

def get_channel_info(channel_id):
  request=youtube.channels().list(
          part="snippet,contentDetails,statistics",
          id=channel_id
  )
  response=request.execute()

  for i in response["items"]:
    data=dict(Channel_Name=i["snippet"]["title"],
              Channel_Id=i["id"],
              Subscribers=i["statistics"]["subscriberCount"],
              Views=i["statistics"]["viewCount"],
              Total_Videos=i["statistics"]["videoCount"],
              Channel_Description=i["snippet"]["description"],
              Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data
  
def get_playlist_details(channel_id):
    next_page_token=None
    All_data=[]
    while True:
        request=youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response=request.execute()
        for item in response["items"]:
            data=dict(Playlist_Id=item["id"],
                    Title=item["snippet"]["title"],
                    Channel_Id=item["snippet"]["channelId"],
                    Channel_Name=item["snippet"]["channelTitle"],
                    PublishedAt=item["snippet"]["publishedAt"],
                    Video_Count=item["contentDetails"]["itemCount"])
        All_data.append(data)

        next_page_token=response.get("nextPageToken")
        if next_page_token is None:
            break
    return All_data
  

def get_video_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id,
                    part="contentDetails").execute()
    Playlist_Id=response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    next_page_token=None

    while True:
        response1=youtube.playlistItems().list(
                                            part="snippet",
                                            playlistId=Playlist_Id,
                                            maxResults=50,
                                            pageToken=next_page_token).execute()
        for i in range(len(response1["items"])):
            video_ids.append(response1["items"][i]["snippet"]['resourceId']['videoId'])
        next_page_token=response1.get("nextPageToken")

        if next_page_token is None:
            break
    return video_ids
  
def get_video_info(video_ids):
    video_data=[]
    for video_id in video_ids:
        request=youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response=request.execute()

        for item in response["items"]:
            data=dict(Channel_Name=item["snippet"]["channelTitle"],
                Channel_Id=item["snippet"]["channelId"],
                Video_Id=item["id"],
                Title=item["snippet"]["title"],
                Tags=item["snippet"].get("tags"),
                Thumbnail=item["snippet"]["thumbnails"]["default"]["url"],
                Description=item["snippet"].get("description"),
                Published_Data=item["snippet"]["publishedAt"],
                Duration=item["contentDetails"]["duration"],
                Views=item["statistics"].get("viewCount"),
                Likes=item["statistics"].get("likeCount"),
                Comments=item["statistics"].get("commentCount"),
                Favorite_Count=item["statistics"]["favoriteCount"],
                Definition=item["contentDetails"]["definition"],
                Caption_Status=item["contentDetails"]["caption"]
                )
        video_data.append(data)
        return video_data
    
def get_comment_info(video_ids):
  Comment_data=[]
  try:
    for video_id in video_ids:
      request=youtube.commentThreads().list(
          part="snippet",
          videoId=video_id,
          maxResults=50
      )
      response=request.execute()

      for item in response["items"]:
        data=dict(Comment_Id=item["snippet"]["topLevelComment"]["id"],
                  Video_Id=item["snippet"]["topLevelComment"]["snippet"]["videoId"],
                  Comment_Text=item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                  Comment_Author=item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                  Comment_Published=item["snippet"]["topLevelComment"]["snippet"]["publishedAt"])
        Comment_data.append(data)
  except:
    pass
  return Comment_data


client=MongoClient("mongodb+srv://jaya:111916@cluster0.9l8a2jd.mongodb.net/?retryWrites=true&w=majority") # dt1819.leo
db = client["Youtube_data"]

def channel_details(channel_id):
  ch_details=get_channel_info(channel_id)
  pl_details=get_playlist_details(channel_id)
  vi_ids=get_video_ids(channel_id)
  vi_details=get_video_info(vi_ids)
  com_details=get_comment_info(vi_ids)
  
  coll1 = db["channel_details"]
  coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,
                    "video_information":vi_details,"comment_information":com_details})

  return "upolad completed succussfully"


def channels_tables():

   mydb = psycopg2.connect(host="localhost",
                           user="postgres",
                           password="111916",
                           database="youtube_data",
                           port="5432")
   cursor=mydb.cursor()

   drop_query='''drop table if exists channels'''
   cursor.execute(drop_query)
   mydb.commit()

   try:
      create_query='''create table if not exists channels(Channel_Name varchar(100),
                                                               Channel_Id varchar(100) primary key,
                                                               Subscribers bigint,
                                                               Views bigint,
                                                               Total_Videos int,
                                                               Channel_Description text,
                                                               Playlist_Id varchar(100))'''
      cursor.execute(create_query)
      mydb.commit()
   except:
      print("Channels table already created")

   ch_list=[]
   db=client["Youtube_data"]
   coll1=db["channel_details"]
   for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
      ch_list.append(ch_data["channel_information"])
   df=pd.DataFrame(ch_list)

   for index,row in df.iterrows():
         insert_query='''insert into channels(Channel_Name,
                                             Channel_Id,
                                             Subscribers,
                                             Views,
                                             Total_Videos,
                                             Channel_Description,
                                             Playlist_Id)

                                             values(%s,%s,%s,%s,%s,%s,%s)'''
         values=(row['Channel_Name'],
                  row['Channel_Id'],
                  row['Subscribers'],
                  row['Views'],
                  row['Total_Videos'],
                  row['Channel_Description'],
                  row['Playlist_Id'])
         try:
               cursor.execute(insert_query,values)
               mydb.commit()
         except:
               print("Channels values are already inserted")

def playlists_table():

    mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="111916",
                            database="youtube_data",
                            port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists playlists'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists playlists(Playlist_Id varchar(100) primary key,
                                                            Title varchar(100),
                                                            Channel_Id varchar(100),
                                                            Channel_Name varchar(100),
                                                            PublishedAt timestamp,
                                                            Video_Count int
                                                            )'''
    cursor.execute(create_query)
    mydb.commit()

    pl_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])
    df1=pd.DataFrame(pl_list)

    for index,row in df1.iterrows():
        insert_query='''insert into playlists(Playlist_Id,
                                            Title,
                                            Channel_Id,
                                            Channel_Name,
                                            PublishedAt,
                                            Video_Count)
                                            values(%s,%s,%s,%s,%s,%s)'''
        values=(row['Playlist_Id'],
                row['Title'],
                row['Channel_Id'],
                row['Channel_Name'],
                row['PublishedAt'],
                row['Video_Count'])

        cursor.execute(insert_query,values)
        mydb.commit()


def videos_table():
    mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="111916",
                            database="youtube_data",
                            port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists videos'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists videos(Channel_Name varchar(100),
                                                    Channel_Id varchar(100),
                                                    Video_Id varchar(30),
                                                    Title varchar(150),
                                                    Tags text,
                                                    Thumbnail varchar(200),
                                                    Description text,
                                                    Published_Data timestamp,
                                                    Duration interval,
                                                    Views bigint,
                                                    Likes bigint,
                                                    Comments int,
                                                    Favorite_Count int,
                                                    Definition varchar(20),
                                                    Caption_Status varchar(50)
                                                    )'''
    cursor.execute(create_query)
    mydb.commit()

    vi_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
            for i in range(len(vi_data["video_information"])):
                    vi_list.append(vi_data["video_information"][i])
    df2=pd.DataFrame(vi_list)

    for index,row in df2.iterrows():
                    insert_query='''insert into videos(Channel_Name,
                                                        Channel_Id,
                                                        Video_Id,
                                                        Title,
                                                        Tags,
                                                        Thumbnail,
                                                        Description,
                                                        Published_Data,
                                                        Duration,
                                                        Views,
                                                        Likes,
                                                        Comments,
                                                        Favorite_Count,
                                                        Definition,
                                                        Caption_Status
                                                        )
                                                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                    values=(row['Channel_Name'],
                            row['Channel_Id'],
                            row['Video_Id'],
                            row['Title'],
                            row['Tags'],
                            row['Thumbnail'],
                            row['Description'],
                            row['Published_Data'],
                            row['Duration'],
                            row['Views'],
                            row['Likes'],
                            row['Comments'],
                            row['Favorite_Count'],
                            row['Definition'],
                            row['Caption_Status'])

                    cursor.execute(insert_query,values)
                    mydb.commit()


def comments_table():
    mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="111916",
                            database="youtube_data",
                            port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists comments'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists comments(Comment_Id varchar(100) primary key,
                                                        Video_Id varchar(100),
                                                        Comment_Text text,
                                                        Comment_Author varchar(100),
                                                        Comment_Published timestamp
                                                        )'''
    cursor.execute(create_query)
    mydb.commit()

    com_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3=pd.DataFrame(com_list)

    for index,row in df3.iterrows():
        insert_query='''insert into comments(Comment_Id,
                                            Video_Id,
                                            Comment_Text,
                                            Comment_Author,
                                            Comment_Published)
                                            values(%s,%s,%s,%s,%s)'''
        values=(row['Comment_Id'],
                row['Video_Id'],
                row['Comment_Text'],
                row['Comment_Author'],
                row['Comment_Published'])

        cursor.execute(insert_query,values)
        mydb.commit()


def tables():
  channels_tables()
  playlists_table()
  videos_table()
  comments_table()

  return "Tables Created succesfully"

def show_channels_table():
  ch_list=[]
  db=client["Youtube_data"]
  coll1=db["channel_details"]

  for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
    ch_list.append(ch_data["channel_information"])
  df=st.dataframe(ch_list)
  return df

def show_playlists_table():
    pl_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])
    df1=st.dataframe(pl_list)
    return df1

def show_videos_table():
  vi_list=[]
  db=client["Youtube_data"]
  coll1=db["channel_details"]
  for vi_data in coll1.find({},{"_id":0,"video_information":1}):
    for i in range(len(vi_data["video_information"])):
      vi_list.append(vi_data["video_information"][i])
  df2=st.dataframe(vi_list)
  return df2

def show_comments_table():
  com_list=[]
  db=client["Youtube_data"]
  coll1=db["channel_details"]
  for com_data in coll1.find({},{"_id":0,"comment_information":1}):
    for i in range(len(com_data["comment_information"])):
      com_list.append(com_data["comment_information"][i])
  df3=st.dataframe(com_list)
  return df3

with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("SKILL TAKE AWAY")
    st.caption('Python scripting')
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption(" Data Managment using MongoDB and SQL")
    
channel_id = st.text_input("Enter the Channel id")
channels = channel_id.split(',')
channels = [ch.strip() for ch in channels if ch]

if st.button("Collect and Store data"):
    for channel in channels:
        ch_ids = []
        db = client["Youtube_data"]
        coll1 = db["channel_details"]
        for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
            ch_ids.append(ch_data["channel_information"]["Channel_Id"])
        if channel in ch_ids:
            st.success("Channel details of the given channel id: " + channel + " already exists")
        else:
            output = channel_details(channel)
            st.success(output)
            
if st.button("Migrate to SQL"):
    display = tables()
    st.success(display)
    
show_table = st.radio("SELECT THE TABLE FOR VIEW",(":green[channels]",":orange[playlists]",":red[videos]",":blue[comments]"))

if show_table == ":green[channels]":
    show_channels_table()
elif show_table == ":orange[playlists]":
    show_playlists_table()
elif show_table ==":red[videos]":
    show_videos_table()
elif show_table == ":blue[comments]":
    show_comments_table()


mydb = psycopg2.connect(host="localhost",
                           user="postgres",
                           password="111916",
                           database="youtube_data",
                           port="5432")
cursor=mydb.cursor()

question=st.selectbox("select your question",("1.All the videos and the channel name",
                                              "2.channel with most number of videos",
                                              "3.10 most viewed vodeos",
                                              "4.comments in each videos",
                                              "5.videos with highest like",
                                              "6.likes of all videos",
                                              "7.views in each channel",
                                              "8.videos published in the year of 2022",
                                              "9.average duration of all videos in each channel",
                                              "10.videos with highest number of comments"))


if question=="1.All the videos and the channel name":
  query1='''select title as video,channel_name as channelname from videos'''
  cursor.execute(query1)
  mydb.commit()
  t1=cursor.fetchall()
  df=pd.DataFrame(t1,columns=["video title","channelname"])
  st.write(df)

elif question=="2.channel with most number of videos":
  query2='''select channel_name as channelname,total_videos as no_videos from channels
              order by total_videos desc'''
  cursor.execute(query2)
  mydb.commit()
  t2=cursor.fetchall()
  df1=pd.DataFrame(t2,columns=["channelname","no_videos"])
  st.write(df1)

elif question=="3.Top 10 most viewed videos":
  query3='''select views as views,channel_name as channelname,title as videotitle from videos
              where views is not null order by views desc'''
  cursor.execute(query3)
  mydb.commit()
  t3=cursor.fetchall()
  df2=pd.DataFrame(t3,columns=["views","channelname","no_videos"])
  st.write(df2)

elif question=="4.comments in each videos":
  query4='''select comments as no_comments,title as videotitle from videos
              where comments is not null'''
  cursor.execute(query4)
  mydb.commit()
  t4=cursor.fetchall()
  df3=pd.DataFrame(t4,columns=["no of comments","videotitle"])
  st.write(df3)


elif question=="5.videos with highest like":
  query5='''select title as videotitle,channel_name as channelname,Likes as likecount from videos
              where likes is not null order by likes desc'''
  cursor.execute(query5)
  mydb.commit()
  t5=cursor.fetchall()
  df4=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])
  st.write(df4)

elif question=="6.likes of all videos":
  query6='''select Likes as likecount,title as videotitle from videos'''
  cursor.execute(query6)
  mydb.commit()
  t6=cursor.fetchall()
  df5=pd.DataFrame(t6,columns=["likecount","videotitle"])
  st.write(df5)

elif question=="7.views in each channel":
  query7='''select channel_name as channelname,views as Totalviews from channels'''
  cursor.execute(query7)
  mydb.commit()
  t7=cursor.fetchall()
  df6=pd.DataFrame(t7,columns=["channelname","Totalviews"])
  st.write(df6)

elif question=="8.videos published in the year of 2022":
  query8='''select title as video_title,Published_Data as videorelease,channel_name as channelname from videos
          where extract(year from Published_Data)=2022'''
  cursor.execute(query8)
  mydb.commit()
  t8=cursor.fetchall()
  df7=pd.DataFrame(t8,columns=["videotitle","published_Date","channelname"])
  st.write(df7)

elif question=="9. average duration of all videos in each channel":
  query9='''select channel_name as channelname,AVG(duration) as averageduration from videos group by 
            channel_name'''
  cursor.execute(query9)
  mydb.commit()
  t9=cursor.fetchall()
  df8=pd.DataFrame(t9,columns=["channelname","averageduration"])
  df8

  T9=[]
  for index,row in df8.iterrows():
    channel_title=row["channelname"]
    average_duration=row["averageduration"]
    average_duration_str=str(average_duration)
    T9.append(dict(channeltitle=channel_title,averageduration=average_duration_str))
  df1=pd.DataFrame(T9)
  st.write(df1)

elif question=="10.videos with highest number of comments":
  query10='''select title as videotitle,channel_name as channelname, comments as comments from videos
            where comments is not null order by comments desc'''
  cursor.execute(query10)
  mydb.commit()
  t10=cursor.fetchall()
  df9=pd.DataFrame(t10,columns=["videotitle","channelname","comments"])
  st.write(df9)