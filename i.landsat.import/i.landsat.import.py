#!/usr/bin/env python
#-*- coding: utf-8 -*-
############################################################################
#
# MODULE:      i.landsat.import
# AUTHOR(S):   Veronica Andreo
# PURPOSE:     Imports Landsat data downloaded from EarthExplorer using
#              i.landsat.download.
# COPYRIGHT:   (C) 2020-2021 by Veronica Andreo, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#% description: Imports Landsat satellite data downloaded from EarthExplorer using i.landsat.download.
#% keyword: imagery
#% keyword: satellite
#% keyword: Landsat
#% keyword: import
#%end
#%option G_OPT_M_DIR
#% key: input
#% description: Name of input directory with downloaded Landsat data
#% required: yes
#%end
#%option G_OPT_M_DIR
#% key: unzip_dir
#% description: Name of directory into which Landsat zip-files are extracted (default=input)
#% required: no
#%end
#%option
#% key: pattern
#% description: Band name pattern to import
#% guisection: Filter
#%end
#%option
#% key: pattern_file
#% description: File name pattern to import
#% guisection: Filter
#%end
#%option
#% key: extent
#% type: string
#% required: no
#% multiple: no
#% options: input,region
#% answer: input
#% description: Output raster map extent
#% descriptions: region;extent of current region;input;extent of input map
#% guisection: Filter
#%end
#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end
#%flag
#% key: r
#% description: Reproject raster data using r.import if needed
#% guisection: Settings
#%end
#%flag
#% key: o
#% description: Override projection check (use current location's projection)
#% guisection: Settings
#%end
#% key: n
#% description: Do not unzip if files are already extracted
#% guisection: Settings
#%end
#%flag
#% key: p
#% description: Print raster data to be imported and exit
#% guisection: Print
#%end

import os
import sys
import glob
import re
import shutil
import grass.script as gs
from grass.exceptions import CalledModuleError

class LandsatImporter(object):

    def __init__(self, input_dir, unzip_dir):
        # list of directories to cleanup
        self._dir_list = []

        # check if input dir exists
        self.input_dir = input_dir
        if not os.path.exists(input_dir):
            gs.fatal(_('Input directory <{}> does not exist').format(input_dir))

        # check if unzip dir exists
        if unzip_dir is None or unzip_dir == '':
            unzip_dir = input_dir

        self.unzip_dir = unzip_dir
        if not os.path.exists(unzip_dir):
            gs.fatal(_('Directory <{}> does not exist').format(unzip_dir))

    def __del__(self):
        if flags['l']:
            # unzipped files are required when linking
            return

        # otherwise unzipped directory can be removed (?)
        for dirname in self._dir_list:
            dirpath = os.path.join(self.unzip_dir, dirname)
            gs.debug('Removing <{}>'.format(dirpath))
            try:
                shutil.rmtree(dirpath)
            except OSError:
                pass

    def filter(self, pattern=None):
        if pattern:
            filter_p = r'.*{}.*.tif$'.format(pattern)
        else:
            filter_p = r'.*_B.*.tif$'

        gs.debug('Filter: {}'.format(filter_p), 1)
        self.files = self._filter(filter_p, force_unzip=not flags['n'])

    def _unzip(self, force=False):
        # extract all zip files from input directory
        if options['pattern_file']:
            filter_f = '*' + options['pattern_file'] + '*.tar.gz'
        else:
            filter_f = '*.tar.gz'

        input_files = glob.glob(os.path.join(self.input_dir, filter_f))

        for filepath in input_files:
            shutil.unpack_archive(filepath, self.unzip_dir)

    def _filter(self, filter_p, force_unzip=False):
        # unzip archives before filtering
        self._unzip(force=force_unzip)

        if options['pattern_file']:
            filter_f = '*' + options['pattern_file'] + '*'
        else:
            filter_f = '*'

        pattern = re.compile(filter_p)
        files = []
        scenes = glob.glob(os.path.join(self.unzip_dir, filter_f))
        if len(scenes) < 1:
            gs.fatal(_('Nothing found to import. Please check input and pattern_file options.'))

        for scene in scenes:
            for rec in os.walk(scene):
                if not rec[-1]:
                    continue

                match = filter(pattern.match, rec[-1])
                if match is None:
                    continue

                for f in match:
                    files.append(os.path.join(rec[0], f))

        return files

    def import_products(self, reproject=False, link=False, override=False):
        args = {}
        if link:
            module = 'r.external'
            args['flags'] = 'o' if override else None
        else:
            args['memory'] = options['memory']
            if reproject:
                module = 'r.import'
                args['resample'] = 'bilinear'
                args['resolution'] = 'value'
                args['extent'] = options['extent']
            else:
                module = 'r.in.gdal'
                args['flags'] = 'o' if override else None
                if options['extent'] == 'region':
                    if args['flags']:
                        args['flags'] += 'r'
                    else:
                        args['flags'] = 'r'

        for f in self.files:
            if not override and (link or (not link and not reproject)):
                if not self._check_projection(f):
                    gs.fatal(_('Projection of dataset does not appear to match current location. '
                               'Force reprojection using -r flag.'))

            self._import_file(f, module, args)

    def _check_projection(self, filename):
        try:
            with open(os.devnull) as null:
                gs.run_command('r.in.gdal', flags='j',
                               input=filename, quiet=True, stderr=null)
        except CalledModuleError as e:
            return False

        return True

    def _raster_resolution(self, filename):
        try:
            from osgeo import gdal
        except ImportError as e:
            gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
        dsn = gdal.Open(filename)
        trans = dsn.GetGeoTransform()

        ret = int(trans[1])
        dsn = None

        return ret

    def _raster_epsg(self, filename):
        try:
            from osgeo import gdal, osr
        except ImportError as e:
            gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
        dsn = gdal.Open(filename)

        srs = osr.SpatialReference()
        srs.ImportFromWkt(dsn.GetProjectionRef())

        ret = srs.GetAuthorityCode(None)
        dsn = None

        return ret

    @staticmethod
    def _map_name(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def _import_file(self, filename, module, args):
        mapname = self._map_name(filename)
        gs.message(_('Processing <{}>...').format(mapname))
        if module == 'r.import':
            args['resolution_value'] = self._raster_resolution(filename)
        try:
            gs.run_command(module, input=filename, output=mapname, **args)
            if gs.raster_info(mapname)['datatype'] in ('FCELL', 'DCELL'):
                gs.message('Rounding to integer after reprojection')
                gs.use_temp_region()
                gs.run_command('g.region', raster=mapname)
                gs.run_command('r.mapcalc', quiet=True, expression='tmp_%s = round(%s)' % (mapname, mapname))
                gs.run_command('g.rename', quiet=True, overwrite=True, raster='tmp_%s,%s' % (mapname, mapname))
                gs.del_temp_region()
            gs.raster_history(mapname)
        except CalledModuleError as e:
            pass # error already printed

    def print_products(self):
        for f in self.files:
            sys.stdout.write('{} {} (EPSG: {}){}'.format(
                f,
                '1' if self._check_projection(f) else '0',
                self._raster_epsg(f),
                os.linesep
            ))

def main():

    importer = LandsatImporter(options['input'], options['unzip_dir'])

    importer.filter(options['pattern'])
    if len(importer.files) < 1:
        gs.fatal(_('Nothing found to import. Please check input and pattern options.'))

    if flags['p']:
        importer.print_products()
        return 0

    importer.import_products(flags['r'], flags['l'], flags['o'])

    return 0

if __name__ == '__main__':
    options, flags = gs.parser()
    main()
