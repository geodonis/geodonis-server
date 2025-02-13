# Remote GIS 2/12/25

Remote GIS is an idea for a GIS editor like QGIS that works with a remote data source. The main idea is that the user would render the data set locally through vector tiles constructed on the family in the back end. We would have a smallest scale of tile which includes the full detail of the data. We would then also have larger scale tiles which would have reduced resolution. The client would request the necessary tiles as you view and traverse the map. If you tried to edit any of the features you would have to be viewing the smallest scale of tile. This would have to be enforced on the client. The main idea is that you don't have to download the huge data set to your system you can just view the parts you need to view as you work. When you do want to edit the editing would be done on the server with the remote data being edited.

A conversation with Claude is given below:

NOTES:

- There are a couple of Web GIS platforms, in addition to ArcGIS Online
    - ArcGIS ONline is getting more functionality
    - Two other clients: GeoNode and NextGIS Web: Both of these do not solve the large dataset problem I discussed. They work with the entire dataset locally.
- I brought up the idea of integrating the remote dataset into QGIS. Claude gave some thoughts on how this would fit into the architecture.


===============

I've been working with ArcGIS Pro from ESRI and I've done a little work with QGIS. One of the big pains in working with these is that the data sets are so large. It is kind of a pain to download them to my computer. It'd be nice to work with the data sets remotely. Of course, the fact that they're so large also makes it hard to work with them remotely.

I thought about an idea for doing this. We could have a client like a web client for example. We'd also have a backend which would contain the processing functionality of like QGIS. The backend would also have a vector tile server that could make on the fly tiles to send to the client. The tiles would be at a reduced resolution if we're "zoomed out" and it would contain the full data resolution for the smallest scale of tiles. The client would plot these vector tiles, only requesting the tiles it needs for the current display. This would prevent it from downloading huge amounts of data. As a bonus, it would prevent it from trying to render huge amounts of data too.

If we're doing any editing of the data, such as modifying the geometry of feature, we would have to be working with the full resolution tiles. Part of the application logic would ensure that we were doing that. Likewise the back end would have the task of determining the different scales of vector tile data along with the associated resolution of the data in those tiles.

All rendering rules would be done on the client side. We also would have all functionality exposed on the client side. The difference from the normal GIS clients I mentioned is that the rendering would be done using these vector tiles created as needed on the fly, to limit the data exchange between the server and the client.

First, is there anything like a full featured web client GIS tool? I know about ArcGIS online, but I believe this has substantially reduced functionality as compared to ArcGIS Pro. Correct me if I'm wrong on that.

Second, do you think this sounds like it could be workable approach?

Third do you think there is any market for this type of tool? Do the best you can answering this one.

=========================

Let me address your questions one by one:

1. Regarding full-featured web GIS tools:
- ArcGIS Online has indeed historically had reduced functionality compared to ArcGIS Pro, though the gap has been narrowing
- MapBox GL JS provides sophisticated web mapping capabilities with vector tiles, but it's more of a development framework than a full GIS tool
- GeoNode is an open-source web-based GIS platform that offers some advanced functionality
- NextGIS Web is another web-based GIS platform with reasonable capabilities
However, none of these truly match the full feature set of desktop GIS applications like QGIS or ArcGIS Pro.

2. On the technical feasibility of your approach:
Your proposed architecture sounds quite viable. The key components you've outlined make sense:
- Vector tile server generating tiles on-the-fly at appropriate resolutions
- Client-side rendering with dynamic tile loading
- Full-resolution data access for editing
- Server-side processing for heavy computational tasks

A few technical considerations to keep in mind:
- The vector tile generation process would need to be highly optimized to generate tiles on-the-fly at acceptable speeds
- You'd need a smart caching strategy for commonly requested tiles
- The transition between different resolution levels would need careful handling to maintain visual consistency
- You might want to consider using WebAssembly for some client-side processing to improve performance

3. Regarding market potential:
There are several indicators that suggest there could be a market for this:
- Many organizations are moving toward web-based tools for better accessibility and easier deployment
- There's growing need for collaborative GIS work, which web-based solutions facilitate better than desktop applications
- The pain points you've identified (data size, remote access) are common across the industry
- Small to medium organizations often find current enterprise GIS solutions prohibitively expensive

The main competition would be:
- ESRI's enterprise solutions
- Open-source alternatives
- Custom solutions built by large organizations

Your approach could potentially find a sweet spot between full enterprise solutions and simpler web mapping tools, especially if you focus on specific industry verticals or use cases where the current solutions are inadequate.

Would you be interested in exploring any particular aspect of this architecture in more detail? I could help sketch out some of the technical components or discuss specific implementation challenges.

==========================

I'd like to hear more about Geonode and NextGIS. Tell me what functionality they have and what they're missing. Contrast both of these services with the service I suggested.

============================

Let me break down both GeoNode and NextGIS Web, and compare them to your proposed solution:

