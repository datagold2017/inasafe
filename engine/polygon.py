"""Polygon, line and point algorithms

Clipping
Intersection
Populating a polygon with random points
"""

import numpy as num
from math import sqrt
from numerical_tools import ensure_numeric


def separate_points_by_polygon(points, polygon,
                               closed=True,
                               check_input=True):
    """Determine whether points are inside or outside a polygon

    Input:
       points - Tuple of (x, y) coordinates, or list of tuples
       polygon - list of vertices of polygon
       closed - (optional) determine whether points on boundary should be
       regarded as belonging to the polygon (closed = True)
       or not (closed = False)
       check_input: Allows faster execution if set to False

    Outputs:
       indices: array of same length as points with indices of points falling
       inside the polygon listed from the beginning and indices of points
       falling outside listed from the end.

       count: count of points falling inside the polygon

       The indices of points inside are obtained as indices[:count]
       The indices of points outside are obtained as indices[count:]

    Examples:
       U = [[0,0], [1,0], [1,1], [0,1]]  # Unit square

       separate_points_by_polygon( [[0.5, 0.5], [1, -0.5], [0.3, 0.2]], U)
       will return the indices [0, 2, 1] and count == 2 as only the first
       and the last point are inside the unit square

    Remarks:
       The vertices may be listed clockwise or counterclockwise and
       the first point may optionally be repeated.
       Polygons do not need to be convex.
       Polygons can have holes in them and points inside a hole is
       regarded as being outside the polygon.

    Algorithm is based on work by Darel Finley,
    http://www.alienryderflex.com/polygon/

    """

    if check_input:
        # Input checks
        msg = 'Keyword argument "closed" must be boolean'
        assert isinstance(closed, bool), msg

        try:
            points = ensure_numeric(points, num.float)
        except NameError, e:
            raise NameError, e
        except:
            msg = 'Points could not be converted to numeric array'
            raise msg

        try:
            polygon = ensure_numeric(polygon, num.float)
        except NameError, e:
            raise NameError, e
        except:
            msg = 'Polygon could not be converted to numeric array'
            raise msg

        msg = 'Polygon array must be a 2d array of vertices'
        assert len(polygon.shape) == 2, msg

        msg = 'Polygon array must have two columns'
        assert polygon.shape[1]==2, msg

        msg = ('Points array must be 1 or 2 dimensional. '
               'I got %d dimensions' % len(points.shape))
        assert 0 < len(points.shape) < 3, msg

        if len(points.shape) == 1:
            # Only one point was passed in.  Convert to array of points.
            points = num.reshape(points, (1,2))

            msg = ('Point array must have two columns (x,y), '
                   'I got points.shape[1]=%d' % points.shape[0])
            assert points.shape[1]==2, msg


            msg = ('Points array must be a 2d array. I got %s.'
                   % str(points[:30]))
            assert len(points.shape)==2, msg

            msg = 'Points array must have two columns'
            assert points.shape[1]==2, msg

    N = polygon.shape[0] # Number of vertices in polygon
    M = points.shape[0]  # Number of points

    indices = num.zeros(M, num.int)

    count = _separate_points_by_polygon(points, polygon, indices,
                                        int(closed))

    # log.critical('Found %d points (out of %d) inside polygon' % (count, M))

    return indices, count


