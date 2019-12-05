from BikeMap import BikeMap
from BikeMap.utils import *
from secrets import api_credentials # Make it harder for keys to end up in version control

# Destinations
amarillo = (-101.8313,35.2220)
grand_junction = (-108.5506,39.0639)
santa_fe = (-105.9590,35.6838)
co_springs = (-104.8214,38.8339)

bikemap = BikeMap(creds=api_credentials,
                  name='grand_junction_to_amarillo')

bikemap.set_dirs(workdir='./scratch',
                 outdir='./out')

bikemap.set_route_dests([grand_junction, amarillo])
bikemap.get_api_data() # Small test chunk size to make the list separaiton obvious
# Print the bikemap.token property to use values in API testers

bikemap.output_map( # this is where the MapInterface object is used within BikeMap
    './assets/bikemapTemplate.mxd',
    break_human='60 miles',
    extents_pad_degrees=.05,
    standalone=True)