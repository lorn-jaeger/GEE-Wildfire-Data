 # Todo List

- catch timeout

- quality README

- central install file

- strip notebooks into python files

- tie to Jesse's google drive, might be weird because its a shared folder. Multiple writing.

- containerize and publish

# Prerequisite

 I ran into some problems with google cloud. I signed up for a non-commercial earth engine account
 https://earthengine.google.com/noncommercial/.
 Keep track of the project ID we will need it later.

 As of mid-2023, Google Earth Engine access must be linked to a Google Cloud Project, even for
 free/non-commercial usage.

 # Install/Config instructions

 Make a service account and added these rolls:
 - Owner
 - Service Usage Admin
 - Service Usage Consumer
 - Storage Admin
 - Storage Object Creator

 In main account add these rolls:
 - Owner
 - Service Usage Admin
 - Service Usage Consumer

 We then created an oath account for google drive access.
 - APIs & Services/Credentials/+Create credentials
	- configure OAuth screen, must be a desktop app
	- OAuth client ID
		- select Desktop App and give it a name.
		- keep the Client ID and Client secret in a text file for later use.
		- click download JSON from this screen, rename it to credentials.json, and move it
		to the head of the project.

 TODO: enable apis

 Now we need to add ourselves as a test user
 in google cloud navigate to API's & Servies/OAut concent screen/Audience
	- Scroll down and under Test users click + Add users. Select your main account.


TODO: main file config


