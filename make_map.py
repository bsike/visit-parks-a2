"""
make_map.py
Author: Brandon Sike bsike@umich.edu

(description)

 -------------------------------- ----+---- Todos ----+----

 * Documentation
 #* Check if files exist
 #* Allow for missing files
 #* Account for using different road centerline files
 * Add different park coloring schemes
 * Make config filename a sys arg
 * Make compass more efficient

 ------------------------------- ----+---- License ----+----
 
visit-parks-a2 (c) by Brandon Sike

visit-parks-a2 is licensed under a
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/

"""

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, Point
#from shapely.plotting import plot_polygon
from shapely import shortest_line
import geopandas
from pyogrio.errors import DataSourceError

from matplotlib.colors import to_hex, LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch

from yaml import safe_load

import sys

version_string = "0.21"

def safe_read_geopandas(config, key, layer=None):
    try:
        if layer is None:
            geof = geopandas.read_file(config[key])
        else:
            geof = geopandas.read_file(config[key], layer=layer)
        return geof
    except KeyError:
        print(f'{key} was not found in config file. Skipping...')
        return None
    except DataSourceError:
        print(f'File labeled {key} at {config[key]} could not be read. Skipping...')
        return None

def load_a2_parkf(config):
    parkf = safe_read_geopandas(config, 'a2_parks')
    if parkf is None: return None

    # two extra 'parks' we don't want
    parkf = parkf[(parkf['NAME'] != "Ellsworth Storage Facility") & (parkf['NAME'] != "Tree Nursery")]
    return parkf

def load_a2_recf(config):
    outdoor_recf = safe_read_geopandas(config, 'a2_landuse')
    if outdoor_recf is None: return None

    # only want outdoor recreation land usage
    outdoor_recf = outdoor_recf[outdoor_recf['LANDUSE'] == 'Outdoor Recreation']
    return outdoor_recf

def load_a2_streetf(config):
    return safe_read_geopandas(config, 'a2_street')

def load_a2_noncityf(config):
    return safe_read_geopandas(config, 'a2_noncity')

def load_a2_univf(config):
    return safe_read_geopandas(config, 'a2_univ')

def load_a2_schoolf(config):
    return safe_read_geopandas(config, 'a2_schools')

def load_a2_waterf(config):
    return safe_read_geopandas(config, 'a2_water')

def load_washtenaw_recf(config, bounds):
    washtenaw_recf = safe_read_geopandas(config, 'washtenaw_rec')
    if washtenaw_recf is None: return None

    # limit to plot window
    washtenaw_recf = washtenaw_recf[washtenaw_recf.intersects(bounds)]
    return washtenaw_recf

def load_washtenaw_conservf(config, bounds):
    washtenaw_conservf = safe_read_geopandas(config, 'washtenaw_conserv')
    if washtenaw_conservf is None: return None

    # limit to plot window
    washtenaw_conservf = washtenaw_conservf[washtenaw_conservf.intersects(bounds)]
    return washtenaw_conservf

def load_washtenaw_county_trailsf(config, bounds):
    washtenaw_county_trailsf = safe_read_geopandas(config, 'washtenaw_trails')
    if washtenaw_county_trailsf is None: return None

    # limit to plot window
    washtenaw_county_trailsf = washtenaw_county_trailsf[washtenaw_county_trailsf.intersects(bounds)]
    return washtenaw_county_trailsf

def load_b2bf(config):
    return safe_read_geopandas(config, 'washtenaw_b2b')

# define water bounds
def load_usgs_waterfs(config, bounds, crs, a2_waterf=None):
    # USGS water files
    water1 = safe_read_geopandas(config, 'usgs_water1')
    if water1 is not None:
        water1 = water1.to_crs(crs) # convert coordinate system
        water1 = water1[water1.intersects(bounds)] # limit to plot window
        water1_df = geopandas.GeoDataFrame(water1)

    water2 = safe_read_geopandas(config, 'usgs_water2')
    if water2 is not None:
        water2 = water2.to_crs(crs)
        water2 = water2[water2.intersects(bounds)]
        water2_df = geopandas.GeoDataFrame(water1)

    if water1 is None or water2 is None:
        if water1 is None:
            if water2 is None:
                # both are None
                return None
            else:
                # water1 is None, water2 exists
                water_union_df = water2_df
        else:
            # water1 exists, water2 is None
            water_union_df = water1_df
    else:
        # both exist
        water_union_df = water1_df.overlay(water2_df, how='union', keep_geom_type=True)

    if a2_waterf is not None: 
        # cut out portion already filled in by A2 gov water bodies
        #print(a2_waterf.dissolve().convex_hull.buffer(-100, resolution=0))
        #print(type(a2_waterf.dissolve().convex_hull.buffer(-100, resolution=0)))
        a2_water_bounds = geopandas.GeoDataFrame(geometry=a2_waterf.dissolve().convex_hull.buffer(-100, resolution=0), crs=crs)
        water_removed_df = water_union_df.overlay(a2_water_bounds, how='difference', keep_geom_type=True)

        return water_removed_df
    else:
        return water_union_df

