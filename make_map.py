"""
make_map.py
Author: Brandon Sike bsike@umich.edu

(description)

 -------------------------------- ----+---- Todos ----+----

 * Docstrings

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

from matplotlib.colors import to_hex, LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch

from yaml import safe_load

def load_a2_parkf(config):
    parkf = geopandas.read_file(config['a2_parks']) # TODO
    # two extra 'parks' we don't want
    parkf = parkf[(parkf['NAME'] != "Ellsworth Storage Facility") & (parkf['NAME'] != "Tree Nursery")]
    return parkf

def load_a2_recf(config):
    outdoor_recf = geopandas.read_file(config['a2_landuse']) # TODO
    # only want outdoor recreation land usage
    outdoor_recf = outdoor_recf[outdoor_recf['LANDUSE'] == 'Outdoor Recreation']
    return outdoor_recf

def load_a2_streetf(config):
    streetf = geopandas.read_file(config['a2_street']) # TODO
    return streetf

def load_a2_noncityf(config):
    noncityf = geopandas.read_file(config['a2_noncity']) # TODO
    return noncityf

def load_a2_univf(config):
    univf = geopandas.read_file(config['a2_univ']) # TODO
    return univf

def load_a2_schoolf(config):
    schoolf = geopandas.read_file(config['a2_schools']) # TODO
    return schoolf

def load_a2_riverf(config):
    riverf = geopandas.read_file(config['a2_huron_river']) # TODO
    return riverf

def load_washtenaw_recf(config, bounds):
    washtenaw_recf = geopandas.read_file(config['washtenaw_rec']) # TODO
    washtenaw_recf = washtenaw_recf[washtenaw_recf.intersects(bounds)] # limit to plot window
    return washtenaw_recf

def load_washtenaw_conservf(config, bounds):
    washtenaw_conservf = geopandas.read_file(config['washtenaw_conserv']) # TODO
    washtenaw_conservf = washtenaw_conservf[washtenaw_conservf.intersects(bounds)]
    return washtenaw_conservf

def load_washtenaw_county_trailsf(config, bounds):
    washtenaw_county_trailsf = geopandas.read_file(config['washtenaw_trails']) # TODO
    washtenaw_county_trailsf = washtenaw_county_trailsf[washtenaw_county_trailsf.intersects(bounds)]
    return washtenaw_county_trailsf

def load_b2bf(config):
    b2bf = geopandas.read_file(config['washtenaw_b2b']) # TODO
    return b2bf

# define water bounds
def load_usgs_waterfs(config, bounds, crs):
    river_bounds = np.array(
        [[13274413.014220709, 305266.23547664745],
        [13321261.749900116, 283338.8878334562],
        [13317179.995464692, 274618.04125569976],
        [13270331.259785285, 296545.38889889093],
        [13274413.014220709, 305266.23547664745]]
    )
    extra_waterbounds = Polygon(shell=river_bounds)
    waterbounds_df = geopandas.GeoDataFrame(geometry=[extra_waterbounds], crs=crs)

    # USGS water files
    water1 = geopandas.read_file(config['usgs_water1']) # TODO
    water1 = water1.to_crs(crs) # convert coordinate system
    water1 = water1[water1.intersects(bounds)] # limit to plot window

    water2 = geopandas.read_file(config['usgs_water2']) # TODO
    water2 = water2.to_crs(crs)
    water2 = water2[water2.intersects(bounds)]

    water1_df = geopandas.GeoDataFrame(water1)
    water2_df = geopandas.GeoDataFrame(water1)

    water_union_df = water1_df.overlay(water2_df, how='union', keep_geom_type=True)
    water_removed_df = water_union_df.overlay(waterbounds_df, how='difference', keep_geom_type=True)

    return water_removed_df

def load_usgs_streetfs_and_railf(config, bounds, crs):
    usgs_st_names = config['usgs_streets'] # TODO

    usgs_streetf1 = geopandas.read_file(config['usgs_road1']) # TODO
    usgs_streetf1 = usgs_streetf1.to_crs(crs)
    usgs_streetf1 = usgs_streetf1[usgs_streetf1.intersects(bounds)]
    usgs_streetf1 = usgs_streetf1[np.array([x in usgs_st_names for x in usgs_streetf1['name'].values])]

    usgs_streetf2 = geopandas.read_file(config['usgs_road2']) # TODO
    usgs_streetf2 = usgs_streetf2.to_crs(crs)
    usgs_streetf2 = usgs_streetf2[usgs_streetf2.intersects(bounds)]
    usgs_streetf2 = usgs_streetf2[np.array([x in usgs_st_names for x in usgs_streetf2['name'].values])]

    railf = geopandas.read_file(config['usgs_rail']) # TODO
    railf = railf.to_crs(crs)
    railf = railf[railf.intersects(bounds)]

    return usgs_streetf1, usgs_streetf2, railf

def load_osm(config, bounds, crs, parkfs, trailfs):
    # OSM streets
    osm_streetf = geopandas.read_file(config['osm'], layer='lines') # TODO

    # park-only, footpath/cyclepath filter
    osm_streetf = osm_streetf.to_crs(crs)
    osm_streetf = osm_streetf[osm_streetf.intersects(bounds)]
    osm_streetf = osm_streetf[np.array([x in ['footway', 'path', 'pedestrian', 'cycleway', 'track'] for x in osm_streetf['highway'].values])]

    trail_mask = np.zeros(len(osm_streetf), dtype=bool)
    for parkf in parkfs:
        trail_mask = trail_mask | np.array([np.any(parkf.intersects(x)) for x in osm_streetf['geometry'].values])
    for trailf in trailfs:
        trail_mask = trail_mask & ~np.array([np.any(trailf.intersects(x)) for x in osm_streetf['geometry'].values])

    osm_streetf = osm_streetf[trail_mask]

    # water
    osm_waterf = geopandas.read_file(config['osm'], layer='multipolygons') # TODO
    osm_waterf = osm_waterf[osm_waterf['natural']=='water']
    osm_waterf = osm_waterf.to_crs(crs)
    osm_waterf = osm_waterf[osm_waterf.intersects(bounds)]
    osm_waterf = osm_waterf[osm_waterf.area < 1e6] # small bodies only

    return osm_streetf, osm_waterf

def calculate_street_linewidths(streetf, lane_denom):
    # calculate lane widths
    # apply number of lanes where available, otherwise assume 1
    lanewidth = np.where(streetf['Lanes'].isna(), 1/lane_denom, streetf['Lanes'].astype(float)/lane_denom)
    # apply 6 lanes to known highways
    lanewidth = np.where(~(streetf['NHFS'].isna() | (streetf['NHFS'] == '<Null>')), 6/lane_denom, lanewidth)
    return lanewidth

def add_park_labels(parkf):
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

    # decide where to label things
    change_dict = {
        "2570 Dexter Road Park": updict,
        "Allmendinger Park": updict,
        "Ann Arbor Senior Center": downdict,
        "Arbor Hills Nature Area": downdict,
        "Arbor Oaks Park": updict,
        "Arboretum Nature Area": updict,
        "Argo Nature Area": updict,
        "Bader Park": updict,
        "Bandemer Park": updict,
        "Barton Nature Area": updict,
        "Baxter Park": updict,
        "Beckley Park": updict,
        "Belize Park": updict,
        "Berkshire Creek Nature Area": downdict,
        "Bicentennial Park": updict,
        "Bird Hills Nature Area": updict,
        "Black Pond Woods Nature Area": updict,
        "Bluffs Nature Area": updict,
        "Braun Nature Area": downdict,
        "Broadway Park": updict,
        "Brokaw Nature Area": updict,
        "Bromley Park": updict,
        "Brookside Park": updict,
        "Bryant Community Center": downdict,
        "Buhr Park": updict,
        "Burns Park": updict,
        "Burr Oak Park": leftdict,
        "Buttonbush Nature Area": updict,
        "Cedar Bend Nature Area": updict,
        "Churchill Downs Park": rightdict,
        "Clinton Park": updict,
        "Cloverdale Park": updict,
        "Cobblestone Farm": rightdict,
        "Cranbrook Park": updict,
        "Crary Park": updict,
        "Creal Park": updict,
        "Depot Park": updict,
        "Devonshire Park": downdict,
        "Dhu Varren Woods Nature Area": updict,
        "Dicken Park": rightdict,
        "Dicken Woods Nature Area": updict,
        "Dolph Nature Area": updict,
        "Douglas Park": leftdict,
        "Dr. Harold J. Lockett Park": updict,
        "Earhart Park": updict,
        "Earhart West Park": updict,
        "Eberbach Cultural Arts Bldg": leftdict,
        "Eberwhite Nature Area": updict,
        "Eisenhower Park": rightdict,
        "Ellsworth Park": updict,
        "Esch Park": updict,
        "Evergreen Park": updict,
        "Fairview Cemetery": rightdict,
        "Farmers Market": rightdict,
        "Folkstone Park": rightdict,
        "Forest Nature Area": updict,
        "Forsythe Park": updict,
        "Foxfire East Park": updict,
        "Foxfire North Park": updict,
        "Foxfire South Park": updict,
        "Foxfire West Park": updict,
        "Frisinger Park": leftdict,
        "Fritz Park": updict,
        "Fuller Park": updict,
        "Furstenberg Nature Area": updict,
        "Gallup Park": updict,
        "Garden Homes Park": rightdict,
        "George Washington Park (The Rock)": updict,
        "Glacier Highlands Park": updict,
        "Glazier Hill Nature Area": updict,
        "Graydon Park": updict,
        "Greenbrier Park": rightdict,
        "Hannah Nature Area": updict,
        "Hanover Square Park": updict,
        "Hansen Nature Area": updict,
        "Hickory Nature Area": updict,
        "Hilltop Nature Area": updict,
        "Hollywood Park": updict,
        "Hunt Park": updict,
        "Huron Highlands Park": updict,
        "Huron Hills Golf Course": updict,
        "Huron Parkway Nature Area": updict,
        "Iroquois Park": updict,
        "Island Park": updict,
        "Kelly Park": updict,
        "Kempf House": downdict,
        "Kilburn Park": rightdict,
        "Kuebler Langford Nature Area": leftdict,
        "Lakewood Nature Area": rightdict,
        "Lansdowne Park": updict,
        "Las Vegas Park": updict,
        "Lawton Park": updict,
        "Leslie Park": updict,
        "Leslie Park Golf Course": updict,
        "Leslie Science and Nature Center": updict,
        "Leslie Woods Nature Area": updict,
        "Liberty Plaza": updict,
        "Longshore Park": updict,
        "Mack Pool": updict,
        "Malletts Creek Nature Area": updict,
        "Manchester Park": updict,
        "Marshall Nature Area": updict,
        "Mary Beth Doyle Park": updict,
        "Maryfield Wildwood Park": updict,
        "Meadowbrook Park": updict,
        "Mill Creek Park": leftdict,
        "Miller Nature Area": updict,
        "Mixtwood Pomona Park": updict,
        "Molin Nature Area": updict,
        "Museum On Main": rightdict,
        "Mushroom Park": leftdict,
        "Narrow Gauge Way Nature Area": updict,
        "Newport Creek Nature Area": updict,
        "North Main Park": rightdict,
        "Northside Community Center": downdict,
        "Northside Park": rightdict,
        "Oakridge Nature Area": updict,
        "Oakwoods Nature Area": updict,
        "Olson Park": updict,
        "Onder Park": updict,
        "Pilgrim Park": updict,
        "Pittsview Park": updict,
        "Placid Way Park": downdict,
        "Plymouth Parkway": updict,
        "Postmans Rest": rightdict,
        "Redbud Nature Area": updict,
        "Redwood Park": updict,
        "Riverside Park": downdict,
        "Riverwood Nature Area": updict,
        "Rose Park": leftdict,
        "Ruthven Nature Area": updict,
        "Scarlett Mitchell Nature Area": updict,
        "Scheffler Park": updict,
        "Sculpture Plaza": rightdict,
        "South Maple Park": updict,
        "South Pond Nature Area": rightdict,
        "South University Park": updict,
        "Stapp Nature Area": rightdict,
        "Stone School Park": updict,
        "Sugarbush Park": updict,
        "Sunset Brooks Nature Area": updict,
        "Swift Run Park": updict,
        "Sylvan Park": updict,
        "Terhune Pioneer Memorial Park": updict,
        "The Ponds Park": updict,
        "Traver Creek Nature Area": leftdict,
        "Tuebingen Park": updict,
        "Turnberry Park": updict,
        "Veterans Memorial Park": updict,
        "Virginia Park": updict,
        "Ward Park": updict,
        "Waterworks Park": updict,
        "Waymarket Park": updict,
        "Wellington Park": updict,
        "West Park": updict,
        "Wheeler Park": updict,
        "White Oak Park": updict,
        "Willow Nature Area": updict,
        "Windemere Park": updict,
        "Winewood Thaler Park": updict,
        "Woodbury Park": updict,
        "Wurster Park": updict,
    }

    # apply new labels
    for kname, dval in change_dict.items():
        for dk, dv in dval.items():
            parkf.loc[parkf['NAME'] == kname, dk] = dv

def add_park_colors(config, theme, parkf, xlim, ylim):
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
        parkf['hilbert_args'] = (hilb_args - np.min(hilb_args)) / (np.max(hilb_args)-np.min(hilb_args))
        # everything gets a number from 0 to 1 encoding position along the Hilbert curve

        # turn into colors via cmap
        # turn smooth increase of {0,...,1} to some rapid cycling
        # use an irrational number (e.g., np.e) to ensure that cycling is not periodic
        colorargs = parkf['hilbert_args'].values * (len(xpts)/np.e) % 1

        # colors for parks
        #map_green_colors = [
        #    "#b1d16c", "#72d263", "#42ad3f", "#3fa053", "#459660", "#306943",
        #]
        map_green_colors = theme['park_cycler']

        cmap = LinearSegmentedColormap.from_list('map_greens', map_green_colors)
        #cmap = plt.get_cmap('hsv') # for debugging

        # calculate park colors using the cmap and the hilbert args
        newcolors = cmap(colorargs)
        # edgecolors are just darkened colors
        newedgecolors = newcolors[:,:3]*0.8
        parkf['newcolors'] = [to_hex(x) for x in newcolors]
        parkf['newedgecolors'] = [to_hex(x) for x in newedgecolors]
    else:
        raise NotImplementedError("Only Hilbert currently implemented")

def make_map_main():
    print('Reading config...')
    with open('config.yml', 'r') as stream:
        config = safe_load(stream)
    theme_filename = f"themes/{config['color_theme']}.yml"
    with open(theme_filename, 'r') as stream:
        theme = safe_load(stream)

    xlim = config['xlim'] # TODO
    xlim = [float(k) for k in xlim]
    ylim = config['ylim'] # TODO
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
    riverf = load_a2_riverf(config)

    print('Reading Washtenaw files...')
    washtenaw_recf = load_washtenaw_recf(config, basic_bounds)
    washtenaw_conservf = load_washtenaw_conservf(config, basic_bounds)
    washtenaw_county_trailsf = load_washtenaw_county_trailsf(
        config, basic_bounds)
    b2bf = load_b2bf(config)

    print('Reading USGS files...')
    usgs_waterf = load_usgs_waterfs(config, basic_bounds, parkf.crs)
    usgs_streetf1, usgs_streetf2, railf = load_usgs_streetfs_and_railf(
        config, basic_bounds, parkf.crs)
    
    print('Reading OSM files...')
    osm_streetf, osm_waterf = load_osm(
        config, basic_bounds, parkf.crs, 
        [parkf, washtenaw_recf, washtenaw_conservf, outdoor_recf], 
        [washtenaw_county_trailsf])
    
    # lane widths
    print('Adding lane widths, labels, and colors...')
    lane_denom = config['lane_denom'] # TODO
    lanewidth = calculate_street_linewidths(streetf, lane_denom)

    add_park_labels(parkf)
    add_park_colors(config, theme, parkf, xlim, ylim)

    # main plotting goes here

    print('Starting plotting...')
    fig,ax = plt.subplots(figsize=config['dims_inches'], layout='none', gridspec_kw={"left":0, "right":1, "bottom":0, "top":1})

    ax.set_facecolor(theme['background'])

    # plot basic shapes
    outdoor_recf.plot(ax=ax, color=theme['other_green'])
    washtenaw_recf.plot(ax=ax, color=theme['other_green'])
    noncityf.plot(ax=ax, color=theme['other_green'])
    washtenaw_conservf.plot(ax=ax, color=theme['other_green'])
    univf.plot(ax=ax, color=theme['university'])
    schoolf.plot(ax=ax, color=theme['pub_schools'])
    water_color = theme['water']
    #water1.plot(ax=ax, color=water_color)
    #water2.plot(ax=ax, color=water_color)
    usgs_waterf.plot(ax=ax, color=water_color)
    riverf.plot(ax=ax, color=water_color)

    # parks on top of main water
    parkf.plot(ax=ax, color=parkf['newcolors'], edgecolor=parkf['newedgecolors'], lw=1.5)

    # small bodies of water on top of parks
    osm_waterf.plot(ax=ax, color=water_color)

    # railroads
    railf.plot(ax=ax, color=theme['railroad'], lw=10/lane_denom)

    street_color = theme['streets']

    # street linewidth by num lanes
    streetf.plot(ax=ax, color=street_color, lw=lanewidth)
    # gsis roads lanewidth 1
    usgs_streetf1.plot(ax=ax, color=street_color, lw=1.0/lane_denom)
    usgs_streetf2.plot(ax=ax, color=street_color, lw=1.0/lane_denom)
    # trails thin
    trail_base = theme['trail_base']
    trail_dots = theme['trail_dots']

    washtenaw_county_trailsf.plot(ax=ax, color=trail_base, lw=2.5/lane_denom, ls='-')
    washtenaw_county_trailsf.plot(ax=ax, color=trail_dots, lw=2.5/lane_denom, ls=':')
    osm_streetf.plot(ax=ax, color=trail_base, lw=2.5/lane_denom, ls='-')
    osm_streetf.plot(ax=ax, color=trail_dots, lw=2.5/lane_denom, ls=':')


    b2bf.plot(ax=ax, color=theme['b2b_base'], ls='-', lw=2)
    b2bf.plot(ax=ax, color=theme['b2b_stripes'], ls='--', lw=2)

    park_sq_color = theme['park_label']
    park_text_color = theme['park_text']

    #for cx, cy, ny, cn in zip(xpts, ypts, ypts_name, names):
    for idx, row in parkf.iterrows():
        ptcol = park_text_color if park_text_color != "" else row['newedgecolors']
        #ax.scatter(row['cross_x'], row['cross_y'], marker='x', color='#ee7722', s=0.5, lw=15)
        ax.scatter(row['cross_x'], row['cross_y'], marker='s', facecolors='#ffffff00', edgecolors='#eeeeee', s=24, lw=1, zorder=100+3*idx)
        ax.scatter(row['cross_x'], row['cross_y'], marker='s', facecolors='#ffffff00', edgecolors=park_sq_color, s=20, lw=1, zorder=101+3*idx)
        #ax.text(cx+2e2, ny, cn, color='#229922', fontsize=10, bbox=dict(edgecolor='#229922', facecolor='#ffffffb0', pad=0.3, boxstyle='Round'), ha='left', va='center')
        ax.annotate(row['NAME'], (row['cross_x'], row['cross_y']), (row['cross_x'] + row['label_x'], row['cross_y'] + row['label_y']), color=ptcol, fontsize=9, ha=row['ha'], va=row['va'],
                    bbox=dict(edgecolor=ptcol, facecolor='#ffffffb0', pad=0.3, boxstyle='Round'),
                    arrowprops=dict(color=park_sq_color, arrowstyle='-', relpos=(row['relpos_x'],row['relpos_y']), zorder=102+3*idx)
                    )

    ax.axis('off')

    #mx = (1.3273e7 + 1.3318e7) / 2
    #my = (2.64e5 + 3.03e5) / 2

    #xhalfrange = -(1.3273e7 - 1.3318e7)/2

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    park_name_list = list(parkf['NAME'].sort_values().values)
    park_name_list = [f"□ {pn}" for pn in park_name_list]
    pthird = len(park_name_list)//3
    park_names_1 = '\n'.join(park_name_list[:pthird])
    park_names_2 = '\n'.join(park_name_list[pthird:2*pthird])
    park_names_3 = '\n'.join(park_name_list[2*pthird:])
    fancybox = FancyBboxPatch(xy=(0.817,0.01),width=0.173,height=0.2,facecolor='#ffffffcc', edgecolor='#555555', boxstyle='Round, pad=0.003', transform=ax.transAxes, zorder=10)
    ax.add_patch(fancybox)
    checklist_color = theme['checklist']
    ax.text(0.817,0.21,park_names_1,fontsize=8,color=checklist_color,transform=ax.transAxes,ha='left',va='top', zorder=11)
    ax.text(0.875,0.21,park_names_2,fontsize=8,color=checklist_color,transform=ax.transAxes,ha='left',va='top', zorder=12)
    ax.text(0.937,0.21,park_names_3,fontsize=8,color=checklist_color,transform=ax.transAxes,ha='left',va='top', zorder=13)

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

    compass_x = xlim[0]+8e2+5280/4
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

    ax.text(mile_left-5e2,mile_bottom-5e2,"Primary data from A2Gov, Washtenaw County, and USGS. Some trails, cycling paths, and bodies of water from OSM.\nIntellectual property rights belong to respective owners. Not for commerical use. Version 0.18 by Brandon Sike.", color=street_color, fontsize=8, ha='left', va='top')

    plt.savefig('aa_v18.pdf')
    plt.close()
    print('Done!')


if __name__ == "__main__":
    make_map_main()
