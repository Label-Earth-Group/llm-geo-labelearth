import os
import requests
import networkx as nx
import pandas as pd
import geopandas as gpd
from pyvis.network import Network
import openai
import LLM_Geo_Constants as constants
import helper
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import base64
import json
from pydantic import BaseModel
from LLM_Geo_kernel import Solution
from IPython.display import display, HTML, Code
from IPython.display import clear_output
from fastapi.middleware.cors import CORSMiddleware
isReview = True
app = FastAPI()

# 将配置挂在到app上
app.add_middleware(
    CORSMiddleware,
    # 这里配置允许跨域访问的前端地址
    allow_origins=["*"],
    # 跨域请求是否支持 cookie， 如果这里配置true，则allow_origins不能配置*
    allow_credentials=True,
    # 支持跨域的请求类型，可以单独配置get、post等，也可以直接使用通配符*表示支持所有
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    task_name: str
    task: str
    data_locations: list = []

@app.post("/stream_suite")
async def stream_suite(request_data: Item):
    def stream_content():

        # Stream text content
        text_content = r"""import networkx as nx

# Create a graph
G = nx.DiGraph()

# Load hazardous waste facility shapefile
G.add_node("haz_waste_shp_url", node_type="data", data_path="https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/HW_Sites_EPSG4326.zip", description="Hazardous waste facility shapefile URL")
G.add_node("load_haz_waste_shp", node_type="operation", description="Load hazardous waste facility shapefile")
G.add_node("haz_waste_gdf", node_type="data", description="Hazardous waste facility GeoDataFrame")

G.add_edge("haz_waste_shp_url", "load_haz_waste_shp")
G.add_edge("load_haz_waste_shp", "haz_waste_gdf")

# Load tract boundary shapefile
G.add_node("tract_boundary_shp_url", node_type="data", data_path="https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/tract_37_EPSG4326.zip", description="Tract boundary shapefile URL")
G.add_node("load_tract_boundary_shp", node_type="operation", description="Load tract boundary shapefile")
G.add_node("tract_boundary_gdf", node_type="data", description="Tract boundary GeoDataFrame")

G.add_edge("tract_boundary_shp_url", "load_tract_boundary_shp")
G.add_edge("load_tract_boundary_shp", "tract_boundary_gdf")

# Load tract population CSV file
G.add_node("tract_population_csv_url", node_type="data", data_path="https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/NC_tract_population.csv", description="Tract population CSV file URL")
G.add_node("load_tract_population_csv", node_type="operation", description="Load tract population CSV file")
G.add_node("tract_population_df", node_type="data", description="Tract population DataFrame")

G.add_edge("tract_population_csv_url", "load_tract_population_csv")
G.add_edge("load_tract_population_csv", "tract_population_df")

# Find Census tracts that contain hazardous waste facilities
G.add_node("haz_waste_tracts", node_type="operation", description="Find tracts containing hazardous waste facilities")
G.add_node("haz_waste_tracts_gdf", node_type="data", description="Tracts containing hazardous waste facilities GeoDataFrame")

G.add_edge("haz_waste_gdf", "haz_waste_tracts")
G.add_edge("tract_boundary_gdf", "haz_waste_tracts")
G.add_edge("haz_waste_tracts", "haz_waste_tracts_gdf")

# Compute population living in tracts with hazardous waste facilities
G.add_node("population_in_haz_waste_tracts", node_type="operation", description="Compute population in tracts with hazardous waste facilities")
G.add_node("population_in_haz_waste_tracts_value", node_type="data", description="Population living in tracts with hazardous waste facilities")

G.add_edge("haz_waste_tracts_gdf", "population_in_haz_waste_tracts")
G.add_edge("tract_population_df", "population_in_haz_waste_tracts")
G.add_edge("population_in_haz_waste_tracts", "population_in_haz_waste_tracts_value")

# Generate population choropleth map for all tract polygons in NC
G.add_node("population_choropleth_map", node_type="operation", description="Generate population choropleth map")
G.add_node("population_choropleth_map_image", node_type="data", description="Population choropleth map image")

G.add_edge("tract_boundary_gdf", "population_choropleth_map")
G.add_edge("tract_population_df", "population_choropleth_map")
G.add_edge("population_choropleth_map", "population_choropleth_map_image")

# Highlight the borders of tracts that have hazardous waste facilities on the map
G.add_node("highlighted_tracts_map", node_type="operation", description="Highlight the borders of tracts with hazardous waste facilities on the map")
G.add_node("highlighted_tracts_map_image", node_type="data", description="Highlighted tracts map image")

G.add_edge("population_choropleth_map_image", "highlighted_tracts_map")
G.add_edge("haz_waste_tracts_gdf", "highlighted_tracts_map")
G.add_edge("highlighted_tracts_map", "highlighted_tracts_map_image")

# Save the graph in GraphML format
nx.write_graphml(G, "C:/Users/Administrator/Downloads/LLM-Geo-master/test/test.graphml")
"""
        yield "event: message\ndata: " + json.dumps({"type": "text", "data": text_content}) + "\n\n"

        html_content = r"""<html>
    <head>
        <meta charset="utf-8">
        
            <script>function neighbourhoodHighlight(params) {
  // console.log("in nieghbourhoodhighlight");
  allNodes = nodes.get({ returnType: "Object" });
  // originalNodes = JSON.parse(JSON.stringify(allNodes));
  // if something is selected:
  if (params.nodes.length > 0) {
    highlightActive = true;
    var i, j;
    var selectedNode = params.nodes[0];
    var degrees = 2;

    // mark all nodes as hard to read.
    for (let nodeId in allNodes) {
      // nodeColors[nodeId] = allNodes[nodeId].color;
      allNodes[nodeId].color = "rgba(200,200,200,0.5)";
      if (allNodes[nodeId].hiddenLabel === undefined) {
        allNodes[nodeId].hiddenLabel = allNodes[nodeId].label;
        allNodes[nodeId].label = undefined;
      }
    }
    var connectedNodes = network.getConnectedNodes(selectedNode);
    var allConnectedNodes = [];

    // get the second degree nodes
    for (i = 1; i < degrees; i++) {
      for (j = 0; j < connectedNodes.length; j++) {
        allConnectedNodes = allConnectedNodes.concat(
          network.getConnectedNodes(connectedNodes[j])
        );
      }
    }

    // all second degree nodes get a different color and their label back
    for (i = 0; i < allConnectedNodes.length; i++) {
      // allNodes[allConnectedNodes[i]].color = "pink";
      allNodes[allConnectedNodes[i]].color = "rgba(150,150,150,0.75)";
      if (allNodes[allConnectedNodes[i]].hiddenLabel !== undefined) {
        allNodes[allConnectedNodes[i]].label =
          allNodes[allConnectedNodes[i]].hiddenLabel;
        allNodes[allConnectedNodes[i]].hiddenLabel = undefined;
      }
    }

    // all first degree nodes get their own color and their label back
    for (i = 0; i < connectedNodes.length; i++) {
      // allNodes[connectedNodes[i]].color = undefined;
      allNodes[connectedNodes[i]].color = nodeColors[connectedNodes[i]];
      if (allNodes[connectedNodes[i]].hiddenLabel !== undefined) {
        allNodes[connectedNodes[i]].label =
          allNodes[connectedNodes[i]].hiddenLabel;
        allNodes[connectedNodes[i]].hiddenLabel = undefined;
      }
    }

    // the main node gets its own color and its label back.
    // allNodes[selectedNode].color = undefined;
    allNodes[selectedNode].color = nodeColors[selectedNode];
    if (allNodes[selectedNode].hiddenLabel !== undefined) {
      allNodes[selectedNode].label = allNodes[selectedNode].hiddenLabel;
      allNodes[selectedNode].hiddenLabel = undefined;
    }
  } else if (highlightActive === true) {
    // console.log("highlightActive was true");
    // reset all nodes
    for (let nodeId in allNodes) {
      // allNodes[nodeId].color = "purple";
      allNodes[nodeId].color = nodeColors[nodeId];
      // delete allNodes[nodeId].color;
      if (allNodes[nodeId].hiddenLabel !== undefined) {
        allNodes[nodeId].label = allNodes[nodeId].hiddenLabel;
        allNodes[nodeId].hiddenLabel = undefined;
      }
    }
    highlightActive = false;
  }

  // transform the object into an array
  var updateArray = [];
  if (params.nodes.length > 0) {
    for (let nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        // console.log(allNodes[nodeId]);
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodes.update(updateArray);
  } else {
    // console.log("Nothing was selected");
    for (let nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        // console.log(allNodes[nodeId]);
        // allNodes[nodeId].color = {};
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodes.update(updateArray);
  }
}

function filterHighlight(params) {
  allNodes = nodes.get({ returnType: "Object" });
  // if something is selected:
  if (params.nodes.length > 0) {
    filterActive = true;
    let selectedNodes = params.nodes;

    // hiding all nodes and saving the label
    for (let nodeId in allNodes) {
      allNodes[nodeId].hidden = true;
      if (allNodes[nodeId].savedLabel === undefined) {
        allNodes[nodeId].savedLabel = allNodes[nodeId].label;
        allNodes[nodeId].label = undefined;
      }
    }

    for (let i=0; i < selectedNodes.length; i++) {
      allNodes[selectedNodes[i]].hidden = false;
      if (allNodes[selectedNodes[i]].savedLabel !== undefined) {
        allNodes[selectedNodes[i]].label = allNodes[selectedNodes[i]].savedLabel;
        allNodes[selectedNodes[i]].savedLabel = undefined;
      }
    }

  } else if (filterActive === true) {
    // reset all nodes
    for (let nodeId in allNodes) {
      allNodes[nodeId].hidden = false;
      if (allNodes[nodeId].savedLabel !== undefined) {
        allNodes[nodeId].label = allNodes[nodeId].savedLabel;
        allNodes[nodeId].savedLabel = undefined;
      }
    }
    filterActive = false;
  }

  // transform the object into an array
  var updateArray = [];
  if (params.nodes.length > 0) {
    for (let nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodes.update(updateArray);
  } else {
    for (let nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodes.update(updateArray);
  }
}

function selectNode(nodes) {
  network.selectNodes(nodes);
  neighbourhoodHighlight({ nodes: nodes });
  return nodes;
}

function selectNodes(nodes) {
  network.selectNodes(nodes);
  filterHighlight({nodes: nodes});
  return nodes;
}

function highlightFilter(filter) {
  let selectedNodes = []
  let selectedProp = filter['property']
  if (filter['item'] === 'node') {
    let allNodes = nodes.get({ returnType: "Object" });
    for (let nodeId in allNodes) {
      if (allNodes[nodeId][selectedProp] && filter['value'].includes((allNodes[nodeId][selectedProp]).toString())) {
        selectedNodes.push(nodeId)
      }
    }
  }
  else if (filter['item'] === 'edge'){
    let allEdges = edges.get({returnType: 'object'});
    // check if the selected property exists for selected edge and select the nodes connected to the edge
    for (let edge in allEdges) {
      if (allEdges[edge][selectedProp] && filter['value'].includes((allEdges[edge][selectedProp]).toString())) {
        selectedNodes.push(allEdges[edge]['from'])
        selectedNodes.push(allEdges[edge]['to'])
      }
    }
  }
  selectNodes(selectedNodes)
}</script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" integrity="sha512-WgxfT5LWjfszlPHXRmBWHkV2eceiWTOBvrKCNbdgDYTHrT2AeLCGbF4sZlZw3UMN3WtL0tGUoIAKsu8mllg/XA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js" integrity="sha512-LnvoEWDFrqGHlHmDD2101OrLcbsfkrzoSpvtSQtxK3RMnRV0eOkhhBN2dXHKRrUU8p2DGRTk35n4O8nWSVe1mQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
            
            
            
            
            
            

        
<center>
<h1></h1>
</center>

<!-- <link rel="stylesheet" href="../node_modules/vis/dist/vis.min.css" type="text/css" />
<script type="text/javascript" src="../node_modules/vis/dist/vis.js"> </script>-->
        <link
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6"
          crossorigin="anonymous"
        />
        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-JEW9xMcG8R+pH31jmWH6WWP0WintQrMb4s7ZOdauHnUtxwoG2vI5DkLtS3qm9Ekf"
          crossorigin="anonymous"
        ></script>


        <center>
          <h1></h1>
        </center>
        <style type="text/css">

             #mynetwork {
                 width: 100%;
                 height: 800px;
                 background-color: #ffffff;
                 border: 1px solid lightgray;
                 position: relative;
                 float: left;
             }

             

             

             
        </style>
    </head>


    <body>
        <div class="card" style="width: 100%">
            
            
            <div id="mynetwork" class="card-body"></div>
        </div>

        
        

        <script type="text/javascript">

              // initialize global variables.
              var edges;
              var nodes;
              var allNodes;
              var allEdges;
              var nodeColors;
              var originalNodes;
              var network;
              var container;
              var options, data;
              var filter = {
                  item : '',
                  property : '',
                  value : []
              };

              

              

              // This method is responsible for drawing the graph, returns the drawn network
              function drawGraph() {
                  var container = document.getElementById('mynetwork');

                  

                  // parsing and collecting nodes and edges from the python
                  nodes = new vis.DataSet([{"color": "lightgreen", "data_path": "https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/HW_Sites_EPSG4326.zip", "description": "Hazardous waste facility shapefile URL", "id": "haz_waste_shp_url", "label": "haz_waste_shp_url", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Load hazardous waste facility shapefile", "id": "load_haz_waste_shp", "label": "load_haz_waste_shp", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "orange", "description": "Hazardous waste facility GeoDataFrame", "id": "haz_waste_gdf", "label": "haz_waste_gdf", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Find tracts containing hazardous waste facilities", "id": "haz_waste_tracts", "label": "haz_waste_tracts", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "lightgreen", "data_path": "https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/tract_37_EPSG4326.zip", "description": "Tract boundary shapefile URL", "id": "tract_boundary_shp_url", "label": "tract_boundary_shp_url", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Load tract boundary shapefile", "id": "load_tract_boundary_shp", "label": "load_tract_boundary_shp", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "orange", "description": "Tract boundary GeoDataFrame", "id": "tract_boundary_gdf", "label": "tract_boundary_gdf", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Generate population choropleth map", "id": "population_choropleth_map", "label": "population_choropleth_map", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "lightgreen", "data_path": "https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/NC_tract_population.csv", "description": "Tract population CSV file URL", "id": "tract_population_csv_url", "label": "tract_population_csv_url", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Load tract population CSV file", "id": "load_tract_population_csv", "label": "load_tract_population_csv", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "orange", "description": "Tract population DataFrame", "id": "tract_population_df", "label": "tract_population_df", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Compute population in tracts with hazardous waste facilities", "id": "population_in_haz_waste_tracts", "label": "population_in_haz_waste_tracts", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "orange", "description": "Tracts containing hazardous waste facilities GeoDataFrame", "id": "haz_waste_tracts_gdf", "label": "haz_waste_tracts_gdf", "node_type": "data", "shape": "dot", "size": 10}, {"color": "deepskyblue", "description": "Highlight the borders of tracts with hazardous waste facilities on the map", "id": "highlighted_tracts_map", "label": "highlighted_tracts_map", "node_type": "operation", "shape": "dot", "size": 10}, {"color": "violet", "description": "Population living in tracts with hazardous waste facilities", "id": "population_in_haz_waste_tracts_value", "label": "population_in_haz_waste_tracts_value", "node_type": "data", "shape": "dot", "size": 10}, {"color": "orange", "description": "Population choropleth map image", "id": "population_choropleth_map_image", "label": "population_choropleth_map_image", "node_type": "data", "shape": "dot", "size": 10}, {"color": "violet", "description": "Highlighted tracts map image", "id": "highlighted_tracts_map_image", "label": "highlighted_tracts_map_image", "node_type": "data", "shape": "dot", "size": 10}]);
                  edges = new vis.DataSet([{"arrows": "to", "from": "haz_waste_shp_url", "to": "load_haz_waste_shp", "width": 1}, {"arrows": "to", "from": "load_haz_waste_shp", "to": "haz_waste_gdf", "width": 1}, {"arrows": "to", "from": "haz_waste_gdf", "to": "haz_waste_tracts", "width": 1}, {"arrows": "to", "from": "tract_boundary_shp_url", "to": "load_tract_boundary_shp", "width": 1}, {"arrows": "to", "from": "load_tract_boundary_shp", "to": "tract_boundary_gdf", "width": 1}, {"arrows": "to", "from": "tract_boundary_gdf", "to": "haz_waste_tracts", "width": 1}, {"arrows": "to", "from": "tract_boundary_gdf", "to": "population_choropleth_map", "width": 1}, {"arrows": "to", "from": "tract_population_csv_url", "to": "load_tract_population_csv", "width": 1}, {"arrows": "to", "from": "load_tract_population_csv", "to": "tract_population_df", "width": 1}, {"arrows": "to", "from": "tract_population_df", "to": "population_in_haz_waste_tracts", "width": 1}, {"arrows": "to", "from": "tract_population_df", "to": "population_choropleth_map", "width": 1}, {"arrows": "to", "from": "haz_waste_tracts", "to": "haz_waste_tracts_gdf", "width": 1}, {"arrows": "to", "from": "haz_waste_tracts_gdf", "to": "population_in_haz_waste_tracts", "width": 1}, {"arrows": "to", "from": "haz_waste_tracts_gdf", "to": "highlighted_tracts_map", "width": 1}, {"arrows": "to", "from": "population_in_haz_waste_tracts", "to": "population_in_haz_waste_tracts_value", "width": 1}, {"arrows": "to", "from": "population_choropleth_map", "to": "population_choropleth_map_image", "width": 1}, {"arrows": "to", "from": "population_choropleth_map_image", "to": "highlighted_tracts_map", "width": 1}, {"arrows": "to", "from": "highlighted_tracts_map", "to": "highlighted_tracts_map_image", "width": 1}]);

                  nodeColors = {};
                  allNodes = nodes.get({ returnType: "Object" });
                  for (nodeId in allNodes) {
                    nodeColors[nodeId] = allNodes[nodeId].color;
                  }
                  allEdges = edges.get({ returnType: "Object" });
                  // adding nodes and edges to the graph
                  data = {nodes: nodes, edges: edges};

                  var options = {
    "configure": {
        "enabled": false
    },
    "edges": {
        "color": {
            "inherit": true
        },
        "smooth": {
            "enabled": true,
            "type": "dynamic"
        }
    },
    "interaction": {
        "dragNodes": true,
        "hideEdgesOnDrag": false,
        "hideNodesOnDrag": false
    },
    "physics": {
        "enabled": true,
        "stabilization": {
            "enabled": true,
            "fit": true,
            "iterations": 1000,
            "onlyDynamicEdges": false,
            "updateInterval": 50
        }
    }
};

                  network = new vis.Network(container, data, options);
                  return network;

              }
              drawGraph();
        </script>
    </body>
</html>"""
        # Stream HTML content
        yield "event: message\ndata: " + json.dumps({"type": "html", "data": html_content}) + "\n\n"

        # Stream code content
        code_content = r'''import geopandas as gpd

def load_haz_waste_shp(haz_waste_shp_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/HW_Sites_EPSG4326.zip'):
    # Description: Load hazardous waste facility shapefile from a given URL
    # haz_waste_shp_url: Hazardous waste facility shapefile URL
    haz_waste_gdf = gpd.read_file(haz_waste_shp_url)
    return haz_waste_gdf

def load_tract_boundary_shp(tract_boundary_shp_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/tract_37_EPSG4326.zip'):
    # Description: Load tract boundary shapefile
    # tract_boundary_shp_url: Tract boundary shapefile URL
    tract_boundary_gdf = gpd.read_file(tract_boundary_shp_url)

    return tract_boundary_gdf
import pandas as pd

def load_tract_population_csv(tract_population_csv_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/NC_tract_population.csv'):
    """
    Load tract population CSV file.

    Parameters:
    tract_population_csv_url (str): URL of the tract population CSV file

    Returns:
    pd.DataFrame: DataFrame containing the tract population data
    """
    tract_population_df = pd.read_csv(tract_population_csv_url, dtype={'GEOID': str})
    tract_population_df.dropna(subset=['GEOID', 'TotalPopulation'], inplace=True)
    tract_population_df['GEOID'] = tract_population_df['GEOID'].str.zfill(11)  # Pad GEOID column with leading zeros if necessary

    return tract_population_df
import geopandas as gpd
import pandas as pd

def haz_waste_tracts(haz_waste_gdf, tract_boundary_gdf):
    """
    Find tracts containing hazardous waste facilities

    Parameters:
    - haz_waste_gdf: Hazardous waste facility GeoDataFrame
    - tract_boundary_gdf: Tract boundary GeoDataFrame

    Returns:
    - haz_waste_tracts_gdf: Tracts containing hazardous waste facilities GeoDataFrame
    """
    # Perform a spatial join between hazardous waste facilities and tract boundaries
    haz_waste_tracts_gdf = gpd.sjoin(tract_boundary_gdf, haz_waste_gdf, how='inner', op='intersects')
    
    return haz_waste_tracts_gdf
def population_in_haz_waste_tracts(tract_population_df=tract_population_df, haz_waste_tracts_gdf=haz_waste_tracts_gdf):
    """
    Compute population in tracts with hazardous waste facilities

    Parameters:
    - tract_population_df: Tract population DataFrame
    - haz_waste_tracts_gdf: Tracts containing hazardous waste facilities GeoDataFrame

    Returns:
    - population_in_haz_waste_tracts_value: Population living in tracts with hazardous waste facilities
    """
    # Perform a spatial join between tract population data and tracts with hazardous waste facilities
    haz_waste_population_gdf = gpd.sjoin(haz_waste_tracts_gdf, tract_population_df, how='inner', op='intersects')
    
    # Calculate the total population in tracts with hazardous waste facilities
    population_in_haz_waste_tracts_value = haz_waste_population_gdf['TotalPopulation'].sum()
    
    return population_in_haz_waste_tracts_value
import geopandas as gpd
import matplotlib.pyplot as plt

def population_choropleth_map(tract_boundary_gdf, tract_population_df):
    """
    Generate population choropleth map.

    Parameters:
    tract_boundary_gdf (GeoDataFrame): GeoDataFrame of tract boundaries
    tract_population_df (DataFrame): DataFrame of tract population data

    Returns:
    str: File path of the generated population choropleth map
    """
    # Merge the tract boundary GeoDataFrame with the tract population DataFrame
    merged_gdf = tract_boundary_gdf.merge(tract_population_df, on='GEOID')

    # Plot the choropleth map of population
    fig, ax = plt.subplots(figsize=(15, 10))
    merged_gdf.plot(column='TotalPopulation', cmap='coolwarm', linewidth=0.8, ax=ax, edgecolor='black', legend=True)
    
    # Highlight the borders of tracts with hazardous waste facilities
    haz_waste_tracts_gdf.plot(ax=ax, edgecolor='red', linewidth=3, facecolor='none')

    # Set plot title and axis labels
    ax.set_title('Population Choropleth Map')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Save the generated population choropleth map
    population_choropleth_map_image = 'population_choropleth_map.png'
    plt.savefig(population_choropleth_map_image, dpi=300)
    plt.close()

    return population_choropleth_map_image

population_choropleth_map(tract_boundary_gdf, tract_population_df)
def highlighted_tracts_map(haz_waste_tracts_gdf, population_choropleth_map_image):
    """
    Highlight the borders of tracts with hazardous waste facilities on the map.

    Parameters:
    - haz_waste_tracts_gdf: Tracts containing hazardous waste facilities GeoDataFrame
    - population_choropleth_map_image: File path of the population choropleth map image

    Returns:
    - highlighted_tracts_map_image: File path of the highlighted tracts map image
    """
    # Read the population choropleth map image
    population_map = plt.imread(population_choropleth_map_image)

    # Create a new figure and plot the population choropleth map
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.imshow(population_map)

    # Plot the borders of tracts with hazardous waste facilities as red lines
    haz_waste_tracts_gdf.boundary.plot(ax=ax, color='red', linewidth=2)

    # Set plot title and axis labels
    ax.set_title('Highlighted Tracts with Hazardous Waste Facilities')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Save the highlighted tracts map image
    highlighted_tracts_map_image = 'highlighted_tracts_map.png'
    plt.savefig(highlighted_tracts_map_image, dpi=300)
    plt.close()

    return highlighted_tracts_map_image
# Complete corrected code
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt


def assembly_solution():
    # Step 1: Load the hazardous waste facility shapefile
    def load_haz_waste_shp(haz_waste_shp_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/HW_Sites_EPSG4326.zip'):
        haz_waste_gdf = gpd.read_file(haz_waste_shp_url)
        return haz_waste_gdf

    # Step 2: Load the tract boundary shapefile
    def load_tract_boundary_shp(tract_boundary_shp_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/tract_37_EPSG4326.zip'):
        tract_boundary_gdf = gpd.read_file(tract_boundary_shp_url)
        return tract_boundary_gdf

    # Step 3: Load the tract population CSV file
    def load_tract_population_csv(tract_population_csv_url='https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/NC_tract_population.csv'):
        tract_population_df = pd.read_csv(tract_population_csv_url, dtype={'GEOID': str})
        tract_population_df.dropna(subset=['GEOID', 'TotalPopulation'], inplace=True)
        tract_population_df['GEOID'] = tract_population_df['GEOID'].str.zfill(11)
        return tract_population_df

    # Step 4: Find tracts containing hazardous waste facilities
    def haz_waste_tracts(haz_waste_gdf, tract_boundary_gdf):
        haz_waste_tracts_gdf = gpd.sjoin(tract_boundary_gdf, haz_waste_gdf, how='inner', op='intersects')
        return haz_waste_tracts_gdf

    # Step 5: Compute population in tracts with hazardous waste facilities
    def population_in_haz_waste_tracts(tract_population_df, haz_waste_tracts_gdf):
        haz_waste_population_gdf = gpd.sjoin(haz_waste_tracts_gdf, tract_population_df, how='inner', op='intersects')
        population_in_haz_waste_tracts_value = haz_waste_population_gdf['TotalPopulation'].sum()
        return population_in_haz_waste_tracts_value

    # Step 6: Generate population choropleth map 
    def population_choropleth_map(tract_boundary_gdf, tract_population_df):
        merged_gdf = tract_boundary_gdf.merge(tract_population_df, on='GEOID')
        fig, ax = plt.subplots(figsize=(15, 10))
        merged_gdf.plot(column='TotalPopulation', cmap='coolwarm', linewidth=0.8, ax=ax, edgecolor='black', legend=True)
        haz_waste_tracts_gdf.boundary.plot(ax=ax, edgecolor='red', linewidth=3, facecolor='none')
        ax.set_title('Population Choropleth Map')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        population_choropleth_map_image = 'population_choropleth_map.png'
        plt.savefig(population_choropleth_map_image, dpi=300)
        plt.close()
        return population_choropleth_map_image

    # Step 7: Highlight the borders of tracts with hazardous waste facilities on the map
    def highlighted_tracts_map(haz_waste_tracts_gdf, population_choropleth_map_image):
        population_map = plt.imread(population_choropleth_map_image)
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.imshow(population_map)
        haz_waste_tracts_gdf.boundary.plot(ax=ax, color='red', linewidth=2)
        ax.set_title('Highlighted Tracts with Hazardous Waste Facilities')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        highlighted_tracts_map_image = 'highlighted_tracts_map.png'
        plt.savefig(highlighted_tracts_map_image, dpi=300)
        plt.close()
        return highlighted_tracts_map_image

    # Step 1: Load the hazardous waste facility shapefile
    haz_waste_gdf = load_haz_waste_shp()

    # Step 2: Load the tract boundary shapefile
    tract_boundary_gdf = load_tract_boundary_shp()

    # Step 3: Load the tract population CSV file
    tract_population_df = load_tract_population_csv()

    # Step 4: Find tracts containing hazardous waste facilities
    haz_waste_tracts_gdf = haz_waste_tracts(haz_waste_gdf, tract_boundary_gdf)

    # Step 5: Compute population in tracts with hazardous waste facilities
    population_in_haz_waste_tracts_value = population_in_haz_waste_tracts(tract_population_df, haz_waste_tracts_gdf)
    print(f"Population in tracts with hazardous waste facilities: {population_in_haz_waste_tracts_value}")

    # Step 6: Generate population choropleth map
    population_choropleth_map_image = population_choropleth_map(tract_boundary_gdf, tract_population_df)

    # Step 7: Highlight the borders of tracts with hazardous waste facilities on the map
    highlighted_tracts_map_image = highlighted_tracts_map(haz_waste_tracts_gdf, population_choropleth_map_image)

assembly_solution()'''
        yield "event: message\ndata: " + json.dumps({"type": "code", "data": code_content}) + "\n\n"

        # Stream image content
        with open("result.png", "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
            yield "event: message\ndata: " + json.dumps({"type": "image", "data": "data:image/png;base64," + encoded_image}) + "\n\n"

    return StreamingResponse(stream_content(), media_type="text/event-stream")



@app.post('/llmgeo')
async def handler(request_data: Item):
    task_name = request_data.task_name
    task = request_data.task
    data_locations = request_data.data_locations

    save_dir = os.path.join(os.getcwd(), task_name)
    os.makedirs(save_dir, exist_ok=True)

    # create graph
    model = r"gpt-3.5-turbo"
    solution = Solution(
        task=task,
        task_name=task_name,
        save_dir=save_dir,
        data_locations=data_locations,
        model=model,
    )
    response_for_graph = solution.get_LLM_response_for_graph()
    solution.graph_response = response_for_graph
    solution.save_solution()

    # clear_output(wait=True)
    # display(Code(solution.code_for_graph, language='python'))
    #
    # exec(solution.code_for_graph)
    # solution_graph = solution.load_graph_file()

    # Show the graph
    G = nx.read_graphml(solution.graph_file)
    nt = helper.show_graph(G)
    html_name = os.path.join(os.getcwd(), solution.task_name + '.html')

    nt.show(name=html_name)
    with open(html_name, "r") as f:
        d = f.read()
    os.remove(html_name)
    return d

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)