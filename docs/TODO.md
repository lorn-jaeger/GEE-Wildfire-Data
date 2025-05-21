# TODO List

- [x] Dataset only goes to 2021, make a bounds check for year.

- [ ] file conversion tiff to hdf5

- [ ] Catch timeout when downloading data.[^2]

- [ ] Tie to Jesse's google drive, might be weird because its a shared folder.

- [ ] Whats the spacial/temporal resolutions for each tiff file from google earth engine?[^1]

# Known Issues

- There were a ton of fires in 2021, and Google doesn't like it when you pull 
  more than 5000 entries at once. How the batch exporting is done will need to be changed.[^2]


# Footnotes

[^1] The WildfireSpreadTS paper re-samples them to a 375m resolution.
