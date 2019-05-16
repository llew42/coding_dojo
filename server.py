from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
from datetime import timedelta
import re

app = Flask(__name__)
app.secret_key = "Shhh be bary bary quiet, I'm hunting wabbit"

bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

# DISPLAY REGISTRATION AND LOGIN FORMS
@app.route('/')
def index():
  return render_template('index.html')

# HANDLE NEW USER REGISTRATION 
@app.route('/register', methods = ['POST'])
def register_user():
  mysql = connectToMySQL('wall')
  if len(request.form['fname']) < 2:
    flash(u'Your first name must be at least 2 characters', 'error')
    return redirect('/')
  if len(request.form['lname']) < 2:
    flash(u'Your last name must be at least 2 characters', 'error')
    return redirect('/')
  if not EMAIL_REGEX.match(request.form['email']):
    flash(u'Invalid email address', 'error')
    return redirect('/')
  db = connectToMySQL('wall')
  query = 'SELECT * FROM users WHERE email = %(em)s'
  data = {
    'em': request.form['email']
  }
  duplicate_email_check = db.query_db(query, data)
  if len(duplicate_email_check) != 0:
    flash(u'Email address already in use', 'error')
    return redirect('/')
  else:
    pw_hash = bcrypt.generate_password_hash(request.form['pw'])
    print(pw_hash)
    query = 'INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s, NOW(), NOW());'
    data = {
      'fn': request.form['fname'],
      'ln': request.form['lname'],
      'em': request.form['email'],
      'pw': pw_hash
    }
    result = mysql.query_db(query, data)
    session['userid'] = result
    flash(u"You've been successfully registered", 'success')
    return redirect('/wall')
  if len(request.form['pw']) < 8:
    flash(u'Your password must be at least 8 characters', 'error')
    return redirect('/')
  if request.form['pw'] != request.form['pw_confirm']:
    flash(u'Your passwords must match' 'error')
    return redirect('/')

# HANDLE USER LOGIN INFORMATION
@app.route('/login', methods = ['POST'])
def login():
  db = connectToMySQL('wall')
  query = 'SELECT * FROM users WHERE email = %(em)s'
  data = {
    'em': request.form['em']
  }
  result = db.query_db(query, data)
  print(request.form)
  if result:
    if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
      session['userid'] = result[0]['id']
      flash(u'Welcome back', 'success')
      return redirect('/wall')
  flash(u"You could not be logged in", 'error')
  return redirect('/')
    
@app.route('/wall')
def wall():
  db = connectToMySQL('wall')
  if 'userid' not in session:
    flash("You need to be logged in to view this page")
    return redirect('/')
  else:
    query = 'SELECT * FROM users WHERE id = %(id)s;'
    data = {
      'id': session['userid']
    }
    users = db.query_db(query, data)
    db = connectToMySQL('wall')
    query = 'SELECT * FROM users ORDER BY first_name;'
    recipients = db.query_db(query)
    print(recipients)
    db = connectToMySQL('wall')
    query = 'SELECT users.id, users.first_name, messages.id, messages.recipient_id, messages.content, messages.created_at FROM users JOIN messages ON users.id = messages.users_id WHERE recipient_id = %(rid)s;'
    data = {
      'rid': session['userid']
    }
    display = db.query_db(query, data)
    message_total = len(display)
    db = connectToMySQL('wall')
    query = 'SELECT COUNT(*) FROM messages WHERE users_id = %(id)s'
    data = {
      'id': session['userid']
    }
    sent_messages = db.query_db(query, data)
    return render_template('wall.html', all_users = users, recipients = recipients, display = display, message_total = message_total, sent_messages = sent_messages)

@app.route('/logout')
def logout():
  session.clear()
  return redirect('/')

@app.route('/messages', methods = ['POST'])
def messages():
  # check message validity length
  if len(request.form['message']) < 5:
    flash('Your message must be at least 5 characters')
    return redirect ('/wall')
  else:
    # connect to db
    db = connectToMySQL('wall')
    # write query INSERT INTO (COMMENT, USER_ID, AUTHOR_ID)
    query = 'INSERT INTO messages (content, users_id, recipient_id) VALUES (%(cm)s, %(ui)s, %(ri)s);'
    # data
    data = {
      'cm': request.form['message'],
      'ui': session['userid'],
      'ri': request.form['recipient_id']
    }
    # run query_db
    db.query_db(query, data)
    print(request.form)
    return redirect('/wall')

@app.route('/delete/<id>')
def delete_message(id):
  # connect to db
  db = connectToMySQL('wall')
   ####### DELETE USING MESSAGE ID PRIMARY KEY IT'S UNIQUE
  query = 'DELETE FROM messages WHERE id = %(id)s;'
  # data
  data = {
    'id': id,
  }
  db.query_db(query, data)
  return redirect('/wall')

if __name__ == "__main__":
  app.run(debug=True)
