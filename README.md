 # stuff todo

- github repo

- quality README

- central config file

- central install file

- strip notebooks into python files

- tie to Jesse's google drive, might be weird because its a shared folder. Multiple writing.

- containerize and publish

# Some questions I have:

   - What file are needed? What files are just for testing.

   - TIFF to HDF5?

   - Do the data preparation need to be in a separate folder?

   - What is needed out of the python notebooks?

   - Can we make a single file python script? or a single directory python project?

   - For the central google drive folder, do we need to tie each service account to it? or are we
    going to share a service account?

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

 in main account add these rolls:
 - Owner
 - Service Usage Admin
 - Service Usage Consumer

 We then created an oath account for google drive access.
 -> APIs & Services/Credentials/+Create credentials
	-> configure OAuth screen, must be a desktop app
	-> OAuth client ID
		-> select Desktop App and give it a name.
		-> keep the Client ID and Client secret in a text file for later use.
		-> click download JSON from this screen, rename it to credentials.json, and move it
		to the head of the project.

 TODO: enable apis

 now we need to add ourselves as a test user
 in google cloud navigate to API's & Servies/OAut concent screen/Audience
	-> Scroll down and under Test users click + Add users. Select your main account.

 Now to edit some python scripts. in get_globfire.py line 7. Inside the
 ee.Initialize(project="YOUR_ID") method change the project variable to match your earth engine
 project id.
 In globfire_nb.ipynb edit the same line ee.Initialize(project="YOUR_ID")

#in FirePred.py comment out 
        # self.viirs_af = ee.FeatureCollection('projects/ee-earthdata/assets/fire_archive_SV-C2_574505') # This is the historical archive (02-01-2012 to end of 2024)
 and uncomment
        # self.viirs_af = ee.FeatureCollection('projects/grand-drive-285514/assets/afall')

 you then need to run the first two code blocks of globfire_nb.ipynb to get access to the
 authentication portal. For some reason the get_globfire.py 


