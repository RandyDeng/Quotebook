#!flask/bin/python
from flask import Flask, flash, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

import boto3
import time
import datetime
import json
import hashlib
	
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
login_manager.session_protection = "strong"
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
		self.authenticated = False;
		self.active = False;
	def is_authenticated(self):
		return self.authenticated
	def is_active(self):
		return self.active
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
	# handle password hashing and checking
	logout_user()
	if request.method == 'POST':
		result = request.form
		hasher = hashlib.sha512()
		hasher.update(result['u'])
		username = hasher.hexdigest()
		hasher = hashlib.sha512()
		hasher.update(result['p'])
		password = hasher.hexdigest()

		user_list = user_table.scan()['Items']
		for u in user_list:
			if u['Username'] == username and u['Password'] == password:
				user = User(username, u['First Name'], u['Last Name'], u['Access Level'])
				login_user(user)
				return redirect('/quotes')
		return render_template('login.html', error='Invalid username or password')
	else:
		return render_template('login.html', error=None)

# Show sorted quotes and allow deletion
@app.route('/quotes', methods=['GET'])
@login_required
def quotes_page():
	quote_list = table.scan()['Items']
	quote_list.sort(key=lambda x: time.mktime(time.strptime(x['Timestamp'], '%Y-%m-%d %H:%M:%S')[0:9]), reverse=True)
	return render_template('quotebook.html', user=current_user, quote_list=quote_list)

# Add quote
@app.route('/add_quote', methods=['GET', 'POST'])
@login_required
def add_quote():
	# Guests may not add quotes
	if (current_user.access_level == "Guest"):
		return redirect('/quotes')
	if request.method == 'POST':
		result = request.form
		author = result.get('author')
		quote = result.get('new_quote')
		# check for custom author option
		if current_user.access_level == "User" or author == None:
			author = current_user.first_name + " " + current_user.last_name
		elif author == "Other":
			author = result.get('custom')
			if (not author):
				author = "Anonymous"
		ts = time.time()
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
		data = {"Timestamp": timestamp, "Author": author, "Quote": quote}
		table.put_item(Item=data)
		flash("Your quote was submitted successfully! :)")
		return render_template('add_quote.html', user=current_user)
	else:
		return render_template('add_quote.html', user=current_user, success=None)

# Delete quote
@app.route('/delete_quote/<string:ts>/<string:author>', methods=['GET'])
@login_required
def delete_quote(ts, author):
	# only admins can delete quotes
	if (not current_user.access_level == "Admin"):
		return redirect('/quotes')
	try:
		table.delete_item(Key={'Timestamp': ts, 'Author': author})
		flash("Quote was successfully deleted.")
	except:
		flash("An error has occurred. Quote was not deleted.")
	return redirect('/quotes')

# Manage accounts
@app.route('/accounts', methods=['GET'])
@login_required
def manage_users():
	# only admins can delete accounts
	if (not current_user.access_level == "Admin"):
		return redirect('/quotes')
	user_list = user_table.scan()['Items']
	return render_template('accounts.html', user=current_user, user_list=user_list)

# Add accounts
@app.route('/accounts', methods=['GET', 'POST'])
@login_required
def add_account():
	# only admins can add accounts
	if (not current_user.access_level == "Admin"):
		return redirect('/quotes')
	if request.method == 'POST':
		result = request.form
		hasher = hashlib.sha512()
		hasher.update(result.get('Username'))
		username = hasher.hexdigest()
		hasher = hashlib.sha512()
		hasher.update(result.get('Password'))
		password = hasher.hexdigest()
		access_level = result.get('Access_Level')
		first_name = result.get('First_Name')
		last_name = result.get('Last_Name')
		user_list = user_table.scan().get('Items')
		for item in user_list:
			if item.get('Username') == username:
				flash("Please select a unique username.")
				return redirect('/accounts')
		new_user = {"Username": username, "Password": password, "Access Level": access_level, "First Name": first_name, "Last Name": last_name}
		user_table.put_item(Item=new_user)
		try:
			flash("User was successfully added.")
		except:
			flash("Failed to add user.")
	return redirect('/accounts')

# Delete account
@app.route('/delete_account/<string:username>/<string:access_level>', methods=['GET', 'POST'])
@login_required
def delete_user(username, access_level):
	# only admins can delete accounts
	if (not current_user.access_level == "Admin"):
		return redirect('/quotes')
	if (access_level == "Admin"):
		flash("You may not delete Admin accounts")
	else:
		try:
			user_table.delete_item(Key={'Username': username})
			flash("Account successfully deleted")
		except:
			flash("Error when deleting account")
	return redirect('/accounts')

# Log out
@app.route('/logout')
def logout():
	logout_user()
	return redirect('/login')

# Running on EC2 Instance
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=80)
	
