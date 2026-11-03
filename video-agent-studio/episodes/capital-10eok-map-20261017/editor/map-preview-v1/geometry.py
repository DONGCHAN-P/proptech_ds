import math
# GRS80 transverse Mercator: EPSG5179 / UTM-K. SGIS provenance-linked inference,
# not CRS metadata certified for the local simplified file.
def forward(lon,lat):
 a=6378137.;f=1/298.257222101;e2=f*(2-f);ep=e2/(1-e2);k=.9996;p=math.radians(lat);l=math.radians(lon);l0=math.radians(127.5);p0=math.radians(38)
 def M(v):return a*((1-e2/4-3*e2**2/64-5*e2**3/256)*v-(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*v)+(15*e2**2/256+45*e2**3/1024)*math.sin(4*v)-35*e2**3/3072*math.sin(6*v))
 N=a/math.sqrt(1-e2*math.sin(p)**2);T=math.tan(p)**2;C=ep*math.cos(p)**2;A=math.cos(p)*(l-l0)
 x=1000000+k*N*(A+(1-T+C)*A**3/6+(5-18*T+T*T+72*C-58*ep)*A**5/120)
 y=2000000+k*(M(p)-M(p0)+N*math.tan(p)*(A*A/2+(5-T+9*C+4*C*C)*A**4/24+(61-58*T+T*T+600*C-330*ep)*A**6/720))
 return x,y

def rings(g):return g['coordinates'] if g['type']=='Polygon' else [r for poly in g['coordinates'] for r in poly]
def inside(point,geometry):
 x,y=point;yes=False
 for r in rings(geometry):
  for i,a in enumerate(r):
   b=r[i-1]
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
