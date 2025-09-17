I have a project for work that I'd like help on. The original codebase this one is based on was meant to build a dataset for predicting wildfire spread called WildfireSpreadTS. It created a bunch of tiffs for each day of about 1000 fires in the United States (one tiff per fire per day). We modified it quite a bit to make using Google Earth Engine a bit easier but we went astray. The pipeline has a lot of stuff that adds unneccessary complexity like command line cosmetics and complicated configs. I want to take this repo and turn it into what it should have been, a simple to use, robust pipeline for creating raster datasets for fire spread. 

Here are my ideas for how the program should be structured. 

The primary user interface for the dataset should be a single config file. It will define where your earthacces and Earth Engine Credentials are, where your raw and final data is, and a schema for the dataset.

This schema will consist of datasets. Each schema will have a source (earthacces, Earth Engine, or on custom/on disk) and a function that gets the data from that source. The idea is you only have to define how to get data once, then you can just add it to the schema when needed. These will be broadly grouped into the categories of earthacces, earthengine, and custom as each will need some special processing and authentication code. 

There is one special dataset in the schema, which is the index dataset. This is how we define what locations and times to get from our other dataset. In the case of WildfireSpreadTS this is globfire, which gives us the start and end of the fire and the location it started at so that we can build tiffs at that location for every day of the fire. 

Broadly I think the pipeline should first get the index dataset, then get tiffs from earthengine, then add the earthaccess datasets, then add the custom data. We wont really worry about caching for now, and i think each step of the pipeline should be run indepenendtly. 