# GeoProject Format

This document describes a quick and dirty format for a GeoProject to be displayed on MapLibre. The format is subject to future refinement.

## Structure

A GeoProject is defined as a JSON object with the following fields:

- **name**
- **desc**
- **basemap**
- **view**
- **layers**

### Name and Description

- **name** (required): A text name for the project.
- **desc** (optional): A description of the project.

### Basemap

```json
"basemap": {
  "style": "https://api.maptiler.com/maps/streets/style.json"
}
```

- **style**: A URL to the MapLibre style.

### View

The view holds the initial view. It can be defined using either a center/zoom or bounds format. **Choose one option.**

- **Center/Zoom Format**

    ```json
    "view": {
        "center": [-73.935242, 40.730610],
        "zoom": 10
    }
    ```

    - **center**: An array with `[longitude, latitude]`.
    - **zoom**: A numeric zoom level.

- **Bounds Format**

    ```json
    "view": {
        "bounds": [[minLng, minLat], [maxLng, maxLat]]
    }
    ```

    - **bounds**: An array with two coordinate arrays defining the southwest and northeast corners.

### Layers

Layers are specified as an array of layer objects. For now, keep the structure as shown below.

```json
"layers": [
  {
    "name": "myGeoSource",
    "desc": "Optional description",
    "data": {
      "data_type": "geojson",
      "ref_type": "url",
      "ref": "http://localhost:8000/geoprojects/sample1.geojson"
    },
    "visible": true,
    "style": [
      {
        "type": "fill",
        "paint": {
          "fill-color": "#1f78b4",
          "fill-opacity": 0.5
        }
      }
    ]
  }
]
```

#### Layer Object Details

- **name** (required): A text identifier for the layer.
- **desc** (optional): A description of the layer.
- **data**: A JSON object that specifies the source of the data.
    - **data_type**: Currently only "geojson" is supported.
    - **ref_type**: Can be "url" or "geodonis_file".  
        - For "url", the "ref" field should hold a url.
        - For "geodonis_file", the "ref" field should hold a uploaded file path.
- **visible**: Boolean flag indicating whether the layer is visible.
- **style**: An array of style objects in MapLibre format.  

## Software Implementation Notes

1. For the style url, we will check the url base to see if we should append a api key. We will just support map tiler for now.
2. If both view center and region are included, select the region (preferred mechanism)

## Database Storage

- (other required fields: id, user, etc)
- **name**: string
- **description**: string (null ok)
- **basemap**: store as a string field, holding the style URL.
- **view**: hold as a json
- **layers**: hold in a layers table
    - (id reference)
    - **order**: int
    - **name**: string
    - **description**: string (null ok)
    - **data**: json
    - **visible**: boolean
    - **style**: json
