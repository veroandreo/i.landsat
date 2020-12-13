# Description

This repo holds a toolset to search and download Landsat 5, 7 and 8 
data from [EarthExplorer](https://earthexplorer.usgs.gov/) and further 
import them into [GRASS GIS](https://grass.osgeo.org/). 
Search and download are carried out through the
[landsatxplore](https://github.com/yannforget/landsatxplore) 
python library.

Following the logic of other similar add-ons, this toolset contains two 
modules: 
- *i.landsat.download*: to search, filter and download scenes
- *i.landsat.import*: to import the downloaded scenes into GRASS GIS database

## Install the toolset

To add *i.landsat* to your GRASS GIS installation, use 
[g.extension](https://grass.osgeo.org/grass-stable/manuals/g.extension.html):

```
g.extension extension=i.landsat url='https://github.com/veroandreo/i.landsat'
``` 

## Use examples

#### Search 

```shell script
# search available scenes
i.landsat.download -l settings=credentials.txt dataset=LANDSAT_8_C1 clouds=15 start='2018-08-24' end='2018-12-21'
```

#### Download

```shell script
# download all available scenes 
# (if no output dir is provided, data will be downloaded in /tmp)
i.landsat.download settings=credentials.txt dataset=LANDSAT_8_C1 clouds=15 start='2018-08-24' end='2018-12-21'

# download by scene ID
i.landsat.download settings=credentials.txt id=LC81391162018338LGN00 output=landsat_data
```

#### Import

```shell script
# print all landsat bands to import within the landsat_data folder
i.landsat.import -p input=landsat_data

# import only bands 4 and 5 for path 229 and row 083 in 2019
i.landsat.import input=landsat_data pattern_file='229083_2019' pattern='B(4|5)'
```

## TODO

- See [open issues](https://github.com/veroandreo/i.landsat/issues)