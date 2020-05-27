# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 08:50:38 2019

@author: Larry

A class to manage the database for BirdBuddys
"""
import sqlite3
import pandas as pd
from sqlite3 import Error
import numpy as np
import io


class bbdb:
	db_file = "bb.db"
	conn = None
	cursor = None
	
	def __init__(self):
		#Connect
		self.connect()
		#verify tables and erase everything and start over if not perfect
		if self.verify() == False:
			self.createTables() #create the tables first then remove any incidental data that may have existed
			self.wipeDB() #Need to make this less deletey later.
		
		
	def connect(self):
		try:
			bbdb.conn = sqlite3.connect(bbdb.db_file)
			bbdb.cursor = bbdb.conn.cursor()
			print(sqlite3.version)
			print("db created")
		except Error as e:
			print(e)

	def verify(self):
		bbdb.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='files' or name='tracked_objects' or name='classifications');")
		rows = bbdb.cursor.fetchall()
		
		if len(rows) != 3:
			return False
		
	def createTables(self):
		create_table_sql = []
		
		create_table_sql.append(""" 
										CREATE TABLE IF NOT EXISTS tracked_objects (
										id integer,
										path text,
										x integer NOT NULL,
										y integer NOT NULL,
										w integer NOT NULL,
										h integer NOT NULL,
										frame_start integer NOT NULL,
										frame_end integer NOT NULL,
										classification text,
										xywh_track text,
										image blob,
										primary key(id, path),
										FOREIGN KEY(path) REFERENCES files(path)
										); 
										"""
										)
		create_table_sql.append(""" 
										CREATE TABLE IF NOT EXISTS files (
										path text PRIMARY KEY,
										name text,
										last_run text,
										frame_count integer,
										w integer,
										h integer
										); 
										"""
								)
		
		create_table_sql.append(""" 
										CREATE TABLE IF NOT EXISTS classifications (
										path text,
										name text,
										primary key(path, name),
										FOREIGN KEY(path) REFERENCES files(path)
										); 
										"""
										)

		for c in create_table_sql:
			try:
				bbdb.conn.cursor().execute(c)
				print(c)
			except Error as e:
				print(e)
		bbdb.conn.commit()
		
				
	def getFiles(self):
		bbdb.cursor.execute("SELECT * FROM files;")
		rows = bbdb.cursor.fetchall()
		
		ret = []
		for count, r in enumerate(rows,start = 0):
			ret.append(rows[count][0]) #peel off the path from database

		return ret
	
	def numFiles(self):
		return len(self.getFiles())
	
	def addFile(self,path):
		print("Adding files object")
		
		sql = ''' INSERT INTO files(path,last_run)
			  VALUES(?,?) '''
		data_tuple = (path, None)
		bbdb.cursor.execute(sql, data_tuple)
		bbdb.conn.commit()
		print("Python Variables inserted successfully into SqliteDb_developers table")
	
	def wipeDB(self):
		bbdb.cursor.execute("delete from files;")
		bbdb.cursor.execute("delete from tracked_objects;")
		bbdb.cursor.execute("delete from classifications;")
		bbdb.conn.commit()
		
	def convertToBinaryData(self, filename):
		# Convert digital data to binary format
		with open(filename, 'rb') as file:
			binaryData = file.read()
		return binaryData		

	def addTrackedObject(self, to, path):
		print("Adding tracked object")
		
		sql = ''' INSERT INTO tracked_objects(id,path,x,y,w,h,frame_start,frame_end,xywh_track,image,classification) VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
		image_binary = to.image.tobytes()

		data_tuple =(to.ID, path, 
					to.x, to.y, to.w, to.h,
					to.frame_start,to.frame_end,
					str(to.xywh_track),
					image_binary,
					to.classification)
		bbdb.cursor.execute(sql, data_tuple)
		bbdb.conn.commit()
		print("Python Variables inserted successfully into SqliteDb_developers table")
		
	def __del__(self):
		bbdb.conn.close()
		
	def selectFile(self,path):
		sql_query = 'select * from tracked_objects where path = \'%s\';' % (path)
		df = pd.read_sql_query(sql_query, bbdb.conn)
		df['time'] = df['frame_end'] - df['frame_start']
		df['area'] = df['w'] * df['h']
		"""g=(ggplot(df)         # defining what data to use
		 + aes(x='frame_start', y='id', width = 'w', fill = 'id')    # defining what variable to use
		  + geom_col(size=20) # defining the type of plot to use
		  )
		#show the longest tracked objects, widest width one, id on x axis, width on y axis
		df=df.sort_values(by='time', ascending=True)
		g1=(
		  ggplot(df) + 
		  aes(x='id', y='time', width = 20, fill = 'id')  +   # defining what variable to use
		  geom_col(size=20) # defining the type of plot to use
		  )
		
		
		#show the largest to smallest area ones - like a descending bar graph
		df=df.sort_values(by='area', ascending=True)
		g2=(
		  ggplot(df) + 
		  aes(x='id', y='area', width = 1, fill = 'id')  +   # defining what variable to use
		  geom_col(size=20) # defining the type of plot to use
		  )		
		
		
		#show classifications bar graph by type
		
		g3=(
		  ggplot(df) + 
		  aes(x='id', y='area', width = 1, fill = 'id')  +   # defining what variable to use
		  geom_col(size=20) # defining the type of plot to use
		  )
		
		#show object classification bar graph sorted
		# Determine order and create a categorical type
		# Note that value_counts() is already sorted
		classification_list = df['classification'].value_counts().index.tolist()
		classification_cat = pd.Categorical(df['classification'], categories=classification_list)

		# assign to a new column in the DataFrame
		df = df.assign(classification_cat = classification_cat)
		g4 = (
		   ggplot(df) + 
		   aes(x='classification_cat') +
		   geom_bar(size=20) +
		   coord_flip() + 
		   labs(y='Count', x='Classification', title='Number of objects by classification')
			)
		g1"""
		return df
		
	def updateFrameCount(self,path,frame_count):
		bbdb.cursor.execute("update files set frame_count = ? where path = ?", (frame_count, path))
		bbdb.conn.commit()
		
	def setClassification(self, classification, path, id):		
		bbdb.cursor.execute("update tracked_objects set classification = ? where path = ? and id = ?", (classification, path, id))	
		bbdb.conn.commit()
	
	def getClassifications(self, path):
		return (None)

	def getRecords(self,path):
		sql_query = 'select * from tracked_objects where path = \'%s\';' % (path)
		df = pd.read_sql_query(sql_query, bbdb.conn)
		df['time'] = df['frame_end'] - df['frame_start']
		df['area'] = df['w'] * df['h']
		return df
	
	def getPossibles(self,path):
		sql_query = 'select * from classifications where path = \'%s\';' % (path)
		df = pd.read_sql_query(sql_query, bbdb.conn)
		df = df['name']
		ret = []
		for n in df:
			prob = 0
			ret.append((n,prob))
		return ret
	
	def updateDimensions(self, path, w, h):
		bbdb.cursor.execute("update files set w = ?, h = ? where path = ?", (w,h, path))
		bbdb.conn.commit()		

	def getHeight(self,path):
		sql_query = 'select h from files where path = \'%s\';' % (path)
		df = pd.read_sql_query(sql_query, bbdb.conn)
		return df['h'][0]
		

	def getWidth(self,path):
		sql_query = 'select w from files where path = \'%s\';' % (path)
		df = pd.read_sql_query(sql_query, bbdb.conn)
		return df['w'][0]