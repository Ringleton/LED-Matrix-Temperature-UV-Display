#   The following was code from http://github.com/bahamas10/ryb/blob/gh-pages/js/RXB.js#L252-L330
#     and rewritten in Python

#   It converts the RYB color wheel to RGB
#   The RYB color wheel provides a much more varied rainbow effect.

#   * ryb2rgb, the motherload, convert a RYB array to RGB
#   *
#   * @param ryb   {array} RYB values in the form of [0, 255, 0]
#   * @param limit {int}   [optional] max value of the color, defaults to 255
#   * @param magic {array} An array of magic colors to use in the color space interpolation
#   *
#   * returns an array of the RGB values

import math

MAGIC_COLORS =[1,1,1],[1,1,0],[1,0,0],[1,0.5,0],[0.163,0.373,0.6],[0.0,0.66,0.2],[0.5,0.0,0.5],[0.2,0.094,0.0]

def cubicInt(t, A, B):
      weight = t * t * (3 - 2 * t)
      return A + weight * (B - A)

def getR(iR, iY, iB, magic):
      magic = MAGIC_COLORS
      # red
      x0 = cubicInt(iB, magic[0][0], magic[4][0])
      x1 = cubicInt(iB, magic[1][0], magic[5][0])
      x2 = cubicInt(iB, magic[2][0], magic[6][0])
      x3 = cubicInt(iB, magic[3][0], magic[7][0])
      y0 = cubicInt(iY, x0, x1)
      y1 = cubicInt(iY, x2, x3)
      return cubicInt(iR, y0, y1)

def getG(iR, iY, iB, magic):
      magic = MAGIC_COLORS
      # green
      x0 = cubicInt(iB, magic[0][1], magic[4][1])
      x1 = cubicInt(iB, magic[1][1], magic[5][1])
      x2 = cubicInt(iB, magic[2][1], magic[6][1])
      x3 = cubicInt(iB, magic[3][1], magic[7][1])
      y0 = cubicInt(iY, x0, x1)
      y1 = cubicInt(iY, x2, x3)
      return cubicInt(iR, y0, y1)

def getB(iR, iY, iB, magic):
      magic = MAGIC_COLORS
      # blue
      x0 = cubicInt(iB, magic[0][2], magic[4][2])
      x1 = cubicInt(iB, magic[1][2], magic[5][2])
      x2 = cubicInt(iB, magic[2][2], magic[6][2])
      x3 = cubicInt(iB, magic[3][2], magic[7][2])
      y0 = cubicInt(iY, x0, x1)
      y1 = cubicInt(iY, x2, x3)
      return cubicInt(iR, y0, y1)

def ryb2rgb(R,Y,B, limit = 255):
      limit = max(255,limit)
      magic = MAGIC_COLORS
      R = R / limit
      Y = Y / limit
      B = B / limit
      R1 = getR(R, Y, B, magic)
      G1 = getG(R, Y, B, magic)
      B1 = getB(R, Y, B, magic)
      R1 = math.ceil(R1 * limit)
      G1 = math.ceil(G1 * limit)
      B1 = math.ceil(B1 * limit)
      return (R1,G1,B1)
    