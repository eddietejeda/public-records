from flask.ext.sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.orm import relationship
from datetime import datetime
import flask.ext.restless
from public_records_portal import app, db
import json

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	alias = db.Column(db.String(100))
	email = db.Column(db.String(100), unique=True)
	date_created = db.Column(db.DateTime)
	def is_authenticated(self):
		return True
	def is_active(self):
		return True
	def is_anonymous(self):
		return False
	def get_id(self):
		return unicode(self.id)
	def __init__(self, email, alias = None):
		self.email = email
		self.alias = alias
		self.date_created = datetime.now().isoformat()
	def __repr__(self):
		return self.email

class Request(db.Model): 
# The public records request
	__tablename__ = 'request'
	id = db.Column(db.Integer, primary_key =True)
	date_created = db.Column(db.DateTime)
	qas = relationship("QA", cascade="all,delete") # The list of QA units for this request
	status_updated = db.Column(db.DateTime)
	text = db.Column(db.String(), unique=True) # The actual request text.
	subscribers = relationship("Subscriber", cascade ="all, delete") # The list of subscribers following this request.
	owners = relationship("Owner", cascade="all,delete") # The list of city staff ever assigned to the request.
	current_owner = db.Column(db.Integer) # The Owner ID for the city staff that currently 'owns' the request.
	records = relationship("Record", cascade="all,delete") # The list of records that have been uploaded for this request.
	notes = relationship("Note", cascade="all,delete") # The list of notes appended to this request.
	status = db.Column(db.String(400)) # The status of the request (open, closed, etc.)
	creator_id = db.Column(db.Integer, db.ForeignKey('user.id')) # If city staff created it on behalf of the public, otherwise the creator is the subscriber with creator = true
	def __init__(self, text, creator_id = None):
		self.text = text
		self.date_created = datetime.now().isoformat()
		self.creator_id = creator_id
	def __repr__(self):
		return self.text

class QA(db.Model):
# A Q & A block for a request 
	__tablename__ = 'qa'
	id = db.Column(db.Integer, primary_key = True)
	question = db.Column(db.String())
	answer = db.Column(db.String())
	request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
	owner_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Actually just a user ID
	subscriber_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Actually just a user ID
	date_created = db.Column(db.DateTime)
	def __init__(self, request_id, question):
		self.question = question
		self.request_id = request_id
		self.date_created = datetime.now().isoformat()
	def __repr__(self):
		return "Q: %s A: %s" %(question, answer)

class Owner(db.Model): 
# A member of city staff assigned to a particular request, that may or may not upload records towards that request.
	__tablename__ = 'owner'
	id = db.Column(db.Integer, primary_key =True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	records = relationship("Record", cascade="all,delete") # All records that have been uploaded
	request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
	reason = db.Column(db.String()) # Reason they were assigned
	date_created = db.Column(db.DateTime)
	def __init__(self, request_id, user_id, reason= None):
		self.reason = reason
		self.user_id = user_id
		self.request_id = request_id
		self.date_created = datetime.now().isoformat()
	def __repr__(self):
		return self.user_id


class Subscriber(db.Model): 
# A person subscribed to a request, who may or may not have created the request, and may or may not own a part of the request.
	__tablename__ = 'subscriber'
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
	creator = db.Boolean() # True if they created the initial request.
	date_created = db.Column(db.DateTime)
	owner_id = db.Column(db.Integer, db.ForeignKey('owner.id')) # Not null if responsible for fulfilling a part of the request
 	def __init__(self, request_id, user_id):
 		self.user_id = user_id
		self.request_id = request_id
		self.date_created = datetime.now().isoformat()
	def __repr__(self):
		return self.user_id


class Record(db.Model):
# A record that has been uploaded for a request.
	__tablename__ = 'record'
	id = db.Column(db.Integer, primary_key = True)
	date_created = db.Column(db.DateTime)
	owner_id = db.Column(db.Integer, db.ForeignKey('owner.id')) # The city staff who uploaded the record
	doc_id = db.Column(db.Integer) # The document ID. Currently using Scribd API to upload documents.
	request_id = db.Column(db.Integer, db.ForeignKey('request.id')) # The request this record was uploaded for
	description = db.Column(db.String(400)) # A short description of what the record is. 
	filename = db.Column(db.String(400)) # The original name of the file being uploaded.
	url = db.Column(db.String()) # Where it exists on the internet.
	def __init__(self, request_id, owner_id, url = None, doc_id = None, description = None):
		self.doc_id = doc_id
		self.request_id = request_id
		self.owner_id = owner_id
		self.date_created = datetime.now().isoformat()
		self.description = description
		self.url = url
	def __repr__(self):
		return self.records

class Note(db.Model):
# A note on a request.
	__tablename__ = 'note'
	id = db.Column(db.Integer, primary_key = True)
	date_created = db.Column(db.DateTime)
	text = db.Column(db.String())
	request_id = db.Column(db.Integer, db.ForeignKey('request.id')) # The request it belongs to.
	user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # The user who wrote the note. Right now only city staff can.
	def __init__(self, request_id, text, user_id):
		self.text = text
		self.request_id = request_id
		self.user_id = user_id
		self.date_created = datetime.now().isoformat()
	def __repr__(self):
		return self.text

# Create API
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Request, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Owner, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Note, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Record, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(User, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Note, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(QA, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Subscriber, methods=['GET', 'POST', 'PUT', 'DELETE'])
