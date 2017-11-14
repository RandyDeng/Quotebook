#!flask/bin/python
from flask import Flask, flash, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

import boto3
import time
import datetime
import json
	
app = Flask(__name__, static_url_path="")
app.secret_key = '{Uj@wtL=,E5NSWz#;&-zy8!czRoUdlE;rag|Uh(dP$`E]wZ}OGVw)Y]-q#X=(>f'

#Enter AWS Credentials
aws_login = json.loads(open('aws.login').read())
AWS_ACCESS_KEY = aws_login['AWS_ACCESS_KEY']
AWS_SECRET_KEY = aws_login['AWS_SECRET_KEY']
REGION = aws_login['REGION']

# Get the table
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY,
                            region_name=REGION)
table = dynamodb.Table('Quotebook')

# Flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Make database, user object, user_loader callback
user_table = dynamodb.Table('Quotebook_Users')
user_list = user_table.scan()['Items']

class User(UserMixin):
	def __init__(self, username, first_name, last_name, access_level):
		self.username = username
		self.first_name = first_name
		self.last_name = last_name
		self.access_level = access_level
	def is_authenticated(self):
		return True
	def is_active(self):
		return True
	def is_anonymous(self):
		return False
	def get_id(self):
		return str(self.username)

@login_manager.user_loader
def load_user(username):
	user_list = user_table.scan()['Items']
	for u in user_list:
		if u['Username'] == username:
			return User(username, u['First Name'], u['Last Name'], u['Access Level'])
	return

# Redirect to login
@app.route('/')
def home():
	return redirect("/login")

# Displays login page
@app.route('/login', methods=['GET', 'POST'])
def login():
	# handle password checking
	logout_user()
	if request.method == 'POST':
		result = request.form
		username = result['u']
		password = result['p']
		user_list = user_table.scan()['Items']
		for u in user_list:
			if u['Username'] == username and u['Password'] == password:
				user = User(username, u['First Name'], u['Last Name'], u['Access Level'])
				login_user(user)
				return redirect('/quotes')
		return render_template('login.html', error='Invalid username or password')
	else:
		return render_template('login.html', error=None)

# Show quotes and allow deletion
@app.route('/quotes', methods=['GET'])
@login_required
def quotes_page():
	# display sorted content
	quote_list = table.scan()['Items']
	quote_list.sort(key=lambda x: time.mktime(time.strptime(x['Timestamp'], '%Y-%m-%d %H:%M:%S')[0:9]), reverse=True)
	return render_template('quotebook.html', quote_list=quote_list, user_name=(current_user.first_name + " " + current_user.last_name))

# Add quote
@app.route('/add_quote', methods=['GET', 'POST'])
@login_required
def add_quote():
	# handle requests
	if request.method == 'POST':
		result = request.form
		author = result['author']
		quote = result['new_quote']
		# check if author is valid
		if (author == "Other"):
			author = result['custom']
			if (not author):
				author = "Anonymous"
		ts = time.time()
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
		data = {"Timestamp": timestamp, "Author": author, "Quote": quote}
		table.put_item(Item=data)
		return render_template('add_quote.html', success="Your quote was submitted successfully! :)")
	else:
		return render_template('add_quote.html', success=None)

# Delete quote
@app.route('/delete_quote/<string:ts>/<string:author>', methods=['GET'])
@login_required
def delete_quote(ts, author):
	# handle request
	try:
		table.delete_item(Key={'Timestamp': ts, 'Author': author})
	except:
		print ("An error has occurred")
	return redirect('/quotes')

# Log out
@app.route('/logout')
def logout():
	logout_user()
	return redirect('/login')

# Running on EC2 Instance
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=80)
	