def load_usgs_streetfs_and_railf(config, bounds, crs, a2_streetf=None):
    usgs_st_names = config['usgs_streets']

    usgs_streetf1 = safe_read_geopandas(config, 'usgs_road1')
    if usgs_streetf1 is not None:
        usgs_streetf1 = usgs_streetf1.to_crs(crs)
        usgs_streetf1 = usgs_streetf1[usgs_streetf1.intersects(bounds)]
        if a2_streetf is None:
            print('Using USGS streets because A2 streets are missing.')
        elif usgs_st_names:
            usgs_streetf1 = usgs_streetf1[np.array([x in usgs_st_names for x in usgs_streetf1['name'].values])]

    usgs_streetf2 = safe_read_geopandas(config, 'usgs_road2')
    if usgs_streetf2 is not None:
        usgs_streetf2 = usgs_streetf2.to_crs(crs)
        usgs_streetf2 = usgs_streetf2[usgs_streetf2.intersects(bounds)]
        if a2_streetf is not None:
            ... # already printed
        elif usgs_st_names:
            usgs_streetf2 = usgs_streetf2[np.array([x in usgs_st_names for x in usgs_streetf2['name'].values])]

    railf = safe_read_geopandas(config, 'usgs_rail')
    if railf is not None:
        railf = railf.to_crs(crs)
        railf = railf[railf.intersects(bounds)]

    return usgs_streetf1, usgs_streetf2, railf

def load_osm(config, bounds, crs, parkfs, trailfs, 
             use_as_primary_streets=False,
             use_as_huron_river=False,
             use_small_water_bodies=False,
             a2_waterf=None):
    if use_as_primary_streets:
        raise NotImplementedError('OSM as primary street layer has not yet been implemented.')
    
    # OSM streets
    osm_streetf = safe_read_geopandas(config, 'osm', layer='lines')
    if osm_streetf is not None:
        # park-only, footpath/cyclepath filter
        osm_streetf = osm_streetf.to_crs(crs)
        osm_streetf = osm_streetf[osm_streetf.intersects(bounds)]
        osm_streetf = osm_streetf[np.array([x in ['footway', 'path', 'pedestrian', 'cycleway', 'track'] for x in osm_streetf['highway'].values])]

        trail_mask = np.zeros(len(osm_streetf), dtype=bool)
        for parkf in parkfs:
            if parkf is not None:
                trail_mask = trail_mask | np.array([np.any(parkf.intersects(x)) for x in osm_streetf['geometry'].values])
        for trailf in trailfs:
            if trailf is not None:
                trail_mask = trail_mask & ~np.array([np.any(trailf.intersects(x)) for x in osm_streetf['geometry'].values])

        osm_streetf = osm_streetf[trail_mask]

    # OSM water
    osm_waterf = None
    if use_as_huron_river or use_small_water_bodies:
        osm_waterf = safe_read_geopandas(config, 'osm', layer='multipolygons')
        if osm_waterf is not None:
            osm_waterf = osm_waterf[osm_waterf['natural']=='water']
            osm_waterf = osm_waterf.to_crs(crs)
            osm_waterf = osm_waterf[osm_waterf.intersects(bounds)]
            if not use_as_huron_river:
                # small bodies only
                osm_waterf = osm_waterf[osm_waterf.area < 1e6] 
                if a2_waterf is not None:
                    osm_waterf = geopandas.GeoDataFrame(data=osm_waterf, crs=crs)
                    # cut out portion already filled in by A2 gov water bodies
                    #a2_water_bounds = geopandas.GeoDataFrame(geometry=a2_waterf.dissolve().convex_hull.buffer(-100, resolution=0), crs=crs)
                    a2_water_bounds = geopandas.GeoDataFrame(geometry=a2_waterf.dissolve().concave_hull(ratio=0.1, allow_holes=False).buffer(-100,resolution=0), crs=crs)
                    osm_waterf = osm_waterf.overlay(a2_water_bounds, how='difference', keep_geom_type=True)

            elif use_as_huron_river and not use_small_water_bodies:
                # large bodies only
                osm_waterf = osm_waterf[osm_waterf.area > 1e6] 

    return osm_streetf, osm_waterf

