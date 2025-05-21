# TODO List

- [x] Authenticate with google user account not a service account.

- [ ] We want to pull fires with a small minimum size. But this has a known issue [^1].

- [x] Dataset only goes to 2021, make a bounds check for year.

- [ ] Remote desktop for ssh compatibility?

- [ ] Configuration is funky. It should be streamlined

- [ ] When generating geojson, make sure the path exists and/or create it.

- [ ] file conversion tiff to hdf5

- [ ] Catch timeout when downloading data.[^1]

- [ ] Program config defaults should have relative paths.

- [ ] Tie to Jesse's google drive, might be weird because its a shared folder.

- [ ] Whats the spacial/temporal resolutions for each tiff file from google earth engine?

# Known Issues

- There were a ton of fires in 2021, and Google doesn't like it when you pull 
  more than 5000 entries at once. How the exporting is done will need to be changed, done in batches by month.[^1]


# Footnotes