def _separate_points_by_polygon(points, polygon, indices,
                                closed):
    """Underlying algorithm to partition point according to polygon

    Old C-code converted to Python
    FIXME(Ole): Refactor into numpy code
    """

    rtol=0.0
    atol=0.0

    # Get polygon extents to quickly rule out points that
    # are outside its bounding box
    minpx = min(polygon[:, 0])
    maxpx = max(polygon[:, 0])
    minpy = min(polygon[:, 1])
    maxpy = max(polygon[:, 1])

    M = points.shape[0]
    N = polygon.shape[0]

    inside_index = 0     # Keep track of points inside
    outside_index = M-1  # Keep track of points outside (starting from end)

    # Begin main loop (for each point) - FIXME (write as vector ops)
    for k in range(M):
        x = points[k, 0]
        y = points[k, 1]
        inside = 0

        if x > maxpx or x < minpx or y > maxpy or y < minpy:
            #  Skip if point is outside polygon bounding box
            pass
        else:
            # Check if it is inside polygon
            for i in range(N):
                # Loop through polygon vertices
                j = (i + 1) % N

                px_i = polygon[i, 0]
                py_i = polygon[i, 1]
                px_j = polygon[j, 0]
                py_j = polygon[j, 1]

                if point_on_line(points[k, :],
                                 [[px_i, py_i], [px_j, py_j]],
                                 rtol, atol):
                    #  Point coincides with line segment
                    if closed == 1:
                        inside = 1
                    else:
                        inside = 0
                    break
                else:
                    # Check if truly inside polygon
                    if (((py_i < y) and (py_j >= y)) or
                        ((py_j < y) and (py_i >= y))):
                        if (px_i + (y-py_i)/(py_j-py_i)*(px_j-px_i) < x):
                            inside = 1-inside

        # Record point as either inside or outside
        if inside == 1:
            indices[inside_index] = k
            inside_index += 1
        else:
            indices[outside_index] = k
            outside_index -= 1

    return inside_index;


def point_on_line(point, line, rtol=1.0e-5, atol=1.0e-8):
    """Determine whether a point is on a line segment

    Input
        point:  Coordinates given by sequence [x, y]
        line: Endpoint coordinates [[x0, y0], [x1, y1]] or
              the equivalent 2x2 numeric array with each row corresponding
              to a point.
        rtol: Relative error for how close a point must be to be accepted
        atol: Absolute error for how close a point must be to be accepted

    Output
        True or False

    Notes

    Line can be degenerate and function still works to discern coinciding
    points from non-coinciding.

    Tolerances rtol and atol are used with numpy.allclose()
    """

    point = ensure_numeric(point)
    line = ensure_numeric(line)

    x = point[0]; y = point[1]
    x0, y0 = line[0]
    x1, y1 = line[1]

    a0 = x - x0
    a1 = y - y0

    a_normal0 = a1
    a_normal1 = -a0

    b0 = x1 - x0
    b1 = y1 - y0

    nominator = abs(a_normal0 * b0 + a_normal1 * b1)
    denominator = b0 * b0 + b1 * b1;

    # Determine if line is parallel to point vector up to a tolerance
    is_parallel = 0;
    if denominator == 0.0:
        # Denominator is negative - use absolute tolerance
        if nominator <= atol:
            is_parallel = True
    else:
        # Denominator is positive - use relative tolerance
        if nominator / denominator <= rtol:
            is_parallel = True

    if is_parallel:
        # Point is somewhere on the infinite extension of the line
        # subject to specified absolute tolerance

        len_a = sqrt(a0 * a0 + a1 * a1)
        len_b = sqrt(b0 * b0 + b1 * b1)

        if a0 * b0 + a1 * b1 >= 0 and len_a <= len_b:
            return True
        else:
            return False
    else:
        return False


######
# Result functions used in intersection() below for collinear lines.
# (p0,p1) defines line 0, (p2,p3) defines line 1.
######

# Result functions for possible states
def lines_dont_coincide(p0,p1,p2,p3):
    return (3, None)

def lines_0_fully_included_in_1(p0, p1, p2, p3):
    return (2, num.array([p0, p1]))

def lines_1_fully_included_in_0(p0, p1, p2, p3):
    return (2, num.array([p2, p3]))

def lines_overlap_same_direction(p0, p1, p2, p3):
    return (2, num.array([p0, p3]))

def lines_overlap_same_direction2(p0, p1, p2, p3):
    return (2, num.array([p2, p1]))