valid_nfcs_highway_types = ['Interstate', 'Other Freeway']
def identify_known_highways(streetf):
    return np.array([x in valid_nfcs_highway_types for x in streetf['NFCS'].values])

def calculate_street_linewidths(streetf, lane_denom, highway_mask):
    # calculate lane widths
    # apply number of lanes where available, otherwise assume 1
    lanewidth = np.where(streetf['Lanes'].isna(), 1/lane_denom, streetf['Lanes'].astype(float)/lane_denom)
    # apply 6 lanes to known highways
    lanewidth = np.where(~(streetf['NHFS'].isna() | (streetf['NHFS'] == '<Null>')) & streetf['Lanes'].isna(), 6/lane_denom, lanewidth)
    lanewidth = np.where(highway_mask, 10/lane_denom, lanewidth)
    return lanewidth

def add_park_labels(config, parkf):
    # add crosses and label relative positions for everything

    # representative points for parks, to place the empty square
    centroids = []
    for idx, row in parkf.iterrows():
        geom = row['geometry']
        if geom.contains(geom.centroid):
            # if the centroid is within the shape, use it
            centroids.append(geom.centroid)
            # not always true (e.g., for some concave shapes, like a crescent moon)
        elif isinstance(geom, MultiPolygon):
            # if the shape is multiple polygons, pick the biggest one
            polys = geom.geoms
            maxpoly = polys[np.argmax([p.area for p in polys])]
            # same logic applied onto biggest polygon
            if maxpoly.contains(maxpoly.centroid):
                centroids.append(maxpoly.centroid)
            else:
                centroids.append(maxpoly.representative_point())
        else:
            # centroid was in the shape; easy answer
            centroids.append(geom.representative_point())

    # labelling information
    parkf['cross_x'] = [c.x for c in centroids]
    parkf['cross_y'] = [c.y for c in centroids]
    parkf['label_x'] = 0.0
    parkf['label_y'] = 2.5e2
    parkf['ha'] = 'center'
    parkf['va'] = 'bottom'
    parkf['relpos_x'] = 0.5
    parkf['relpos_y'] = 0.0

    updict = dict(
        label_x = 0,
        label_y = 2.5e2,
        ha='center',
        va='bottom',
        relpos_x=0.5,
        relpos_y=0.0,
    )
    downdict = dict(
        label_x = 0,
        label_y = -2.5e2,
        ha='center',
        va='top',
        relpos_x=0.5,
        relpos_y=1.0,
    )
    leftdict = dict(
        label_x = -2.5e2,
        label_y = 0.0,
        ha='right',
        va='center',
        relpos_x=1.0,
        relpos_y=0.5,
    )
    rightdict = dict(
        label_x = 2.5e2,
        label_y = 0.0,
        ha='left',
        va='center',
        relpos_x=0.0,
        relpos_y=0.5,
    )

    direction_encoder = {
        'up': updict,
        'down': downdict,
        'left': leftdict,
        'right': rightdict,
    }

    # decide where to label things
    label_filename = f"{config['label_directions']}.yml"
    with open(label_filename, 'r') as stream:
        change_dict = safe_load(stream)

    change_dict = {k:direction_encoder[i] for k,i in change_dict.items()}

    # apply new labels
    for kname, dval in change_dict.items():
        for dk, dv in dval.items():
            parkf.loc[parkf['NAME'] == kname, dk] = dv

