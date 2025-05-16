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

 Make a service account and add these rolls:
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
We need to create an OAuth account for Google Drive access. In the top right hamburger menu select:
 - APIs & Services/Credentials/+Create credentials/OAuth client ID
	- OAuth client ID
		- first configure OAuth screen. Select Desktop App and give it a name.
		- keep track of the Client ID and Client secret, we will need those later.
		- click download JSON from this screen, these are your credentials.

 TODO: enable apis
Now we need to enable the apis. In the top right hamburger menu select:
	- APIs & Services
	From this menu select `Google Drive API` and click `Enable API`. Do the same for `Google
 Earth Engine API`

 Now we need to add ourselves as a test user
 in google cloud navigate to API's & Servies/OAut concent screen/Audience
	- Scroll down and under Test users click + Add users. Select your main account.


TODO: main file config

## Acknowledgements

This project builds on work from the [WildfireSpreadTSCreateDataset]{https://github.com/SebastianGer/WildfireSpreadTSCreateDataset}. Credit to original authors for providing data, methods,
and insights.