def lines_overlap_opposite_direction(p0, p1, p2, p3):
    return (2, num.array([p0, p2]))

def lines_overlap_opposite_direction2(p0, p1, p2, p3):
    return (2, num.array([p3, p1]))

# This function called when an impossible state is found
def lines_error(p1, p2, p3, p4):
    msg = ('INTERNAL ERROR: p1=%s, p2=%s, p3=%s, p4=%s'
           % (str(p1), str(p2), str(p3), str(p4)))
    raise RuntimeError, msg

# Mapping to possible states for line intersection
#
#                 0s1    0e1    1s0    1e0   # line 0 starts on 1, 0 ends 1,
#                                                   1 starts 0, 1 ends 0
collinear_result = { (False, False, False, False): lines_dont_coincide,
                     (False, False, False, True ): lines_error,
                     (False, False, True,  False): lines_error,
                     (False, False, True,  True ): lines_1_fully_included_in_0,
                     (False, True,  False, False): lines_error,
                     (False, True,  False, True ): lines_overlap_opposite_direction2,
                     (False, True,  True,  False): lines_overlap_same_direction2,
                     (False, True,  True,  True ): lines_1_fully_included_in_0,
                     (True,  False, False, False): lines_error,
                     (True,  False, False, True ): lines_overlap_same_direction,
                     (True,  False, True,  False): lines_overlap_opposite_direction,
                     (True,  False, True,  True ): lines_1_fully_included_in_0,
                     (True,  True,  False, False): lines_0_fully_included_in_1,
                     (True,  True,  False, True ): lines_0_fully_included_in_1,
                     (True,  True,  True,  False): lines_0_fully_included_in_1,
                     (True,  True,  True,  True ): lines_0_fully_included_in_1}

def intersection(line0, line1, rtol=1.0e-5, atol=1.0e-8):
    """Returns intersecting point between two line segments.

    However, if parallel lines coincide partly (i.e. share a common segment),
    the line segment where lines coincide is returned

    Inputs:
        line0, line1: Each defined by two end points as in: [[x0, y0], [x1, y1]]
                      A line can also be a 2x2 numpy array with each row
                      corresponding to a point.

    Output:
        status, value - where status and value is interpreted as follows:
        status == 0: no intersection, value set to None.
        status == 1: intersection point found and returned in value as [x,y].
        status == 2: Collinear overlapping lines found.
                     Value takes the form [[x0,y0], [x1,y1]].
        status == 3: Collinear non-overlapping lines. Value set to None.
        status == 4: Lines are parallel. Value set to None.
    """

    # FIXME (Ole): Write this in C

    line0 = ensure_numeric(line0, num.float)
    line1 = ensure_numeric(line1, num.float)

    x0 = line0[0,0]; y0 = line0[0,1]
    x1 = line0[1,0]; y1 = line0[1,1]

    x2 = line1[0,0]; y2 = line1[0,1]
    x3 = line1[1,0]; y3 = line1[1,1]

    denom = (y3-y2)*(x1-x0) - (x3-x2)*(y1-y0)
    u0 = (x3-x2)*(y0-y2) - (y3-y2)*(x0-x2)
    u1 = (x2-x0)*(y1-y0) - (y2-y0)*(x1-x0)

    if num.allclose(denom, 0.0, rtol=rtol, atol=atol):
        # Lines are parallel - check if they are collinear
        if num.allclose([u0, u1], 0.0, rtol=rtol, atol=atol):
            # We now know that the lines are collinear
            state_tuple = (point_on_line([x0, y0], line1, rtol=rtol, atol=atol),
                           point_on_line([x1, y1], line1, rtol=rtol, atol=atol),
                           point_on_line([x2, y2], line0, rtol=rtol, atol=atol),
                           point_on_line([x3, y3], line0, rtol=rtol, atol=atol))

            return collinear_result[state_tuple]([x0,y0], [x1,y1],
                                                 [x2,y2], [x3,y3])
        else:
            # Lines are parallel but aren't collinear
            return 4, None #FIXME (Ole): Add distance here instead of None
    else:
        # Lines are not parallel, check if they intersect
        u0 = u0/denom
        u1 = u1/denom

        x = x0 + u0*(x1-x0)
        y = y0 + u0*(y1-y0)

        # Sanity check - can be removed to speed up if needed
        assert num.allclose(x, x2 + u1*(x3-x2), rtol=rtol, atol=atol)
        assert num.allclose(y, y2 + u1*(y3-y2), rtol=rtol, atol=atol)

        # Check if point found lies within given line segments
        if 0.0 <= u0 <= 1.0 and 0.0 <= u1 <= 1.0:
            # We have intersection
            return 1, num.array([x, y])
        else:
            # No intersection
            return 0, None