def add_park_colors(config, parkf, xlim, ylim):
    if config['park_color_cycler'].lower() == 'hilbert':
        # colors via Hilbert curve
        import hilbert
        from scipy.interpolate import RegularGridInterpolator

        hilbert_dirs, hilbert_cons = hilbert.gen_hilbert(depth = 8)

        # calculate distances along hilbert curve
        hil_dists = hilbert.map_dist(hilbert_cons).T

        # calculate grid points (x,y) of the hilbert curve
        npoints = hil_dists.shape[0]
        ds = 1.0/npoints
        dx = (xlim[1] - xlim[0])*ds
        dy = (ylim[1] - ylim[0])*ds
        #dy = (ymax-ymin)*ds
        xpts = np.linspace(xlim[0]+dx/2, xlim[1]-dx/2,npoints)
        ypts = np.linspace(ylim[0]+dy/2, ylim[1]-dy/2,npoints)[::-1]

        # make interpolator for (x,y) -> D_Hilbert
        rgi_dist = RegularGridInterpolator((xpts, ypts), hil_dists)

        # calculate the hilbert distance (here "Hilbert argument") for each park based
        # on its label position
        hilb_args = rgi_dist((parkf['cross_x'], parkf['cross_y']))
        parkf['hilbert_args'] = np.argsort(hilb_args)
        # everything gets a number from 0 to 1 encoding position along the Hilbert curve

        # turn into colors via cmap
        # turn smooth increase of {0,...,1} to some rapid cycling
        # use an irrational number (e.g., np.e) to ensure that cycling is not periodic
        colorargs = parkf['hilbert_args'].values * (len(xpts)/np.e) % 1

        parkf['newcolors_arg'] = colorargs
    else:
        # TODO implement random, something else
        raise NotImplementedError("Only Hilbert currently implemented")

