layer_styles = {
#'Building As Symbol': {'color': 'black', 'renderer': 'point', 'opacity': 0.5},
'Spot Height': {'color': 'orange', 'renderer': 'point', 'opacity': 0.5},
'Bathymetry Point': {'color': 'yellow', 'renderer': 'point', 'opacity': 0.5},
'OHN Hydrographic Point': {'color': 'teal', 'renderer': 'point', 'opacity': 1},
'OHN Watercourse': {'color': 'blue', 'renderer': 'line', 'opacity': 0.5},
'Constructed Drain': {'color': 'blue', 'renderer': 'line', 'opacity': 0.5},
'ORN Segment With Address': {'color': 'gray', 'renderer': 'line', 'opacity': 0.5},
'Bathymetry Line': {'color': 'teal', 'renderer': 'line', 'opacity': 0.5},
'Contour': {'color': 'brown', 'renderer': 'line', 'opacity': 0.5},
'OHN Hydrographic Line': {'color': 'blue', 'renderer': 'line', 'opacity': 0.5},
'OHN Shoreline': {'color': 'purple', 'renderer': 'line', 'opacity': 0.5},
'Built Up Area': {'color': 'black', 'renderer': 'fill', 'opacity': 0.5},
'Building To Scale': {'color': 'black', 'renderer': 'fill', 'opacity': 0.5},
'Bathymetry Index': {'color': 'red', 'renderer': 'fill', 'opacity': 0.5},
'OHN Hydrographic Poly': {'color': 'red', 'renderer': 'fill', 'opacity': 0.5},
'Tile Drainage Area': {'color': 'orange', 'renderer': 'fill', 'opacity': 0.5},
'Wetland With Significance': {'color': 'purple', 'renderer': 'fill', 'opacity': 0.5},
'OHN Waterbody': {'color': 'lightblue', 'renderer': 'fill', 'opacity': 0.5},
'Conservation Reserve Regulated': {'color': 'lightgreen', 'renderer': 'fill', 'opacity': 0.5},
'Conservation Authority Admin Area': {'color': 'lightred', 'renderer': 'fill', 'opacity': 0.5},
'Ecodistrict': {'color': 'green', 'renderer': 'fill', 'opacity': 0.5},
'Ecoregion': {'color': 'beige', 'renderer': 'fill', 'opacity': 0.5},
'Ecozone': {'color': 'coral', 'renderer': 'fill', 'opacity': 0.5},
'Federal Protected Area': {'color': 'darkolivegreen', 'renderer': 'fill', 'opacity': 0.5},
'Indian Reserve': {'color': 'pink', 'renderer': 'fill', 'opacity': 0.5},
'Landform Conservation Area': {'color': 'khaki', 'renderer': 'fill', 'opacity': 0.5},
'MNR District': {'color': 'honeydew', 'renderer': 'fill', 'opacity': 0.5},
'MNR Region': {'color': 'goldenrod', 'renderer': 'fill', 'opacity': 0.5},
'Municipal Park': {'color': 'forestgreen', 'renderer': 'fill', 'opacity': 0.5},
'Municipal Bnd Lower And Single': {'color': 'gray', 'renderer': 'fill', 'opacity': 0.5},
'Municipal Bnd Upper And Dist': {'color': 'slategray', 'renderer': 'fill', 'opacity': 0.5},
'National Wildlife Area': {'color': 'maroon', 'renderer': 'fill', 'opacity': 0.5},
'OPS Region': {'color': 'fuchsia', 'renderer': 'fill', 'opacity': 0.5},
'Provincial Park Admin Zone': {'color': 'firebrick', 'renderer': 'fill', 'opacity': 0.5},
'Provincial Park Regulated': {'color': 'red', 'renderer': 'fill', 'opacity': 0.5},
'Province': {'color': 'dimgray', 'renderer': 'fill', 'opacity': 0.5},
'Site District': {'color': 'darkslategray', 'renderer': 'fill', 'opacity': 0.5},
'Site Region': {'color': 'red', 'renderer': 'fill', 'opacity': 0.5},
'Emergency Management Historical Event': {'color': 'red', 'renderer': 'point','opacity': 0.5},
'Fire Aviation and Emergency Facility Point': {'color': 'darkred', 'renderer': 'point', 'opacity': 0.5},
'Utility Site': {'color': 'brown', 'renderer': 'point', 'opacity': 0.5},
'Utility Line': {'color': 'darkorange', 'renderer': 'point', 'opacity': 0.5},
'Aggregate Designated Area': {'color': 'hotpink', 'renderer': 'fill', 'opacity': 0.5},
'Aggregate Inspector Jurisdiction': {'color': 'lightred', 'renderer': 'fill', 'opacity': 0.5},
'Aggregate Site Authorized Active': {'color': 'orange', 'renderer': 'fill', 'opacity': 0.5},
'Aggregate Site Authorized Inactive': {'color': 'darkgray', 'renderer': 'fill', 'opacity': 0.5},
'Aggregate Site Authorized Partial Surrender': {'color': 'gray', 'renderer': 'fill', 'opacity': 0.5},
'Aggregate Extraction Area': {'color': 'red', 'renderer': 'fill', 'opacity': 0.5},
'Aggregate Site Unrehabilitated': {'color': 'magenta', 'renderer': 'fill', 'opacity': 0.5},
'Airport Official': {'color': 'black', 'renderer': 'fill', 'opacity': 0.5},
'Airport Other': {'color': 'gray', 'renderer': 'fill', 'opacity': 0.5},
'ANSI': {'color': 'purple', 'renderer': 'fill', 'opacity': 0.5},
# 'Cadastral Location': {'color': 'red', 'renderer': 'unknown'},
# 'Caribou Range Boundary': {'color': 'red', 'renderer': 'unknown'},
# 'Crown Game Preserve': {'color': 'red', 'renderer': 'unknown'},
# 'Designated Gas Storage Area': {'color': 'red', 'renderer': 'unknown'},
# 'Fire Management Agreement Area': {'color': 'red', 'renderer': 'unknown'},
# 'Fire Response Plan Area': {'color': 'red', 'renderer': 'unknown'},
'Soil Survey Complex': {'color': 'khaki', 'renderer': 'fill', 'opacity': 0.5},
# 'Source Protection Area Generalized': {'color': 'red', 'renderer': 'unknown'},
# 'Wildlife Management Unit': {'color': 'red', 'renderer': 'unknown'},
# 'Greenbelt Hamlet': {'color': 'red', 'renderer': 'unknown'},
# 'Greenbelt River Valley Connection': {'color': 'red', 'renderer': 'unknown'},
# 'CLUPA Overlay': {'color': 'red', 'renderer': 'unknown'},
# 'CLUPA Provincial': {'color': 'red', 'renderer': 'unknown'},
# 'Federal Land Other': {'color': 'red', 'renderer': 'unknown'},
# 'Greenbelt Towns Villages': {'color': 'red', 'renderer': 'unknown'},
# 'Greenbelt Specialty Crop': {'color': 'red', 'renderer': 'unknown'},
'Greenbelt Outer Boundary': {'color': 'lightgreen', 'renderer': 'line', 'opacity': 0.5},
'Greenbelt Designation': {'color': 'violet', 'renderer': 'fill', 'opacity': 0.5},
# 'Geographic Township Improved': {'color': 'red', 'renderer': 'unknown'},
# 'Lake Simcoe PAW Boundary': {'color': 'red', 'renderer': 'unknown'},
# 'Lot Fabric Improved': {'color': 'red', 'renderer': 'unknown'},
# 'Natural Heritage System Area': {'color': 'red', 'renderer': 'unknown'},
'NGO Nature Reserve': {'color': 'darkgreen', 'renderer': 'fill', 'opacity': 0.5},
# 'Niagara Escarpment Policy Area': {'color': 'red', 'renderer': 'unknown'},
# 'Niagara Escarpment Minor Urban Centre': {'color': 'red', 'renderer': 'unknown'},
# 'Niagara Escarpment Plan Boundary': {'color': 'red', 'renderer': 'unknown'},
# 'Niagara Escarpment Plan Designation': {'color': 'red', 'renderer': 'unknown'},
'ORM Planning Area': {'color': 'yellow', 'renderer': 'fill', 'opacity': 0.5},
'ORM Land Use Designation': {'color': 'yellow', 'renderer': 'fill', 'opacity': 0.5},
# 'Forest Processing Facility': {'color': 'red', 'renderer': 'unknown'},
# 'Aquatic Resource Area Survey Point': {'color': 'red', 'renderer': 'unknown'},
# 'Fishing Access Point': {'color': 'red', 'renderer': 'unknown'},
# 'ARA Water Line Segment': {'color': 'red', 'renderer': 'unknown'},
# 'Fish Pathogen Boundary Source': {'color': 'red', 'renderer': 'unknown'},
# 'Fish Culture Operation MNR': {'color': 'red', 'renderer': 'unknown'},
# 'Fish Culture Operation Areas of Impact': {'color': 'red', 'renderer': 'unknown'},
# 'Bait Harvest Area': {'color': 'red', 'renderer': 'unknown'},
# 'ARA Water Poly Segment': {'color': 'red', 'renderer': 'unknown'},
# 'Fish Pathogen Management Zone': {'color': 'red', 'renderer': 'unknown'},
# 'Fisheries Management Zone': {'color': 'red', 'renderer': 'unknown'},
# 'Fish Activity Area': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Abiotic Damage Event': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Disease Damage Event': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Genetics Zone': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Insect Damage Event': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Management Unit': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Misc Damage Event': {'color': 'red', 'renderer': 'unknown'},
# 'Forest Resource Inventory Status': {'color': 'red', 'renderer': 'unknown'},
# 'Provincially Tracked Species 1km Grid': {'color': 'red', 'renderer': 'unknown'},
'Wooded Area': {'color': 'green', 'renderer': 'fill', 'opacity': 0.4}
}