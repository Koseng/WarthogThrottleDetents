import cadquery as cq
import math

# ============================================
# EDIT HERE
#----------------
# Possible angles between 5° and 70° // max 73,4
# A320: [14, 23.5, 68]
# CJ4 : [18, 70]
# F15 : [70] StartBlock = [14]
# Blank: [] th=2.2
detentAngles = [14, 23.5, 68]

# Must be in order
startBlockDetentAngles = []
endBlockDetentAngles = []

text = "A320"

# Set overlap to 0 for fast test printing
overlap = 4
# ============================================

detentOffset = 0.1
detentRadius = 1.5


def calculate_arc_middle_point(arcStartPoint, arcEndPoint, radius):
    startEndDir = arcEndPoint-arcStartPoint
    halfPointDist = startEndDir.Length/2
    halfPoint =  arcStartPoint + startEndDir.normalized()*halfPointDist
    # 90 degrees to halfPoint direction
    hpMiddlePointDir = cq.Vector(startEndDir.y, -startEndDir.x, startEndDir.z)
    halfPMiddlePDist = math.sqrt(pow(radius,2)-pow(halfPointDist,2))
    midPoint = halfPoint + hpMiddlePointDir.normalized()*halfPMiddlePDist 
    return midPoint

def get_radius_point(midPoint, zeroDir, radius, alpha):
    rad = alpha * math.pi/180
    xN = zeroDir.x*math.cos(rad)+zeroDir.y*math.sin(rad)
    yN = -zeroDir.x*math.sin(rad)+zeroDir.y*math.cos(rad)
    return midPoint + cq.Vector(xN,yN,0)*radius

def create_detent(res, midpoint, zeroDir, radius, angle):
    p1 = get_radius_point(midPoint, zeroDir, radius, angle)
    return res.moveTo(p1.x, p1.y).circle(detentRadius).cutThruAll()

def create_stop(res, midpoint, zeroDir, radius, fromAngle, toAngle, ex):
    s = 1
    if (toAngle > fromAngle): s = -1
    p1 = get_radius_point(midPoint, zeroDir, radius, fromAngle)
    p2 = get_radius_point(midPoint, zeroDir, radius+1.7, fromAngle)
    p3 = get_radius_point(midPoint, zeroDir, radius+2, fromAngle-(1*s))
    p4 = get_radius_point(midPoint, zeroDir, radius, toAngle)
    res = res.moveTo(p1.x, p1.y).lineTo(p2.x,p2.y)
    res = res.tangentArcPoint((p3.x,p3.y), relative=False)
    res = res.tangentArcPoint((p4.x,p4.y), relative=False)
    return res.lineTo(p1.x, p1.y).close().extrude(ex)

# Create the base
(r,h,ln,fh,th) = (2.85, 13.6, 28, 10.2, 2.3)
res = cq.Workplane("YZ")
res = res.move(r,r).hLine(h).vLine(-2*r).hLine(-h)
res = res.radiusArc((r,r),r).close().extrude(ln)

# Create cut
res = res.faces(">Z").workplane(offset=overlap)
res = res.moveTo(ln,fh).vLine(r+h-fh).hLine(-12.8).vLine(-5)
res = res.line(6.4,-7.25)
startArc1 = cq.Vector(res.vertices().last().val().toTuple())
res = res.lineTo(ln,fh).close().cutThruAll()

# Create first arc
r1 = 18.8
endPointOffset = cq.Vector(22.37, 2.36, 0)
endArc1 = startArc1 + endPointOffset
res = res.moveTo(startArc1.x,startArc1.y)
res = res.radiusArc((endArc1.x, endArc1.y), r1)

# Create second arc and close
r2 = r1 + th
midPoint = calculate_arc_middle_point(startArc1, endArc1, r1)
mPointSArc1DirN = (startArc1 - midPoint).normalized()
mPointEArc1DirN = (endArc1 - midPoint).normalized()
startArc2 = midPoint + mPointSArc1DirN*r2
endArc2 = midPoint + mPointEArc1DirN*r2
res = res.lineTo(endArc2.x, endArc2.y)
res = res.radiusArc((startArc2.x, startArc2.y), -r2)
exLength = -2*(r+overlap)
res = res.lineTo(startArc1.x,startArc1.y).close().extrude(exLength)

# Create the detents
for a in detentAngles:
    res = create_detent(res, midPoint, mPointSArc1DirN, (r2+detentOffset), a)

prevAngle = 0    
for a in startBlockDetentAngles:
    res = create_stop(res, midPoint, mPointSArc1DirN, r2, a, prevAngle, exLength)
    prevAngle = a
    
prevAngle = 73.3 
for a in endBlockDetentAngles:
    res = create_stop(res, midPoint, mPointSArc1DirN, r2, a, prevAngle, exLength)
    prevAngle = a

# Text
if text:
    res = res.faces(">Y").workplane().center(-7.5,-(r+overlap))
    res = res.text(text, 5.5, -0.2, cut=True, combine=True)

# Export
cq.exporters.export(res,'detents.stl', tolerance=0.1, angularTolerance=0.1)