def make_map_main():
    try:
        config_filename = sys.argv[1]
    except IndexError:
        config_filename = 'config.yml'
    print('Reading config...')
    with open(config_filename, 'r') as stream:
        config = safe_load(stream)
    theme_name = config['color_theme']

    xlim = config['xlim']
    xlim = [float(k) for k in xlim]
    ylim = config['ylim']
    ylim = [float(k) for k in ylim]

    # create a rectangle that is our plot bounds
    polygon_shell = np.array([
        [xlim[0], xlim[1], xlim[1], xlim[0], xlim[0]],
        [ylim[0],ylim[0],ylim[1],ylim[1],ylim[0]]]).T
    basic_bounds = Polygon(shell=polygon_shell)

    # read files
    print('Reading files...')
    parkf = load_a2_parkf(config)
    outdoor_recf = load_a2_recf(config)
    streetf = load_a2_streetf(config)
    noncityf = load_a2_noncityf(config)
    univf = load_a2_univf(config)
    schoolf = load_a2_schoolf(config)
    a2waterf = load_a2_waterf(config)

    print('Reading Washtenaw files...')
    washtenaw_recf = load_washtenaw_recf(config, basic_bounds)
    washtenaw_conservf = load_washtenaw_conservf(config, basic_bounds)
    washtenaw_county_trailsf = load_washtenaw_county_trailsf(
        config, basic_bounds)
    b2bf = load_b2bf(config)

    print('Reading USGS files...')
    usgs_waterf = load_usgs_waterfs(config, basic_bounds, parkf.crs, a2_waterf=a2waterf)
    usgs_streetf1, usgs_streetf2, railf = load_usgs_streetfs_and_railf(
        config, basic_bounds, parkf.crs, a2_streetf=streetf)
    
    print('Reading OSM files...')
    osm_streetf, osm_waterf = load_osm(
        config, basic_bounds, parkf.crs, 
        [parkf, washtenaw_recf, washtenaw_conservf, outdoor_recf], 
        [washtenaw_county_trailsf],
        a2_waterf=a2waterf,
        use_small_water_bodies=True)
    
    # lane widths
    print('Adding lane widths, labels, and colors...')
    lane_denom = config['lane_denom']
    known_highway_mask = identify_known_highways(streetf)
    lanewidth = calculate_street_linewidths(streetf, lane_denom, known_highway_mask)

    add_park_labels(config, parkf)
    add_park_colors(config, parkf, xlim, ylim)

    # main plotting goes here
    while theme_name:
        print('Starting plotting...')
        theme_filename = f"themes/{theme_name}.yml"
        with open(theme_filename, 'r') as stream:
            theme = safe_load(stream)
        fig,ax = plt.subplots(figsize=config['dims_inches'], layout='none', gridspec_kw={"left":0, "right":1, "bottom":0, "top":1})

        fig.set_facecolor(theme['background'])

        other_green_color = theme['other_green']

        # plot basic shapes
        if outdoor_recf is not None:
            outdoor_recf.plot(ax=ax, color=other_green_color)
        if washtenaw_recf is not None:
            washtenaw_recf.plot(ax=ax, color=other_green_color)
        if noncityf is not None:
            noncityf.plot(ax=ax, color=other_green_color)
        if washtenaw_conservf is not None:
            washtenaw_conservf.plot(ax=ax, color=other_green_color)
        if univf is not None:
            univf.plot(ax=ax, color=theme['university'])
        if schoolf is not None:
            schoolf.plot(ax=ax, color=theme['pub_schools'])

        # parks below main water
        # prepare colors
        park_cycler = theme['park_cycler']
        if isinstance(park_cycler, str):
            cmap = plt.get_cmap(park_cycler)
        else:
            park_cycler_colors = theme['park_cycler']
            cmap = LinearSegmentedColormap.from_list('park_cycler', park_cycler_colors)

        # calculate park colors using the cmap and the hilbert args
        if parkf is not None:
            newcolors = cmap(parkf['newcolors_arg'])
            newedgecolors = newcolors[:,:3]*0.8
            parkf['newcolors'] = [to_hex(x) for x in newcolors]
            parkf['newedgecolors'] = [to_hex(x) for x in newedgecolors]

            parkf.plot(ax=ax, color=parkf['newcolors']) # only faces right now (below water layer)

        # water
        water_color = theme['water']
        if usgs_waterf is not None:
            usgs_waterf.plot(ax=ax, color=water_color)
        if a2waterf is not None:
            a2waterf.plot(ax=ax, color=water_color)

        # osm water
        if osm_waterf is not None:
            osm_waterf.plot(ax=ax, color=water_color)

        # park outlines on top of water
        if parkf is not None:
            parkf.plot(ax=ax, facecolor='none', edgecolor=parkf['newedgecolors'], lw=1.5)

        # railroads
        if railf is not None:
            railf.plot(ax=ax, color=theme['railroad'], lw=10/lane_denom)

        # streets & highways
        street_color = theme['streets']
        highway_color = theme['highway']
        street_highway_colors = np.where(known_highway_mask, highway_color, street_color)

        # street linewidth by num lanes
        if streetf is not None:
            streetf.plot(ax=ax, color=street_highway_colors, lw=lanewidth)

        # gsis roads lanewidth 1
        if usgs_streetf1 is not None:
            usgs_streetf1.plot(ax=ax, color=street_color, lw=1.0/lane_denom)
        if usgs_streetf2 is not None:
            usgs_streetf2.plot(ax=ax, color=street_color, lw=1.0/lane_denom)

        # trails thin
        trail_base = theme['trail_base']
        trail_dots = theme['trail_dots']
        if washtenaw_county_trailsf is not None:
            washtenaw_county_trailsf.plot(ax=ax, color=trail_base, lw=2.5/lane_denom, ls='-')
            washtenaw_county_trailsf.plot(ax=ax, color=trail_dots, lw=2.5/lane_denom, ls=':')
        if osm_streetf is not None:
            osm_streetf.plot(ax=ax, color=trail_base, lw=2.5/lane_denom, ls='-')
            osm_streetf.plot(ax=ax, color=trail_dots, lw=2.5/lane_denom, ls=':')

        if b2bf is not None:
            b2bf.plot(ax=ax, color=theme['b2b_base'], ls='-', lw=2)
            b2bf.plot(ax=ax, color=theme['b2b_stripes'], ls='--', lw=2)

        park_sq_color = theme['park_label']
        park_text_color = theme['park_text']
        bbox_bg_color = theme['bbox_bgs']

        if parkf is not None:
            for idx, row in parkf.iterrows():
                ptcol = park_text_color if park_text_color != "" else row['newedgecolors']
                ax.scatter(row['cross_x'], row['cross_y'], marker='s', 
                           facecolors='#ffffff00', edgecolors='#eeeeee', 
                           s=24, lw=1, zorder=100+3*idx)
                ax.scatter(row['cross_x'], row['cross_y'], marker='s', 
                           facecolors='#ffffff00', edgecolors=park_sq_color, 
                           s=20, lw=1, zorder=101+3*idx)
                ax.annotate(
                    row['NAME'], 
                    (row['cross_x'], row['cross_y']), 
                    (row['cross_x'] + row['label_x'], row['cross_y'] + row['label_y']), 
                    color=ptcol, fontsize=9, ha=row['ha'], va=row['va'],
                            bbox=dict(
                                edgecolor=ptcol, 
                                facecolor=bbox_bg_color, 
                                pad=0.3, 
                                boxstyle='Round'
                                ),
                            arrowprops=dict(
                                color=park_sq_color,
                                arrowstyle='-', 
                                relpos=(row['relpos_x'],row['relpos_y']), 
                                zorder=102+3*idx
                                )
                            ),

        ax.axis('off')

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

        if bool(config['show_checklist']):
            checklist_color = theme['checklist']
            park_name_list = list(parkf['NAME'].sort_values().values)
            park_name_list = [f"□ {pn}" for pn in park_name_list]
            pthird = len(park_name_list)//3
            park_names_1 = '\n'.join(park_name_list[:pthird])
            park_names_2 = '\n'.join(park_name_list[pthird:2*pthird])
            park_names_3 = '\n'.join(park_name_list[2*pthird:])
            fancybox = FancyBboxPatch(
                xy=(0.817,0.01),width=0.173,height=0.2,
                facecolor=bbox_bg_color, edgecolor=checklist_color, 
                boxstyle='Round, pad=0.003', transform=ax.transAxes, zorder=10)
            ax.add_patch(fancybox)
            ax.text(0.817,0.21,park_names_1,fontsize=8,color=checklist_color,
                    transform=ax.transAxes,ha='left',va='top', zorder=11)
            ax.text(0.875,0.21,park_names_2,fontsize=8,color=checklist_color,
                    transform=ax.transAxes,ha='left',va='top', zorder=12)
            ax.text(0.937,0.21,park_names_3,fontsize=8,color=checklist_color,
                    transform=ax.transAxes,ha='left',va='top', zorder=13)

        #plot_hilbert(ax, running_hilbert, running_connectors, mx-xhalfrange, mx+xhalfrange, my-xhalfrange, my+xhalfrange)

        mile_left = xlim[0]+1e3
        mile_bottom = ylim[0]+1e3
        mile_color = theme['scale_mile']
        km_color = theme['scale_km']
        ax.plot([mile_left, mile_left + 5280], [mile_bottom, mile_bottom], lw=3, color=mile_color)
        ax.plot([mile_left, mile_left + 3280.84], [mile_bottom-4e1, mile_bottom-4e1], lw=3, color=km_color)
        ax.vlines([mile_left, mile_left + 5280], [mile_bottom, mile_bottom], [mile_bottom+1.2e2, mile_bottom+1.2e2], color=mile_color, lw=3)
        ax.vlines([mile_left, mile_left + 3280.84], [mile_bottom-4e1-1.2e2, mile_bottom-4e1-1.2e2], [mile_bottom-4e1, mile_bottom-4e1], color=km_color, lw=3)
        ax.text(mile_left+5280/2, mile_bottom+4e1, '1 mi', va='bottom', ha='center', color=mile_color)
        ax.text(mile_left+3280.84/2, mile_bottom-1e2, '1 km', va='top', ha='center', color=km_color)

        compass_x = xlim[0]+2.5e3+5280/4
        compass_y = ylim[0]+1e3+5280/4
        compass_size = 3e2
        compass_lw=5
        compass_color1 = theme['compass_base']
        compass_color2 = theme['compass_acc']

        ax.plot([compass_x, compass_x], [compass_y, compass_y+compass_size], lw=compass_lw, color=compass_color1)
        ax.plot([compass_x, compass_x], [compass_y, compass_y-compass_size], lw=compass_lw, color=compass_color1)
        ax.plot([compass_x, compass_x+compass_size], [compass_y, compass_y], lw=compass_lw, color=compass_color1)
        ax.plot([compass_x, compass_x-compass_size], [compass_y, compass_y], lw=compass_lw, color=compass_color1)
        ax.plot([compass_x, compass_x], [compass_y, compass_y+compass_size*0.97], lw=1, color=compass_color2)
        ax.plot([compass_x, compass_x], [compass_y, compass_y-compass_size*0.97], lw=1, color=compass_color2)
        ax.plot([compass_x, compass_x+compass_size*0.97], [compass_y, compass_y], lw=1, color=compass_color2)
        ax.plot([compass_x, compass_x-compass_size*0.97], [compass_y, compass_y], lw=1, color=compass_color2)

        ax.text(compass_x, compass_y+compass_size+1e2, 'N', ha='center', va='bottom', fontsize=10, color=compass_color1)
        ax.text(compass_x, compass_y-compass_size-1e2, 'S', ha='center', va='top', fontsize=10, color=compass_color1)
        ax.text(compass_x+compass_size+1e2, compass_y, 'E', ha='left', va='center', fontsize=10, color=compass_color1)
        ax.text(compass_x-compass_size-1e2, compass_y, 'W', ha='right', va='center', fontsize=10, color=compass_color1)

        # legend
        legend_axes = ax.inset_axes(bounds=(mile_left, mile_bottom+7.5e2, 2e3, 1.8e3), transform=ax.transData, zorder=11)
        fancybox = FancyBboxPatch(xy=(0,0),width=1,height=1,facecolor='#ffffffff', edgecolor='#555555', boxstyle='Round, pad=0.01', transform=legend_axes.transAxes, zorder=10)
        ax.add_patch(fancybox)
        legend_axes.set_xlim(0,1)
        legend_axes.set_ylim(0,1)
        legend_axes.axis('off')

        legend_axes.plot([0.05,0.15],[0.9,0.9], color=street_color, lw=3/lane_denom)
        legend_axes.text(0.18,0.9,'Street',transform=legend_axes.transAxes, fontsize=8, color=street_color, ha='left', va='center')

        legend_axes.plot([0.05,0.15],[0.8,0.8], color=trail_base, lw=2.5/lane_denom, ls='-')
        legend_axes.plot([0.05,0.15],[0.8,0.8], color=trail_dots, lw=2.5/lane_denom, ls=':')
        legend_axes.text(0.18,0.8,'Trail',transform=legend_axes.transAxes, fontsize=8, color=trail_base, ha='left', va='center')

        legend_axes.plot([0.05,0.1],[0.7,0.7], color=theme['b2b_base'], lw=2, ls='-')
        legend_axes.plot([0.1,0.15],[0.7,0.7], color=theme['b2b_stripes'], lw=2, ls='-')
        legend_axes.text(0.18,0.7,'B2B',transform=legend_axes.transAxes, fontsize=8, color=theme['b2b_base'], ha='left', va='center')

        legend_axes.plot([0.05,0.15],[0.6,0.6], color=highway_color, lw=10/lane_denom)
        legend_axes.text(0.18,0.6,'Highway',transform=legend_axes.transAxes, fontsize=8, color=highway_color, ha='left', va='center')

        legend_axes.plot([0.05,0.15],[0.5,0.5], color=theme['railroad'], lw=10/lane_denom)
        legend_axes.text(0.18,0.5,'Railway',transform=legend_axes.transAxes, fontsize=8, color=theme['railroad'], ha='left', va='center')

        legend_axes.fill_between([0.07,0.13],[0.37,0.37],[0.43,0.43],color=other_green_color)
        legend_axes.text(0.18,0.4,'Non-city Green Space',transform=legend_axes.transAxes, fontsize=8, color='#555555', ha='left', va='center')

        legend_axes.fill_between([0.07,0.13],[0.27,0.27],[0.33,0.33],color=theme['university'])
        legend_axes.text(0.18,0.3,'University-Owned',transform=legend_axes.transAxes, fontsize=8, color='#555555', ha='left', va='center')

        legend_axes.fill_between([0.07,0.13],[0.17,0.17],[0.23,0.23],color=theme['pub_schools'])
        legend_axes.text(0.18,0.2,'Public School',transform=legend_axes.transAxes, fontsize=8, color='#555555', ha='left', va='center')

        legend_axes.fill_between([0.07,0.13],[0.07,0.07],[0.13,0.13],color=water_color)
        legend_axes.text(0.18,0.1,'Water',transform=legend_axes.transAxes, fontsize=8, color=water_color, ha='left', va='center')

        # TODO update data information based on what is actually provided.
        ax.text(mile_left-5e2,mile_bottom-5e2,"Primary data from A2Gov, Washtenaw County, and USGS. Some trails, cycling paths, and bodies of water from OSM.\nIntellectual property rights belong to respective owners. Not for commerical use. https://github.com/bsike/visit-parks-a2", color=street_color, fontsize=8, ha='left', va='top')

        plt.savefig(f'aa_{theme_name}_v{version_string}.pdf')
        plt.close()
        theme_name = input('Make another with theme: ')
    print('Done!')


if __name__ == "__main__":
    make_map_main()