GeoNode:
- Core Functionality:
  - Data upload and management for vector and raster data
  - Basic map creation and styling
  - User management and permissions
  - Metadata management and cataloging
  - Basic spatial analysis tools
  - OGC services support (WMS, WFS, WCS)
  - REST API for integration

- Key Limitations:
  - Limited advanced analysis capabilities compared to desktop GIS
  - Basic styling options compared to QGIS/ArcGIS Pro
  - No real-time vector tile generation
  - Limited editing capabilities for geometries
  - Performance can be an issue with large datasets
  - No advanced topology editing

NextGIS Web:
- Core Functionality:
  - Web mapping interface
  - Vector and raster data management
  - User management and access control
  - Basic styling capabilities
  - Integration with QGIS via plugins
  - Mobile data collection support
  - Support for various spatial data formats

- Key Limitations:
  - Limited advanced spatial analysis
  - Basic editing capabilities
  - No dynamic vector tile generation
  - Limited customization options
  - Performance issues with large datasets
  - Dependency on their ecosystem for full functionality

Comparing to Your Proposed Solution:
Your approach differs in several key ways:

1. Data Handling:
- Your solution: Dynamic vector tile generation with resolution optimization
- GeoNode/NextGIS: Traditional tile caching and full dataset loading

2. Performance:
- Your solution: Better handling of large datasets through intelligent tiling
- GeoNode/NextGIS: Can struggle with large datasets

3. Editing Capabilities:
- Your solution: Full-resolution editing with smart data loading
- GeoNode/NextGIS: Basic editing capabilities with full dataset loading

4. Architecture:
- Your solution: Modern client-server architecture with focus on optimized data transfer
- GeoNode/NextGIS: More traditional web GIS architecture

5. Scalability:
- Your solution: Better potential for scaling with large datasets
- GeoNode/NextGIS: Can face scaling challenges

The main advantage of your proposed solution is its focus on handling large datasets efficiently through dynamic vector tiling and smart data loading. Neither GeoNode nor NextGIS Web currently offers this level of sophisticated data handling. Your approach would be particularly valuable for organizations working with large, frequently updated spatial datasets that need both visualization and editing capabilities.

However, both GeoNode and NextGIS Web have mature ecosystems with features like:
- Established user management systems
- Integration with other GIS tools
- Metadata management
- OGC services support

These are areas you'd need to consider implementing in your solution to make it a viable alternative.

The key innovation in your proposal is the combination of dynamic vector tiling with full-featured GIS capabilities, which could potentially offer better performance and usability than either of these existing solutions, particularly for large dataset handling.

=============================

An alternate implementation of the application I was discussing would be to Implement the back end as I described and modify the qjis client so it can connect to this back end. It might even be possible to have it work with local data and remote data (though this would only make sense for small local data sets). Knowing what you know about qgis code, if anything, can you suggest at the high level what we would need to do for this.

One think I wonder about, is there any kind of modular architecture for a data set in qgis which includes the functionality edit the data set and the interface to render it? We would have to create the remote data set  module to go in this system.

=========================

Let me analyze this from what I know about QGIS's architecture:

QGIS does have a modular architecture for data handling through its provider system. The QgsDataProvider class is the base class for all data providers in QGIS, and it's designed to be extensible. Here's a high-level breakdown of what would be needed:

1. Data Provider Implementation:
- Create a new custom QgsDataProvider subclass for your remote data source
- Implement core functionality like:
  - Feature retrieval based on extent/zoom level
  - Feature editing capabilities
  - Geometry operations
  - Integration with the vector tile system
- Handle the connection to your backend server

2. Vector Layer Modifications:
- Extend QgsVectorLayer to work with your custom provider
- Implement caching mechanisms for vector tiles
- Handle resolution switching based on zoom levels
- Manage the transition between local and remote data modes

3. Provider Plugin Registration:
```cpp
class MyProviderGuiPlugin: public QgisGuiPlugin
{
  public:
    void initGui() {
      // Register the data provider
      QgsProviderRegistry::instance()->registerProvider(
        new MyProviderMetadata()
      );
    }
};
```

4. Data Source Management:
```cpp
class MyRemoteProvider: public QgsDataProvider
{
  public:
    // Handle vector tile requests
    QgsFeatureIterator getFeatures(const QgsFeatureRequest& request);
    
    // Implement editing capabilities
    bool addFeatures(QgsFeatureList& flist);
    bool deleteFeatures(const QgsFeatureIds& id);
    bool changeGeometryValues(const QgsGeometryMap& geometry_map);
    
    // Handle resolution management
    bool setDataSourceUri(const QString& uri);
};
```

The good news is that QGIS's architecture is designed for this kind of extensibility. The provider system was specifically created to allow different data sources to be plugged in.

Key challenges would include:
1. Managing the transition between different resolution levels
2. Implementing efficient caching for vector tiles
3. Handling edit operations with proper locking mechanisms
4. Maintaining performance with remote data
5. Synchronizing local and remote data states

Would you like me to elaborate on any of these aspects or explore a specific part of the implementation in more detail?