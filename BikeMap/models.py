from utils import *

import settings

class Points:

    def __init__(self,points_list,mode='lonlat'):
        from arcpy import Array as _Array
        from arcpy import Point as _Point
        from arcpy import Polyline as _Polyline
        # Data validation
        if not isinstance(points_list,list):
            raise ValueError('RoutePoints object requires lists') # Type hinting would be nice, but this is not Python 3
        # Some / all of these could be replaced with getters to avoid unnecessary comprehensions.
        if len(points_list) > 1:
            self.points = [self.validate_point(point,mode=mode) for point in points_list]
            self.start = points_list[0]
            self.end = points_list[-1]
            self.midpoints = None
            if len(points_list) > 2:
                self.midpoints = points_list[1:-1]
            self.points_lonlat = self.points
            self.points_latlon = [p[::-1] for p in self.points] # This is the type that google wants
            self.points_arc_array = _Array([ # Arcpy takes x,y ie lon,lat
                _Point(point[0],point[1]) for point in self.points_lonlat
            ])
            self.arc_polyline = _Polyline(self.points_arc_array,settings.ref_arc)
        else:
            raise ValueError('Bad number of points ({} provided).'.format(len(points_list)))

    def validate_point(self, point, mode='lonlat'):
        if (isinstance(point, tuple) or isinstance(point,list)) & (len(point) == 2):
            if mode == 'lonlat':
                cond = (isinstance(point, tuple) or isinstance(point,list)) & (len(point) == 2) & (abs(point[0]) <= 180) & (abs(point[1]) <= 90)
            elif mode == 'latlon':
                cond = (isinstance(point, tuple) or isinstance(point,list)) & (len(point) == 2) & (abs(point[0]) <= 90) & (abs(point[1]) <= 180)
            else:
                raise ValueError('Unknown mode')
        else:
            raise ValueError('Points are the wrong type - expecting tuples or lists of length 2 each')
        if cond:
            return point
        else:
            raise ValueError(
                'Points are invalid, possible mode mismatch. Passed point: {}, mode is {}'.format(point, mode))

    def setBreakpoints(self,breaks):
        self.breakpoints = breaks

    def setMapsegmentExtents(self,extents_list):
        # Expects a list of lists - [ [[x,y],[x,y]], [[x2,y2],[x3,y3]] ... ]
        self.mapsegment_extents = extents_list