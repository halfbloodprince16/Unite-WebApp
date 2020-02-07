#!venv/bin/python
import os
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
import flask_admin
from flask_admin.contrib import sqla
from collections import OrderedDict
from flask_admin import helpers as admin_helpers
from flask_admin import BaseView, expose
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired
from flask_security.forms import RegisterForm
import requests, time, random
from bs4 import BeautifulSoup
import sqlite3, pymongo
from InstagramAPI import InstagramScraper
from TwitterAPI import TwitterScraper
from FacebookAPI import FacebookScraper
from SentenceClassifier import SentenceCategorizer

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["unite"]
mycoll = mydb["user"]

k = InstagramScraper()
t = TwitterScraper()
f = FacebookScraper()
sc = SentenceCategorizer()


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config_login.py')
db = SQLAlchemy(app)


# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    twitter_id = db.Column(db.String(255), unique=True)
    instagram_id = db.Column(db.String(255), unique=True)
    linkedin_id = db.Column(db.String(255), unique=True)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email

class ExtendedRegisterForm(RegisterForm):
    first_name = StringField('First Name', [DataRequired()])
    last_name = StringField('Last Name', [DataRequired()])
    twitter_id = StringField('Twitter ID', [DataRequired()])
    instagram_id = StringField('Instagram ID', [DataRequired()])
    linkedin_id = StringField('LinkedIn ID', [DataRequired()])
    print(first_name)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore,register_form=ExtendedRegisterForm)


# Create customized model view class
class MyModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


    # can_edit = True
    edit_modal = True
    create_modal = True    
    can_export = True
    can_view_details = True
    details_modal = True


class UserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = column_editable_list
    column_exclude_list = ['password']
    # form_excluded_columns = column_exclude_list
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list


class CustomView(BaseView):
    @expose('/',methods=["GET","POST"])
    def index(self):
    	conn  =sqlite3.connect("db.sqlite")
    	c = conn.cursor()
    	res = []
    	user_info = OrderedDict()
    	insta_text = []
    	pie_chart = {}
    	if request.method == "POST":
	    	text = request.form["search"]
	    	#print(text)
	    	c.execute("select * from user where first_name = '"+text+"' ")
        	res = c.fetchall()
        	#print(res)
        	if(res == []):
        		print("empty")
        		user_info = {"Status":"No Such User Found !"}
        	else:
	        	instagram_id = res[0][6]
	        	twitter_id = res[0][5]
	        	linkedin_id  =res[0][7]
	        	name = res[0][1] +" "+ res[0][2]
	        	email = res[0][3]
	        	print(instagram_id)
	        	print(linkedin_id)
	        	print(twitter_id)

	        	try:
	        		results = k.profile_page_recent_posts('https://www.instagram.com/'+instagram_id+'/?hl=en')
	        	except:
	        		results = []

	        	try:
	        		tweets = t.get_profile(twitter_id)
	        	except:
	        		tweets = []

	        	try:
					face = f.get_profile("EAAG3vNkCRfgBAAyIt6fun9QClx4OECOWj2lsOEs1fe7pvgJeUxh6igZA3eAGc1iaFyTVCEqw8hGwm1sXPo5IZAxjeTIvRZA3AZC1yQwWA2FCMZA414cmATguLeVxuO9ZCCleVD5K49FULucHoAZCRqhyki4hQE6ag0Wrej8MC6Oquzr3gfJSQ1qtGVuqy1IzaggYs7iWbhXGmw01jqcP87e")
	        	
	        	except:
	        		face = {"user_photos":[],
	        				"dob":"unknown",
	        				"address":{"name":"unknown"}
	        				}

				if(results != []):
					try:
						for x in range(0,len(results)):
							insta_text.append(results[x]["edge_media_to_caption"]["edges"][0]["node"]["text"])
					except IndexError:
						pass
				else:
					insta_text = []

	        	if(tweets != []):
		        	tweet_id = []
			        tweet_text = []
			        for info in tweets[:10]:
			            tweet_id.append(format(info.id))
			            tweet_text.append(info.full_text)

		        insta_categories = sc.categorize(insta_text)
		        twitter_categories = sc.categorize(tweet_text)
		        
		        """
		        print(insta_categories)
		        print(type(insta_categories))
		        print(twitter_categories)
		        print(type(twitter_categories))
		        """

		        pie_chart = {'Travel Lover':int(0),'Food Lover':int(0),'Family Lover':int(0),'Entertainment Lover':int(0),\
		        'Sports Lover':int(0),'Finance Lover':int(0),'Politics Lover':int(0),'Marketing Lover':int(0),\
		        'Technology Lover':int(0),'Environment Lover':int(0),'Medical Lover':int(0),'Humanity Lover':int(0),\
		        'Pets Lover':int(0),'military Lover':int(0)}

		        for i in insta_categories.iteritems():
		        	pie_chart[i[1]] = pie_chart[i[1]] + 1

		        for i in twitter_categories.iteritems():
		        	pie_chart[i[1]] = pie_chart[i[1]] + 1
		       	print(pie_chart)

		        user_info = {"name":name,
		                     "email":email,
		                     "instagram_data":insta_text,
		                     "instagram_summary":insta_categories,
		                     "twitter_data":tweet_text,
		                     "twitter_summary":twitter_categories,
		                     "facebook_photos":face["user_photos"],
		                     "dob":face["dob"],
		                     "address":face["address"]["name"]}

		        #mycoll.insert_one(user_info)
	        #print(user_info)
        return self.render('admin/custom_index.html',result = user_info.copy(),pie_chart=pie_chart)


class NewView(BaseView):
    @expose('/',methods=["GET","POST"])
    def index(self):
    	print("youuu i have been called")
    	return self.render('admin/main_page.html')


# Flask views
@app.route('/')
def index():
    return render_template('index.html')

# Create admin
admin = flask_admin.Admin(
    app,
    'My Dashboard',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(MyModelView(Role, db.session, menu_icon_type='fa', menu_icon_value='fa-server', name="Roles"))
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name="Users"))
admin.add_view(CustomView(name="Customer view", endpoint='custom', menu_icon_type='fa', menu_icon_value='fa-connectdevelop',))
admin.add_view(NewView(name="New view", endpoint='new', menu_icon_type='fa', menu_icon_value='fa-connectdevelop',))

# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )

def build_sample_db():
    import string
    import random

    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        first_names = ['admin']
        last_names = ['admin']

        for i in range(len(first_names)):
            tmp_email = first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            tmp_pass = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
            user_datastore.create_user(
                first_name=first_names[i],
                last_name=last_names[i],
                email=tmp_email,
                password=encrypt_password(tmp_pass),
                twitter_id = "xyz.04",
                instagram_id = "xyz.04",
                linkedin_id = "xyz.04",
                roles=[user_role, ]
            )
        db.session.commit()
    return

if __name__ == '__main__':

    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])


    # Build a sample db on the fly, if one does not exist yet.
    if not os.path.exists(database_path):
        build_sample_db()

    # Start app
    app.run(debug=True)