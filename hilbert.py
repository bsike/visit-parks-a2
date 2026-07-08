"""
hilbert.py
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

def get_4corn(center, width, height):
    bl = (center[0] - width/4, center[1] - height/4)
    br = (center[0] + width/4, center[1] - height/4)
    tl = (center[0] - width/4, center[1] + height/4)
    tr = (center[0] + width/4, center[1] + height/4)
    return bl, br, tl, tr

condir_vecs = np.array([[0,1],[0,-1],[-1,0],[1,0]])

atile = np.array([
    [0,0],
    [3,1]
])
btile = np.array([
    [1,2],
    [1,0],
])
ctile = np.array([
    [3,1],
    [2,2],
])
dtile = np.array([
    [2,3],
    [0,3],
])
abcd_tiles = np.array([atile,btile,ctile,dtile])
acon = np.array([
    [3,1],
    [0,-1]
])
bcon = np.array([
    [1,2],
    [3,-1],
])
ccon = np.array([
    [-1,1],
    [0,2],
])
dcon = np.array([
    [-1,2],
    [3,0],
])
abcd_cons = [acon, bcon, ccon, dcon]

def aplot(ax, center, width, height, condir):
    bl, br, tl, tr = get_4corn(center, width, height)
    cv = condir_vecs[condir]*width/2
    #ax.text(center[0], center[1], 'A', color='r', ha='center', va='center')
    ax.plot(*(np.array([bl,tl,tr,br,br+cv]).T), color='r')
def bplot(ax, center, width, height, condir):
    bl, br, tl, tr = get_4corn(center, width, height)
    cv = condir_vecs[condir]*width/2
    #ax.text(center[0], center[1], 'B', color ='b', ha='center', va='center')
    ax.plot(*(np.array([tr,tl,bl,br,br+cv]).T), color='r')
def cplot(ax, center, width, height, condir):
    bl, br, tl, tr = get_4corn(center, width, height)
    cv = condir_vecs[condir]*width/2
    #ax.text(center[0], center[1], 'C', color='g', ha='center', va='center')
    ax.plot(*(np.array([tr,br,bl,tl,tl+cv]).T), color='r')
def dplot(ax, center, width, height, condir):
    bl, br, tl, tr = get_4corn(center, width, height)
    cv = condir_vecs[condir]*width/2
    #ax.text(center[0], center[1], 'D', color='magenta', ha='center', va='center')
    ax.plot(*(np.array([bl,br,tr,tl,tl+cv]).T), color='r')

abcd_plots = [aplot, bplot, cplot, dplot]

def map_dist(conn):
    dist_res = np.zeros_like(conn, dtype=int)
    ii = 0
    xi = 0
    yi = conn.shape[1]-1
    while ii <= conn.size-1:
        assert dist_res[yi,xi] == 0
        dist_res[yi,xi] = ii
        cv = condir_vecs[conn[yi,xi]]

        xi += cv[0]
        yi -= cv[1]
        ii += 1

    return dist_res

def plot_hilbert(ax, hilb, conn, xmin=0,xmax=1,ymin=0,ymax=1,showdist=False):
    if showdist:
        dists = map_dist(conn)
        ax.imshow(dists[::-1,:], origin='lower', cmap='magma', extent=[0,1,0,1])
    npoints = hilb.shape[0]
    ds = 1.0/npoints
    dx = (xmax-xmin)*ds
    dy = (ymax-ymin)*ds
    xpts = np.linspace(xmin+dx/2, xmax-dy/2,npoints)
    ypts = np.linspace(ymin+dy/2, ymax-dy/2,npoints)[::-1]
    for xi in range(hilb.shape[0]):
        xp = xpts[xi]
        for yi in range(hilb.shape[0]):
            yp = ypts[yi]
            hh = hilb[yi,xi]
            cd = conn[yi,xi]
            abcd_plots[hh](ax, (xp,yp), dx, dy, cd)

def gen_hilbert(depth=8):
    running_hilbert = np.array([[0]], dtype=np.int8)
    running_connectors = np.array([[1]], dtype=np.int8)

    for di in range(depth):
        #print('doing depth', di)
        news = running_hilbert.shape[0]*2
        new_hilbert_keys = np.repeat(running_hilbert, 2, axis=0)
        new_hilbert_keys = np.repeat(new_hilbert_keys, 2, axis=1)

        old_cons_repped = np.repeat(running_connectors, 2, axis=0)
        old_cons_repped = np.repeat(old_cons_repped, 2, axis=1)

        tile_fills = [np.tile(xt, (news//2,news//2)) for xt in abcd_tiles]
        con_fills = [np.tile(xt, (news//2,news//2)) for xt in abcd_cons]

        new_hilbert = np.choose(new_hilbert_keys, tile_fills)
        new_con = np.choose(new_hilbert_keys, con_fills)
        new_con = np.where(new_con < 0, old_cons_repped, new_con)

        running_hilbert = new_hilbert
        running_connectors = new_con

    return running_hilbert, running_connectors