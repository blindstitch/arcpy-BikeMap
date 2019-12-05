import settings
from models import *
from utils import *
import request_templates
from json import loads
from requests import request, get
from time import sleep
import arcpy
import pythonaddins # Rectangle drawing
import os
import math
import shutil

class BikeMap:

    # Defaults, instantiation variables
    def __init__(self,creds,name,mode='arcpy'):

        self.engine = mode
        self.name = clean(name)
        self.creds = creds # TODO validate credentials are complete
        self.route_dict = None
        self.route_line = None
        self.routepts = None
        self.elevation_profile = None # API will make this a polyline feature with an elevation attached
        self.api_req_interval_default = settings.defaults['api_request_time_interval'] # Don't set manually - it's in settings.py # todo remove this

        if mode == 'arcpy':
            arcpy.env.overwriteOutput = True


    def set_dirs(self, workdir, outdir):
        self.workdir = workdir
        self.outdir = outdir

    # Setter for the input points
    def set_route_dests(self, dest_list):
        self.routepts = Points(dest_list)


    # Return the API token for this request
    def authenticate(self):

        # TODO Reference for paper: https://developers.arcgis.com/rest/analysis/api-reference/programmatically-accessing-analysis-services.htm

        try:
            client_id = self.creds['keys']['client_id']
            client_secret = self.creds['keys']['client_secret']
        except:
            raise Exception('There are missing API keys and your request could not be authenticated.')

        url = settings.urls['token']

        #         payload = "client_id={}&client_secret={}&grant_type=client_credentials".format(client_id, client_secret)
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
        }
        payload = flatten_dict_for_api_request(payload)

        response = request("POST", url, data=payload, headers=settings.token_request_header)
        token = loads(response.text)['access_token']

        return token


    # Populate the self.routepts variable
    def get_arcgis_api_route(self, token):

        print('Getting route data from API...')  # TODO implement with the PrintMessage wrapper used from lab 11

        # Documentation: https://developers.arcgis.com/rest/network/api-reference/route-synchronous-service.htm
        #  https://route.arcgis.com/arcgis/rest/services/World/Route/NAServer/Route_World/solve?<PARAMETERS>
        # Currently, this method gets the token every single time. It doesn't slow it down as far as I can tell

        start = ",".join(map(str, self.routepts.start))  # This is how the join string method works for tuples of floats
        end = ','.join(map(str, self.routepts.end))

        api_request_points = ';'.join(','.join([str(a) for a in list(p)]) for p in self.routepts.points)

        request_dict = {
            'f': 'json',
            'returnDirections': 'false',
            'token': token,
            'stops': api_request_points
        }
        response = get(settings.urls['route'], params=request_dict)

        if response:
            self.route_dict = loads(response.content)
            self.route_line = self.route_dict['routes']['features'][0]['geometry']['paths'][0]  # The paths are probably nested like this for a reason
            # TODO convert to polyline
            self.route_line_obj = Points(self.route_line,mode='lonlat')
        else:
            raise RuntimeError('Query to Arcgis Routing API failed: {}'.format(response.text))


    # Populate the elevation_profile and route_line variables
    # This could go up apparently?
    def get_api_data(self,
                     time_interval=settings.defaults['api_request_time_interval'],
                     chunksize=settings.defaults['profile_chunk_size']
                     ):

        # TODO use a try/except here with this exception
        # raise RuntimeError('There are 1 or more empty API keys. Unpopulated keys: {}'.format(missing_keys)) # TODO reimpliment exception for missing keys

        self.token = self.authenticate() # Store the API token for this session
        self.get_arcgis_api_route(self.token) # Get the route data, populate self.route_line
        # self.get_arcgis_api_elevation(self.token, time_interval, chunksize) # Populate self.elevation_profile


    def create_breakpoints(self, segment_distance, segment_unit):
        polyline = self.route_line_obj.arc_polyline
        line_length = polyline.getLength('PRESERVE_SHAPE',segment_unit)
        # Breaks are produced using percentages (distances are in degrees and don't work great)
        breaks = [self.routepts.start]
        for i in range(1,1+int(math.ceil(line_length/segment_distance))):
            pct = i*segment_distance/line_length
            distance_point = polyline.positionAlongLine(pct,True).centroid
            breaks.append([distance_point.X,distance_point.Y])

        self.routepts.breaks = breaks

    def create_map_extents(self, pad):

        # Create new extents
        extents = []
        for i in range(len(self.routepts.breaks)-1):
            ext = self.routepts.breaks[i:i + 2]

            # Create a new extents pair that has an UL/LR format - change to [[Xmin,Ymax],[Xmax,Ymin]]
            # Think this should work, except maybe if you're trying to make a map across the north pole
            ext = [
                [ min(ext[0][0],ext[1][0]), max(ext[0][1],ext[1][1]) ],
                [ max(ext[0][0],ext[1][0]), min(ext[0][1],ext[1][1]) ]
            ]

            # Make ratio 1:1 # TODO add param
            if abs(ext[0][0] - ext[1][0]) > abs(ext[0][1] - ext[1][1]):
                largest_dim = 0 # x is larger
            else:
                largest_dim = 1 # y is larger

            smallest_dim = 1 if largest_dim == 0 else 0

            largest_dim_degrees = ext[0][largest_dim] - ext[1][largest_dim]

            # Resize the extents window
            small_dim_midpoint = (ext[0][smallest_dim]+ext[1][smallest_dim])/2
            if smallest_dim == 0:
                ext[0][0] = small_dim_midpoint - largest_dim_degrees/2
                ext[1][0] = small_dim_midpoint + largest_dim_degrees/2
            else:
                ext[0][1] = small_dim_midpoint + largest_dim_degrees/2
                ext[1][1] = small_dim_midpoint - largest_dim_degrees/2

            extents.append(ext)

        # Store to the routepoints object
        # This should use the setter that was created
        self.routepts.seg_extents = extents

        self.extents_poly_points = []
        for ext in self.routepts.seg_extents:
            self.extents_poly_points.append([
                [ext[0][0] - pad, ext[0][1] + pad],
                [ext[1][0] + pad, ext[0][1] + pad],
                [ext[1][0] + pad, ext[1][1] - pad],
                [ext[0][0] - pad, ext[1][1] - pad]
            ])

    def create_route_fc(self):
        self.route_fc_path = '{}/{}_route.shp'.format(self.workdir, self.name)
        self.route_fc_name = self.name + '_route'

        result = arcpy.CreateFeatureclass_management(
            self.workdir,
            self.route_fc_name,
            geometry_type = 'Polyline',
            spatial_reference = settings.ref,
        )
        feature_class = result[0]

        with arcpy.da.InsertCursor(self.route_fc_path, ['SHAPE@']) as cursor:
            cursor.insertRow([self.route_line_obj.arc_polyline])

    def create_extents_fc(self): # TODO Put this somewhere better
        # Create polys for the extents for use in a data-driven ArcMap document.
        # These go clockwise from UL to LL, using the bounds pairs.
        arcpy.env.overwriteOutput = True

        self.extents_fc_path = '{}/{}_extents.shp'.format(self.workdir, self.name)
        self.extents_fc_name = self.name + '_extents'

        result = arcpy.CreateFeatureclass_management(
            self.workdir,
            self.extents_fc_name,
            geometry_type = 'Polygon',
            spatial_reference = 4326,
        )
        feature_class = result[0]

        with arcpy.da.InsertCursor(self.extents_fc_path, ['SHAPE@']) as cursor:
            for extent_points in self.extents_poly_points:
                cursor.insertRow([
                    arcpy.Polygon(
                        arcpy.Array([arcpy.Point(point[0], point[1]) for point in extent_points]),
                        settings.ref_arc
                    )
                ])

    def create_breakpoints_fc(self):
        self.breakpoints_fc_path = '{}/{}_breakpoints.shp'.format(self.workdir, self.name) # unnecessary?
        self.breakpoints_fc_name = self.name + '_breakpoints'

        result = arcpy.CreateFeatureclass_management(
            self.workdir,
            self.breakpoints_fc_name,
            geometry_type='Point',
            spatial_reference=4326,
        )
        feature_class = result[0]

        with arcpy.da.InsertCursor(self.breakpoints_fc_path, ['SHAPE@']) as cursor:
            for point in self.routepts.breaks:
                cursor.insertRow([
                    arcpy.Point(point[0], point[1])
                ])

    def output_map(self,
                   template,
                   break_human,
                   extents_pad_degrees,
                   standalone=True):

        pdf_outpath = self.outdir + '/' + self.name + 'pdf'

        # To make switching out this code possible later
        if self.engine == 'arcpy':
            self.create_route_fc()

            dist = float(break_human.split(' ')[0])
            unit = break_human.split(' ')[1]
            self.create_breakpoints(dist,unit)

            self.create_map_extents(pad=extents_pad_degrees)
            self.create_extents_fc()
            self.create_breakpoints_fc()

            # map.replace_index_layer()
            if standalone == True:
                outpath = '{}/BikeMap_{}.mxd'.format(self.outdir, self.name)
                shutil.copy(template,outpath) # SaveACopy would not work, - 'AttributeError: Unable to save' - no doc online
                mxd = arcpy.mapping.MapDocument(outpath) # This is the copied MXD file
                # print arcpy.mapping.ListDataFrames(mxd)
                # mxd.saveACopy(outpath)

                df = arcpy.mapping.ListDataFrames(mxd,'BikeMap')[0]

                getLayer = lambda mxd,df,name: arcpy.mapping.ListLayers(mxd,name,df)[0]

                # Don't rename anything in the MXD
                breaks_layer = getLayer(mxd,df,'breakpoints')
                extents_layer = getLayer(mxd,df,'extents')
                route_layer = getLayer(mxd,df,'route')

                # TODO write a util that returns an abspath, or provide an abspath to the project
                breaks_layer.replaceDataSource(
                    r"C:\Users\karl\Desktop\527\bikemap\scratch",
                    "SHAPEFILE_WORKSPACE",
                    self.breakpoints_fc_name)
                extents_layer.replaceDataSource(
                    r"C:\Users\karl\Desktop\527\bikemap\scratch",
                    "SHAPEFILE_WORKSPACE",
                    self.extents_fc_name)
                route_layer.replaceDataSource(
                    r"C:\Users\karl\Desktop\527\bikemap\scratch",
                    "SHAPEFILE_WORKSPACE",
                    self.route_fc_name)

                mxd.dataDrivenPages.refresh() # Update the page count after replacing Index layer
                mxd.dataDrivenPages.exportToPDF(
                    "C:/Users/karl/Desktop/527/bikemap/out/BikeMap_" + self.name + '.pdf',
                    'ALL'
                )

                mxd.save()

        else:
            raise NotImplementedError('Only arcpy mode is supported at this time.')