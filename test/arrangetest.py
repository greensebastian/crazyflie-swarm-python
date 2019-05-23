import numpy as np
import AsyncSwarm
import math

dist = 0.2
drone_count = 3

active_uris = (0, 1, 2)

swarm = AsyncSwarm.AsyncSwarm(active_uris)

drone_dist = 0.5
'''distance between each drone'''

formation = {AsyncSwarm.URI1: (0, 0),
             AsyncSwarm.URI2: (drone_dist, 0),
             AsyncSwarm.URI3: (0, drone_dist),
             AsyncSwarm.URI4: (-drone_dist, 0),
             AsyncSwarm.URI5: (0, -drone_dist)}

adj = np.zeros((drone_count, drone_count))

#print(formation['2'][0])


for uri1 in swarm.uris:
    for uri2 in swarm.uris:
        i = int(uri1[-1])-1
        j = int(uri2[-1])-1
        adj[i][j] = math.sqrt((formation[uri1][0]-formation[uri2][0])**2+(formation[uri1][1]-formation[uri2][1])**2)

print(adj)




'''
print(uris)

x = np.arange(0,dist*drone_count/2-dist,dist)
y = np.arange(0,2*dist,dist)

#print(x,y)

[gridx,gridy] = np.meshgrid(x,y)

print(gridx)
print(gridy)
'''
#newgridx = np.reshape(gridx,(drone_count,1))


#print(newgridx)