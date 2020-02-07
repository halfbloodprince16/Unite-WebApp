import facebook
import pandas as pd
import joblib
import  numpy as  np
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
#token ="EAAG3vNkCRfgBACMh1gR1q8cySX7x1TfSyZC2R2u7Ims0DnjOsBGMeUASO9QDo0ZA8B33WlAmcows4Y4ZBuRJttgyiZAHihAq1RjSKmvELZCXo16N26SE6XtgJMUA0BwB54XiIoMUbu2b4YuXCjLQdVhPXMCiu7mZBLi8PTKr1gcJvFpDuTq5PHkHDP2gxkXKI2ZBJxhFoqTsCkaqolOg4RI"


class FacebookScraper:
	def __init__(self):
		self.facebook_dict = {}

	def get_profile(self,token):
		fields= ['email,gender,name,birthday,location,posts.limit(2),photos.limit(4){alt_text,images},likes{about}']
		graph = facebook.GraphAPI(token)
		profile = graph.get_object('me',fields=fields)

		email = profile['email']
		gender = profile['gender']
		name_on_fb = profile['name']
		dob = profile['birthday']
		address = profile['location']

		self.facebook_dict['email']=email
		self.facebook_dict['gender']=gender
		self.facebook_dict['name_on_fb']=name_on_fb
		self.facebook_dict['dob']=dob
		self.facebook_dict['address']=address


		photos_fb = []
		for i in profile['photos']['data']:
			p=i['images']
			for j in p:
			    sour=j['source']
			    #print(sour)
			    photos_fb.append(sour)

			    break

		about = profile['likes']['data']

		self.facebook_dict['pages_about']=[]
		self.facebook_dict['user_photos'] = photos_fb

		return self.facebook_dict;



"""
runner code:

from FacebookAPI import FacebookScraper
k = FacebookScraper()
k.get_profile("EAAG3vNkCRfgBACMh1gR1q8cySX7x1TfSyZC2R2u7Ims0DnjOsBGMeUASO9QDo0ZA8B33WlAmcows4Y4ZBuRJttgyiZAHihAq1RjSKmvELZCXo16N26SE6XtgJMUA0BwB54XiIoMUbu2b4YuXCjLQdVhPXMCiu7mZBLi8PTKr1gcJvFpDuTq5PHkHDP2gxkXKI2ZBJxhFoqTsCkaqolOg4RI")

"""