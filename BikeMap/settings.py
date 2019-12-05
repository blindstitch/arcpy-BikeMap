# Defaults & static data

from arcpy import SpatialReference

defaults = {
    'api_request_time_interval' : 60000,
    'profile_chunk_size' : 1000
}

ref = 4326 # WGS-84
ref_arc = SpatialReference(ref)

endpoints = {
    'routing' : 'https://utility.arcgis.com/usrsvcs/appservices/{}/rest/services/World/Route/NAServer/Route_World/solve',
    'profile' : 'https://utility.arcgis.com/usrsvcs/appservices/{}/rest/services/Tools/Elevation/GPServer/Profile/submitJob',
    'summarize_elevation' : 'https://utility.arcgis.com/usrsvcs/appservices/{}/rest/services/Tools/Elevation/GPServer/SummarizeElevation/submitJob'
}

urls = {
    'token' : 'https://www.arcgis.com/sharing/rest/oauth2/token',
    'route' : 'https://route.arcgis.com/arcgis/rest/services/World/Route/NAServer/Route_World/solve'
}

token_request_header = {
    'content-type': "application/x-www-form-urlencoded",
    'accept': "application/json",
    'cache-control': "no-cache"
}