######################################
# author ben lawson <balawson@bu.edu> 
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, session
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import datetime
import operator
from flask.ext.login import AnonymousUserMixin,current_user
#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!
app.debug = True

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'wyt3838438'
app.config['MYSQL_DATABASE_DB'] = 'pa1'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from users") 
users = cursor.fetchall()

login_manager.anonymous_user = AnonymousUserMixin
class AnonymousUserMixin:
	def __init__(self):
		self.id = 999999999999
def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass
@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname = request.form.get('first_name')
		lname = request.form.get('last_name')
		dob=request.form.get('dob')
		gender = request.form.get('gender')
		hometown = request.form.get('hometown')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO users (first_name, last_name, email, date_of_birth, hometown, gender, password) VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}','{6}')".format(fname, lname, email, dob, hometown, gender, password))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def youmayalso(uid):
	tags = getUserTag(uid)
	query_head = "SELECT P.imgdata, T.photo_id, P.caption FROM photos P, tags T, albums A WHERE A.owner_d = '{0}' AND A.album_id = P.album_id AND P.photo_id = T.photo_id AND (".format(uid)
	query_tail = ") GROUP BY T.photo_id ORDER BY Count(T.text) DESC"
	for tag in tags:
		if tag == tags[-1]:
			query_head += "T.text = '{0}'".format(tag[0])
			break 
		query_head += "T.text = '{0}' OR ".format(tag[0]) 
	query = query_head + query_tail
	print query
	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()

