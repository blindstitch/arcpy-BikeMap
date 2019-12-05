elevation_request_params = {
  'f' : 'json',
  'token' : '',
  'returnZ' : 'true',
  'DEMResolution' : 'FINEST',
  'ProfileIDField' : 'ObjectID',
  'InputLineFeatures' : {
    "geometryType":"esriGeometryPolyline",
    "spatialReference":{
      "wkid": 4326
    },
    "fields":[
      {
        "name": "ObjectId",
        "alias": "ObjectId",
        "type": "esriFieldTypeOID"
      },
      {
        "name": "Name",
        "alias": "Name",
        "type": "esriFieldTypeString"
      }
    ],
    "features":[
      {
        "attributes":{
          "ObjectID":1,
          "Name":"SomeRoute"
        },
        "geometry":{
          "paths":[
              # Fill me with point coordinates as a list of lists
            'foo'
          ]
        }
      }
    ]
  }
}