def is_inside_polygon_quick(point, polygon, closed=True):
    """Determine if one point is inside a polygon
    Both point and polygon are assumed to be numeric arrays or lists and
    no georeferencing etc or other checks will take place.

    As such it is faster than is_inside_polygon
    """

    # FIXME(Ole): This function isn't being used
    polygon = ensure_numeric(polygon, num.float)
    points = ensure_numeric(point, num.float) # Convert point to array of points
    points = num.ascontiguousarray(points[num.newaxis, :])
    msg = (' Function is_inside_polygon() must be invoked with one point only.\n'
           'I got %s and converted to %s' % (str(point), str(points.shape)))
    assert points.shape[0] == 1 and points.shape[1] == 2, msg

    indices = num.zeros(1, num.int)

    count = _separate_points_by_polygon(points, polygon, indices,
                                        int(closed))

    return count > 0


def is_inside_polygon(point, polygon, closed=True):
    """Determine if one point is inside a polygon

    See inside_polygon for more details
    """

    indices = inside_polygon(point, polygon, closed)

    if indices.shape[0] == 1:
        return True
    elif indices.shape[0] == 0:
        return False
    else:
        msg = 'is_inside_polygon must be invoked with one point only'
        raise msg

def inside_polygon(points, polygon, closed=True):
    """Determine points inside a polygon

       Functions inside_polygon and outside_polygon have been defined in
       terms of separate_by_polygon which will put all inside indices in
       the first part of the indices array and outside indices in the last

       See separate_points_by_polygon for documentation

       points and polygon can be a geospatial instance,
       a list or a numeric array
    """

    points = ensure_numeric(points)
    if len(points.shape) == 1:
        # Only one point was passed in. Convert to array of points
        points = num.reshape(points, (1,2))

    indices, count = separate_points_by_polygon(points, polygon,
                                                closed=closed)

    # Return indices of points inside polygon
    return indices[:count]

def is_outside_polygon(point, polygon, closed=True,
                       points_geo_ref=None, polygon_geo_ref=None):
    """Determine if one point is outside a polygon

    See outside_polygon for more details
    """

    indices = outside_polygon(point, polygon, closed)

    if indices.shape[0] == 1:
        return True
    elif indices.shape[0] == 0:
        return False
    else:
        msg = 'is_outside_polygon must be invoked with one point only'
        raise Exception, msg

def outside_polygon(points, polygon, closed = True):
    """Determine points outside a polygon

       Functions inside_polygon and outside_polygon have been defined in
       terms of separate_by_polygon which will put all inside indices in
       the first part of the indices array and outside indices in the last

       See separate_points_by_polygon for documentation
    """

    try:
        points = ensure_numeric(points, num.float)
    except NameError, e:
        raise NameError, e
    except:
        msg = 'Points could not be converted to numeric array'
        raise Exception, msg

    try:
        polygon = ensure_numeric(polygon, num.float)
    except NameError, e:
        raise NameError, e
    except:
        msg = 'Polygon could not be converted to numeric array'
        raise Exception, msg

    if len(points.shape) == 1:
        # Only one point was passed in. Convert to array of points
        points = num.reshape(points, (1,2))

    indices, count = separate_points_by_polygon(points, polygon,
                                                closed=closed)

    # Return indices of points outside polygon
    if count == len(indices):
        # No points are outside
        return num.array([])
    else:
        return indices[count:][::-1]  #return reversed

