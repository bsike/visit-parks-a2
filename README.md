# visit-parks-a2
Custom map creator for the Ann Arbor, Michigan "Visit Every Park" Challenge using publicly-available geospatial data.

# Getting Started:

Set directories to shape files (.shp) in `config.yml`. Then simply run `python make_map.py` to produce a map!

# Dependencies:

* pyyaml
* numpy
* scipy
* shapely
* geopandas
* matplotlib

# Dataset Download Links:

* **(Required!)** [Ann Arbor Parks](https://data.a2gov.org/city-of-ann-arbor/parks) for the city-owned parks included in the Visit Every Park Challenge.
* [Ann Arbor Streets](https://data.a2gov.org/city-of-ann-arbor/road-centerline) for roads.
* [Ann Arbor Water Bodies](https://data.a2gov.org/city-of-ann-arbor/waterbodies) for the Huron River and other bodies of water, limited in spatial extent.
* [Ann Arbor Land Use](https://data.a2gov.org/city-of-ann-arbor/land-use) for green space shading.
* [Ann Arbor Noncity Open Spaces](https://data.a2gov.org/city-of-ann-arbor/non-city-open-spaces) for green space shading.
* [Ann Arbor University-Owned](https://data.a2gov.org/city-of-ann-arbor/university-owned-land) for university land shading.
* [Ann Arbor Public Schools](https://data.a2gov.org/city-of-ann-arbor/schools) for public school shading.
* [USGS Water](https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_Michigan_State_Shape.zip) for water outside the extent of the Ann Arbor dataset.
* [USGS Transportation](https://prd-tnm.s3.amazonaws.com/StagedProducts/Tran/Shape/TRAN_Michigan_State_Shape.zip) for railways and additional roads not included in the Ann Arbor dataset. If the Ann Arbor road centerline file is not available, this will be used instead.
* [Washtenaw Recreation](https://ewashtenaw.sharefile.com/share/view/s8e94298d958e43dc91edfc3096b87e5a) for green space shading.
* [Washtenaw Conservation](https://ewashtenaw.sharefile.com/share/view/s80b216fe50504db8b5de50f7ffab1405) for green space shading.
* [Washtenaw Trails](https://ewashtenaw.sharefile.com/share/view/sde92b09ac7bb483c86e1c89674c8de38) for walking/cycling trails in Washtenaw county parks.
* [Washtenaw B2B](https://ewashtenaw.sharefile.com/share/view/s6ef35a4928854fd2bbc14bf844d0423a) for the Border-to-Border cycling trail.
* [Open Street Maps](https://overpass-api.de/api/map?bbox=-83.8415,42.2067,-83.6403,42.3591) for additional walking and cycling trails, including within Ann Arbor parks. If neither the Ann Arbor road centerline file nor the USGS transportation files are available, this will be used instead.