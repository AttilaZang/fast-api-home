
from math import pi
import math

EARTH_REDIUS = 6367000.0


def rad(d):
    return d * pi / 180.0


def getDistance(lat1, lng1, lat2, lng2):

    radLat1 = rad(lat1)
    radLat2 = rad(lat2)
    diff_lat = radLat1 - radLat2
    diff_lng = rad(lng1) - rad(lng2)
    s = 2 * math.asin(math.sqrt(
        math.pow(math.sin(diff_lat / 2), 2) + math.cos(radLat1) * math.cos(radLat2) * math.pow(math.sin(diff_lng / 2),
                                                                                               2)))
    s = s * EARTH_REDIUS
    return s


if __name__ == '__main__':
    lat1 = 39.904939
    lng1 = 116.250837
    lat2 = 39.90493968384600
    lng2 = 116.25083798970900

    s = getDistance(lat1, lng1, lat2, lng2)
    print(s)
