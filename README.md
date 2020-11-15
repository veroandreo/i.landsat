# Description

This repo holds a **work-in-progress** toolset to search and 
download Landsat 5, 7 and 8 data from 
[EarthExplorer](https://earthexplorer.usgs.gov/) and further 
import them into [GRASS GIS](https://grass.osgeo.org/). 
Search and download are carried out through the
[landsatxplore](https://github.com/yannforget/landsatxplore) 
python library.

Following the logic of other addons, it will contain two 
modules: 
- *i.landsat.download*: to search, filter and download scenes
- *i.landsat.import*: to import the downloaded scenes into GRASS GIS database.