def in_and_outside_polygon(points, polygon, closed=True):
    """Separate a list of points into two sets inside and outside a polygon

    Input
        points: (tuple, list or array) of coordinates
        polygon: Set of points defining the polygon
        closed: Set to True if points on boundary are considered 'inside' polygon

    Output
        inside: Array of points inside the polygon
        outside: Array of points outside the polygon

    See separate_points_by_polygon for more documentation
    """

    try:
        points = ensure_numeric(points, num.float)
    except NameError, e:
        raise NameError, e
    except:
        msg = 'Points could not be converted to numeric array'
        raise Exception, msg

    try:
        polygon = ensure_numeric(polygon, num.float)
    except NameError, e:
        raise NameError, e
    except:
        msg = 'Polygon could not be converted to numeric array'
        raise Exception, msg

    if len(points.shape) == 1:
        # Only one point was passed in. Convert to array of points
        points = num.reshape(points, (1,2))

    indices, count = separate_points_by_polygon(points, polygon,
                                                closed=closed)

    # Returns indices of points inside and indices of points outside
    # the polygon
    if count == len(indices):
        # No points are outside
        return indices[:count],[]
    else:
        return  indices[:count], indices[count:][::-1]  #return reversed


def polygon_area(input_polygon):
    """ Determine area of arbitrary polygon.

    Input
        input_polygon: list or Nx2 array of points defining the polygon

    Output
        scalar value for the polygon area

    Reference:     http://mathworld.wolfram.com/PolygonArea.html
    """

    # Move polygon to origin (0,0) to avoid rounding errors
    # This makes a copy of the polygon to avoid destroying it
    input_polygon = ensure_numeric(input_polygon)
    min_x = min(input_polygon[:,0])
    min_y = min(input_polygon[:,1])
    polygon = input_polygon - [min_x, min_y]

    # Compute area
    n = len(polygon)
    poly_area = 0.0

    for i in range(n):
        pti = polygon[i]
        if i == n-1:
            pt1 = polygon[0]
        else:
            pt1 = polygon[i+1]
        xi = pti[0]
        yi1 = pt1[1]
        xi1 = pt1[0]
        yi = pti[1]
        poly_area += xi*yi1 - xi1*yi

    return abs(poly_area/2)