def getUserTag(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM tags T, photos P WHERE P.owner = '{0}' AND P.photo_id = T.photo_id".format(uid))
	return cursor.fetchall()

'''
def tagRecommendation(text):
	pid = getTagsPhotos(text)
	tags = getPhotosTags(pid)
	M = {}
	for i in tags:
		if i != text:
			M[i] = getTagsRank(i)
			print M
	d = sorted(M.items(), key=operator.itemgetter(1), reverse=True)
	return d
'''
def tag_recommendation(tags):
	pics_head = "( SELECT T2.photo_id FROM tags T2 WHERE " 
	badg_head = "( SELECT T3.text FROM tags T3 WHERE "
	for tag in tags:
		if tag == tags[-1]:
			pics_head += "T2.text = '{0}' GROUP BY T2.photo_id HAVING count(*)>= 1 ) As Temp".format(tag)
			badg_head += "T3.text = '{0}' GROUP BY text HAVING count(*) >= 1 )".format(tag)
			break
		pics_head += "T2.text = '{0}' OR ".format(tag)
		badg_head += "T3.text = '{0}' OR ". format(tag)

	query = "SELECT text, count(T1.text) AS dnum FROM tags T1, " + pics_head + " WHERE Temp.photo_id = T1.photo_id AND T1.text NOT IN " + badg_head + " GROUP BY text ORDER BY dnum DESC"
	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()

def getTag():
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM tags GROUP BY text HAVING COUNT(*)>=1")
	return cursor.fetchall()


def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id FROM photos WHERE owner = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersPhotos_1(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM photos WHERE owner = '{0}'".format(uid))
	return cursor.fetchall()

def getUsersName(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUsersNameID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, user_id FROM users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getPhotosTags(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM tags WHERE photo_id = '{0}'".format(pid))
	return cursor.fetchall()

def getTagsPhotos(tid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM tags WHERE text = '{0}'".format(tid))
	l = cursor.fetchall()
	print l
	return l

def getTagsPhotos_1(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id FROM photos WHERE photo_id = '{0}'".format(pid))
	return cursor.fetchall()

def getSinglePhoto(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata FROM photos WHERE photo_id = '{0}'".format(pid))
	return cursor.fetchall()

def getAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name, album_id FROM albums WHERE owner_d = '{0}'".format(uid))
	return cursor.fetchall()

def getAlbumPhotos(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata FROM photos WHERE album_id = '{0}'".format(aid))
	return cursor.fetchall()

def getAlbumPhotosID(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id FROM photos WHERE album_id = '{0}'".format(aid))
	return cursor.fetchall()

def searchFriend(fname, lname):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, user_id FROM users WHERE first_name = '{0}' AND last_name = '{1}' ".format(fname, lname))
	return cursor.fetchall()

def getPhotoUserComment(uid, pid):
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM comments WHERE owener = '{0}' AND photoid = '{1}'".format(uid, pid))
	return cursor.fetchall()

def getPhotoAllComment(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM comments WHERE photoid = '{0}'".format(pid))
	p =  cursor.fetchall()
	print p
	return p

def getPhotoOtherComment(uid, pid):
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM comments WHERE photoid = '{0}' AND owener != '{1}'".format(pid, uid))
	return cursor.fetchall()

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT friend_id FROM friend WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getFriendsName(uid):
	n = []
	cursor = conn.cursor()
	lst = getUsersFriends(uid)
	print lst
	if len(lst) > 0:
		for i in lst:
			r = i[0]
			cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = '{0}'".format(r))
			n += cursor.fetchall()
			print n
	print n
	return n

def getFriendsNameID(uid):
	n = []
	cursor = conn.cursor()
	lst = getUsersFriends(uid)
	print lst
	if len(lst) > 0:
		for i in lst:
			print i
			r = i[0]
			print r
			cursor.execute("SELECT first_name, last_name, user_id FROM users WHERE user_id = '{0}'".format(r))
			n += cursor.fetchall()
			print n
	print n
	return n

def getuserdata(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, date_of_birth, hometown, gender FROM users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def likecount(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user FROM likes WHERE photo_id = '{0}'".format(pid))
	l = cursor.fetchall()
	n = len(l)
	print n
	return n

def likename(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user FROM likes WHERE photo_id = '{0}'".format(pid))
	l = cursor.fetchall()
	print l
	n = []
	for i in l:
		cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = '{0}'".format(i[0]))
		k=cursor.fetchall()
		print k
		n+=k
		print n
	return n

def getUserRank(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM photos WHERE owner = '{0}'".format(uid))
	l = cursor.fetchall()
	cursor.execute("SELECT comment_id FROM comments WHERE owener = '{0}'".format(uid))
	m = cursor.fetchall()
	n = len(l)+len(m)
	return n

def selectUser():
	m = {}
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM users")
	j = cursor.fetchall()
	for i in j:
		name = getUsersNameID(i[0])
		r = i[0]
		m[name[0]] = getUserRank(r)
	d = sorted(m.items(), key=operator.itemgetter(1), reverse=True)
	print d
	return d[0:10]

def getTagsRank(text):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM tags WHERE text = '{0}'".format(text))
	l = cursor.fetchall()
	n = len(l)
	return n

def selectTopTags():
	m = {}
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM tags")
	j = cursor.fetchall()
	for i in j:
		r = i[0]
		m[r] = getTagsRank(r)
	d = sorted(m.items(), key=operator.itemgetter(1), reverse=True)
	print d
	return d[0:10]

'''
def getFriendID(name):
	cursor = conn.cursor()
	cursor.execute("SELECT userid")
'''
def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/goupload', methods=['GET', 'POST'])
@flask_login.login_required
def goupload():
		return render_template('upload.html')



@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		aid = session['album_id']
		print caption
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO photos (imgdata, album_id, caption, owner) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data, aid, caption, uid))
		conn.commit()
		cursor.execute("SELECT P.photo_id FROM photos P ORDER BY P.photo_id DESC LIMIT 1")
		pid = cursor.fetchall()[0][0]
		tags_text = request.form.get('tag')
		print tags_text
		if len(tags_text)>0:
			lst =  tags_text.split(' ')
			for i in lst:
				print i, pid
				cursor.execute("INSERT INTO tags (text, photo_id) VALUES ('{0}', '{1}')".format(i, pid))
				conn.commit()

		return render_template('showphotos.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getAlbumPhotos(aid), tags= getPhotosTags(pid))
	#The method is GET so we return a  HTML form to upload the a photo.
#end photo uploading code 
		'''
		<!doctype html>
		<title>Upload new Picture</title>
		<h1>Upload new Picture</h1>
		<form action="" method=post enctype=multipart/form-data>
		<p><input type=file name=file>
		<input type=submit value=Upload>
		</form></br>
	<a href='/'>Home</a>
		'''
#end photo uploading code 
@app.route('/showalbums', methods=['GET','POST'])
@flask_login.login_required
def showalbums():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('albumlist.html', name=flask_login.current_user.id, message='Your Albums!!!', albums = getAlbums(uid))

@app.route('/createalbum', methods=['GET','POST'])
@flask_login.login_required
def createalbum():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		name = request.form.get('name')
		date = datetime.date.today()
		date = date.strftime('%Y-%m-%d')
		print name
		cursor = conn.cursor()
		cursor.execute("INSERT INTO albums (name,owner_d, date_of_creation) VALUES ('{0}', {1}, '{2}' )".format(name, uid, date))
		conn.commit()
		return render_template('albumlist.html', name=flask_login.current_user.id, message='Album Created!', albums = getAlbums(uid))
	else:
		return render_template('album.html')

@app.route('/photolist', methods=['GET','POST'])
@flask_login.login_required
def photolist():
	if request.method == 'GET':
		session['album_id'] = request.args['album_id']
		album_id = request.args['album_id']
		return render_template('photolist.html', name=flask_login.current_user.id, message='Your Albums!', albums = getAlbumPhotosID(album_id))

@app.route('/friendphotolist', methods=['GET','POST'])
@flask_login.login_required
def friendphotolist():
	if request.method == 'GET':
		session['album_id'] = request.args['album_id']
		album_id = request.args['album_id']
		return render_template('friendphotolist.html', name=flask_login.current_user.id, message='Your Albums!', albums = getAlbumPhotosID(album_id))


@app.route('/singlephoto', methods=['GET','POST'])
@flask_login.login_required
def singlephoto():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = request.args['photo_id']
		session['pid'] = request.args['photo_id']
		print pid
		return render_template('singlephoto.html', name=flask_login.current_user.id, message='Photo Details', uid = uid, photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid), like = likecount(pid), names = likename(pid))



@app.route('/goaddfriend', methods=['GET','POST'])
@flask_login.login_required
def goaddfriend():
	if request.method == 'GET':
		session['friend_id'] = request.args['friend_id']
		fid = request.args['friend_id']
		return render_template('addfriend.html', name=flask_login.current_user.id)


@app.route('/addfriend', methods=['GET','POST'])
@flask_login.login_required
def addfriend():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		friendid = session['friend_id']
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM friend WHERE user_id = '{0}' AND friend_id = '{1}'".format(uid,friendid))
		l = cursor.fetchall()
		if len(l) == 0:
			cursor.execute("INSERT INTO friend (friend_id, user_id) VALUES ('{0}', '{1}')".format(friendid, uid))
			conn.commit()
			return render_template('addfriendsuccess.html',name=flask_login.current_user.id, message='Add Successful!!!', friends = getFriendsName(uid) )
		else:
			return render_template('addfriendsuccess.html', name = flask_login.current_user.id, message = 'Add Duplicate, already added!!',friends = getFriendsName(uid) )

@app.route('/friendlist', methods = ['GET', 'POST'])
@flask_login.login_required
def friendlist():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friendlist.html', name = flask_login.current_user.id, message = 'Friend List!!!',friends = getFriendsNameID(uid))
	   
@app.route('/seefrienddata', methods = ['GET', 'POST'])
@flask_login.login_required
def seefrienddata():
	if request.method == 'GET':
		fid = request.args['friend_id']
		return render_template('frienddata.html',  name = flask_login.current_user.id, message = 'Your friend data',friends = getuserdata(fid), albums = getAlbums(fid))

@app.route('/findfriend', methods=['GET','POST'])
@flask_login.login_required
def findfriend(): 
	if request.method == 'POST':		
		uid = getUserIdFromEmail(flask_login.current_user.id)
		fname = request.form.get('fname')
		lname = request.form.get('lname')
		return render_template('search_list.html', name=flask_login.current_user.id, message = 'Users!', friends = searchFriend(fname, lname))
	else:
		return render_template('search_friend.html')

@app.route('/getcomment', methods=['GET','POST'])
def getcomment():
	if request.method == 'POST':
		comment = request.form.get('comment')
		date = datetime.date.today()
		date = date.strftime('%Y-%m-%d')
		pid = session['pid']
		if current_user.is_authenticated():
			uid = getUserIdFromEmail(flask_login.current_user.id)
			cursor = conn.cursor()
			cursor.execute("INSERT INTO comments (text, owener, date, photoid) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment, uid, date, pid))
			conn.commit()
			return render_template('singlephotocomment.html', name=flask_login.current_user.id, message='Photo Details', photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid),like = likecount(pid),names = likename(pid))
		else:
			uid = 99999
			cursor = conn.cursor()
			cursor.execute("INSERT INTO comments (text, owener, date, photoid) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment, uid, date, pid))
			conn.commit()
			return render_template('singlephotocomment.html', name= 'Visitor', message='Photo Details', photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoAllComment(pid),like = likecount(pid),names = likename(pid))
	
	else:
		return render_template('singlephoto.html')

@app.route('/getrank', methods=['GET','POST'])
def getrank():
	if request.method == 'GET':
		n = selectUser()
		return render_template('rank.html', message = 'Top 10!!!!', users = n)


@app.route('/like', methods=['GET','POST'])
@flask_login.login_required
def like():
	if request.method == 'GET':
		uid = request.args['uid']
		pid = session['pid']
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM likes WHERE user = '{0}' AND photo_id = '{1}'".format(uid,pid))
		l = cursor.fetchall()
		if len(l) == 0:
			cursor.execute("INSERT INTO likes (user, photo_id) VALUES ('{0}', '{1}')".format(uid, pid))
			conn.commit()
			return render_template('singlephoto.html', name=flask_login.current_user.id, message='Photo Details, Like successful!!!!', uid = uid, photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid),like = likecount(pid),names = likename(pid))
		else:
			return render_template('singlephoto.html', name=flask_login.current_user.id, message='Photo Details, Like Duplicated!!!!', uid = uid, photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid), like = likecount(pid),names = likename(pid))

@app.route('/gotop10', methods=['GET','POST'])
def gotop10():
	if request.method == 'GET':
		uid = request.args['user_id']
		return render_template('topuserdata.html', message = 'Top Users data',friends = getuserdata(uid), albums = getAlbums(uid))

@app.route('/topuserphotolist', methods=['GET','POST'])
def topuserphotolist():
	if request.method == 'GET':
		session['album_id_1'] = request.args['album_id']
		album_id = request.args['album_id']
		return render_template('topuserphotolist.html', message='Albums!', albums = getAlbumPhotosID(album_id))

@app.route('/topusersinglephoto', methods=['GET','POST'])
def topusersinglephoto():
	if request.method == 'GET':
		if current_user.is_authenticated():
			uid = getUserIdFromEmail(flask_login.current_user.id)
		else:
			uid = 99999
		pid = request.args['photo_id']
		session['pid_1'] = request.args['photo_id']
		print pid
		return render_template('topusersinglephoto.html', uid = uid, message='Photo Details', photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoAllComment(pid), like = likecount(pid),names = likename(pid))

@app.route('/gettagrank', methods=['GET','POST'])
def gettagrank():
	if request.method == 'GET':
		n = selectTopTags()
		return render_template('toptags.html', message = 'Top 10!!!!', users = n)

@app.route('/tagphotos', methods=['GET','POST'])
def tagphotos():
	if request.method == 'GET':
		tid = request.args['tid']
		n = getTagsPhotos(tid)
		photos = []
		for i in n:
			photos += getTagsPhotos_1(i[0])
		return render_template('tagsphotos.html', message = 'Tags Photos',photos = photos)

@app.route('/tagsearch', methods=['GET','POST'])
@flask_login.login_required
def tagsearch(): 
	if request.method == 'POST':		
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tags = request.form.get('tags')
		n = getTagsPhotos(tags)
		photos = []
		for i in n:
			photos += getTagsPhotos_1(i[0])
		return render_template('tagsearch_photolist.html', name=flask_login.current_user.id, message = 'Users!', photos = photos)
	else:
		return render_template('tagsearch.html')
'''
@app.route('/tagrecommendation', methods=['GET','POST'])
@flask_login.login_required
def tagrecommendation(): 
	if request.method == 'POST':		
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tags = request.form.get('tags')
		m = {}
		if len(tags)>0:
			lst =  tags.split(' ')
			for i in lst:
				m tagRecommendation(i)
		m = m[5]
		return render_template('tagrecommendation_besttag.html', name=flask_login.current_user.id, message = 'Users!', tag = m)
	else:
		return render_template('tagrecommendation_inputpage.html')
'''
@app.route('/tagrecommendation', methods=['GET','POST'])
def tagrecommendation():
	if request.method == 'POST':
		try:
			tags = request.form.get('tags')
		except:
			print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
			return flask.redirect(flask.url_for('/'))
		ws = tags.split(' ')
		print ws
		taglist = []
		print getTag()
		for t in getTag():
			taglist += t
		T = []
		for x in ws:
			print x 
			if x in taglist:
				T += [x]
		print T
		if not T:
			return render_template('tagrecommendation_besttag.html', name=flask_login.current_user.id, message='Recommanded tags', tag=taglist)
		tags = tag_recommendation(T)
		print tags
		return render_template('tagrecommendation_besttag.html', name=flask_login.current_user.id, message='Recommanded tags', tag=tags)
	else:
		return render_template('tagrecommendation_inputpage.html')

@app.route('/tagphotos2', methods=['GET','POST'])
def tagphotos2():
	if request.method == 'GET':
		tid = request.args['tid']
		n = getTagsPhotos(tid)
		photos = []
		for i in n:
			photos += getTagsPhotos_1(i[0])
		return render_template('tagsphotos.html', message = 'Tags Photos',photos = photos)

@app.route('/getcomment2', methods=['GET','POST'])
def getcomment2():
	if request.method == 'POST':
		comment = request.form.get('comment')
		date = datetime.date.today()
		date = date.strftime('%Y-%m-%d')
		pid = session['pid_1']
		if current_user.is_authenticated():
			uid = getUserIdFromEmail(flask_login.current_user.id)
			cursor = conn.cursor()
			cursor.execute("INSERT INTO comments (text, owener, date, photoid) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment, uid, date, pid))
			conn.commit()
			return render_template('singlephotocomment.html', name=flask_login.current_user.id, message='Photo Details', photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid),like = likecount(pid),names = likename(pid))
		else:
			uid = 99999
			cursor = conn.cursor()
			cursor.execute("INSERT INTO comments (text, owener, date, photoid) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment, uid, date, pid))
			conn.commit()
			return render_template('singlephotocomment.html', name= 'Visitor', message='Photo Details', photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoAllComment(pid),like = likecount(pid),names = likename(pid))
	
	else:
		return render_template('singlephoto.html')

@app.route('/like2', methods=['GET','POST'])
@flask_login.login_required
def like2():
	if request.method == 'GET':
		uid = request.args['uid']
		pid = session['pid_1']
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM likes WHERE user = '{0}' AND photo_id = '{1}'".format(uid,pid))
		l = cursor.fetchall()
		if len(l) == 0:
			cursor.execute("INSERT INTO likes (user, photo_id) VALUES ('{0}', '{1}')".format(uid, pid))
			conn.commit()
			return render_template('singlephoto.html', name=flask_login.current_user.id, message='Photo Details, Like successful!!!!', uid = uid, photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid),like = likecount(pid),names = likename(pid))
		else:
			return render_template('singlephoto.html', name=flask_login.current_user.id, message='Photo Details, Like Duplicated!!!!', uid = uid, photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid),like = likecount(pid),names = likename(pid))

@app.route('/deletealbum', methods=['GET','POST'])
@flask_login.login_required
def deletealbum():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_id = session['album_id']
		cursor = conn.cursor()
		cursor.execute("DELETE FROM albums WHERE album_id = '{0}'".format(album_id))
		conn.commit()
		return render_template('albumlist.html', name=flask_login.current_user.id, message='Your Albums!!!', albums = getAlbums(uid))

@app.route('/mysinglephoto', methods=['GET','POST'])
@flask_login.login_required
def mysinglephoto():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = request.args['photo_id']
		session['pid'] = request.args['photo_id']
		print pid
		return render_template('mysinglephoto.html', name=flask_login.current_user.id, message='Photo Details', uid = uid, photos = getSinglePhoto(pid), tags= getPhotosTags(pid), comments = getPhotoUserComment(uid, pid), others = getPhotoOtherComment(uid, pid),like = likecount(pid),names = likename(pid))

@app.route('/deletephoto', methods=['GET','POST'])
@flask_login.login_required
def deletephoto():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = session['pid']
		album_id = session['album_id']
		cursor = conn.cursor()
		cursor.execute("DELETE FROM photos WHERE photo_id = '{0}'".format(pid))
		conn.commit()
		return render_template('photolist.html', name=flask_login.current_user.id, message='Your Albums!', albums = getAlbumPhotosID(album_id))

@app.route('/youmayalsolike', methods=['GET','POST'])
@flask_login.login_required
def youmayalsolike():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		a = youmayalso(uid)
		print a
	return render_template('youmayalsolike.html', message='You May Also Like', likes = a)
#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)