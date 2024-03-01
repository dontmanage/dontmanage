# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage


@dontmanage.whitelist()
def get_coords(doctype, filters, type):
	"""Get a geojson dict representing a doctype."""
	filters_sql = get_coords_conditions(doctype, filters)[4:]

	coords = None
	if type == "location_field":
		coords = return_location(doctype, filters_sql)
	elif type == "coordinates":
		coords = return_coordinates(doctype, filters_sql)

	return convert_to_geojson(type, coords)


def convert_to_geojson(type, coords):
	"""Converts GPS coordinates to geoJSON string."""
	geojson = {"type": "FeatureCollection", "features": None}

	if type == "location_field":
		geojson["features"] = merge_location_features_in_one(coords)
	elif type == "coordinates":
		geojson["features"] = create_gps_markers(coords)

	return geojson


def merge_location_features_in_one(coords):
	"""Merging all features from location field."""
	geojson_dict = []
	for element in coords:
		geojson_loc = dontmanage.parse_json(element["location"])
		if not geojson_loc:
			continue
		for coord in geojson_loc["features"]:
			coord["properties"]["name"] = element["name"]
			geojson_dict.append(coord.copy())

	return geojson_dict


def create_gps_markers(coords):
	"""Build Marker based on latitude and longitude."""
	geojson_dict = []
	for i in coords:
		node = {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": None}}
		node["properties"]["name"] = i.name
		node["geometry"]["coordinates"] = [i.longitude, i.latitude]  # geojson needs it reverse!
		geojson_dict.append(node.copy())

	return geojson_dict


def return_location(doctype, filters_sql):
	"""Get name and location fields for Doctype."""
	if filters_sql:
		try:
			coords = dontmanage.db.sql(
				f"""SELECT name, location FROM `tab{doctype}`  WHERE {filters_sql}""", as_dict=True
			)
		except dontmanage.db.InternalError:
			dontmanage.msgprint(dontmanage._("This Doctype does not contain location fields"), raise_exception=True)
			return
	else:
		coords = dontmanage.get_all(doctype, fields=["name", "location"])
	return coords


def return_coordinates(doctype, filters_sql):
	"""Get name, latitude and longitude fields for Doctype."""
	if filters_sql:
		try:
			coords = dontmanage.db.sql(
				f"""SELECT name, latitude, longitude FROM `tab{doctype}`  WHERE {filters_sql}""",
				as_dict=True,
			)
		except dontmanage.db.InternalError:
			dontmanage.msgprint(
				dontmanage._("This Doctype does not contain latitude and longitude fields"), raise_exception=True
			)
			return
	else:
		coords = dontmanage.get_all(doctype, fields=["name", "latitude", "longitude"])
	return coords


def get_coords_conditions(doctype, filters=None):
	"""Returns SQL conditions with user permissions and filters for event queries."""
	from dontmanage.desk.reportview import get_filters_cond

	if not dontmanage.has_permission(doctype):
		dontmanage.throw(dontmanage._("Not Permitted"), dontmanage.PermissionError)

	return get_filters_cond(doctype, filters, [], with_match_conditions=True)