class Polygon_function:
    """Create callable object f: x,y -> z, where a,y,z are vectors and
    where f will return different values depending on whether x,y belongs
    to specified polygons.

    To instantiate:

       Polygon_function(polygons)

    where polygons is a list of tuples of the form

      [ (P0, v0), (P1, v1), ...]

      with Pi being lists of vertices defining polygons and vi either
      constants or functions of x,y to be applied to points with the polygon.

    The function takes an optional argument, default which is the value
    (or function) to used for points not belonging to any polygon.
    For example:

       Polygon_function(polygons, default = 0.03)

    If omitted the default value will be 0.0

    Note: If two polygons overlap, the one last in the list takes precedence

    Coordinates specified in the call are assumed to be relative to the
    origin (georeference) e.g. used by domain.
    By specifying the optional argument georeference,
    all points are made relative.
    """


    def __init__(self, regions, default=0.0):
        """Create instance of a polygon function.

        See class documentation for details
        """

        try:
            len(regions)
        except:
            msg = ('Polygon_function takes a list of pairs (polygon, value).'
                   'Got %s' % str(regions))
            raise Exception, msg

        T = regions[0]

        if isinstance(T, basestring):
            msg = ('You passed in a list of text values into polygon_function '
                   'instead of a list of pairs (polygon, value): "%s"'
                   % str(T))
            raise Exception, msg

        try:
            a = len(T)
        except:
            msg = ('Polygon_function takes a list of pairs (polygon, value). '
                   'Got %s' % str(T))
            raise Exception, msg

        msg = ('Each entry in regions have two components: (polygon, value). '
               'I got %s' % str(T))
        assert a == 2, msg

        self.default = default

        # Store polygons and their values as regions
        self.regions = []
        for polygon, value in regions:
            self.regions.append((polygon, value))

    def __call__(self, x, y):
        """Callable property of Polygon_function.

        Input
            x: List of x coordinates of points ot interest
            y: List of y coordinates of points ot interest

        Output
            z: Computed value at (x, y)
        """

        x = num.array(x, num.float)
        y = num.array(y, num.float)

        # x and y must be one-dimensional and same length
        assert len(x.shape) == 1 and len(y.shape) == 1
        N = x.shape[0]
        assert y.shape[0] == N

        points = num.ascontiguousarray(num.concatenate((x[:,num.newaxis],
                                                        y[:,num.newaxis]),
                                                       axis=1 ))

        if callable(self.default):
            z = self.default(x, y)
        else:
            z = num.ones(N, num.float) * self.default

        for polygon, value in self.regions:
            indices = inside_polygon(points, polygon)

            # FIXME: This needs to be vectorised
            if callable(value):
                for i in indices:
                    xx = num.array([x[i]])
                    yy = num.array([y[i]])
                    z[i] = value(xx, yy)[0]
            else:
                for i in indices:
                    z[i] = value

        if len(z) == 0:
            msg = ('Warning: points provided to Polygon function did not fall '
                   'within its regions in [%.2f, %.2f], y in [%.2f, %.2f]'
                   % (min(x), max(x), min(y), max(y)))
            log.critical(msg)

        return z


#------------------------------------------------------------
# Helper functions to e.g. read and write polygon information
#------------------------------------------------------------
def read_polygon(filename, delimiter=','):
    """Read points assumed to form a polygon.

    There must be exactly two numbers in each line separated by the delimiter.
    No header.
    """

    fid = open(filename)
    lines = fid.readlines()
    fid.close()
    polygon = []
    for line in lines:
        fields = line.split(delimiter)
        polygon.append([float(fields[0]), float(fields[1])])

    return polygon


def write_polygon(polygon, filename=None):
    """Write polygon to csv file.

    There will be exactly two numbers, easting and northing, in each line
    separated by a comma.

    No header.
    """

    fid = open(filename, 'w')
    for point in polygon:
        fid.write('%f, %f\n' % point)
    fid.close()


def populate_polygon(polygon, number_of_points, seed=None, exclude=None):
    """Populate given polygon with uniformly distributed points.

    Input:
       polygon - list of vertices of polygon
       number_of_points - (optional) number of points
       seed - seed for random number generator (default=None)
       exclude - list of polygons (inside main polygon) from where points
                 should be excluded

    Output:
       points - list of points inside polygon

    Examples:
       populate_polygon( [[0,0], [1,0], [1,1], [0,1]], 5 )
       will return five randomly selected points inside the unit square
    """

    from random import uniform, seed as seed_function

    seed_function(seed)

    points = []

    # Find outer extent of polygon
    max_x = min_x = polygon[0][0]
    max_y = min_y = polygon[0][1]
    for point in polygon[1:]:
        x = point[0]
        if x > max_x: max_x = x
        if x < min_x: min_x = x
        y = point[1]
        if y > max_y: max_y = y
        if y < min_y: min_y = y

    while len(points) < number_of_points:
        x = uniform(min_x, max_x)
        y = uniform(min_y, max_y)

        append = False
        if is_inside_polygon([x,y], polygon):
            append = True

            #Check exclusions
            if exclude is not None:
                for ex_poly in exclude:
                    if is_inside_polygon([x,y], ex_poly):
                        append = False

        if append is True:
            points.append([x,y])

    return points
