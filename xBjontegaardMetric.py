#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#==============================================================================================================================================================

import math as math

try:
  import numpy
except:
  numpy = None

#==============================================================================================================================================================

class xBjontegaardMetric:
  @staticmethod
  def __bjontegaard_pchipend(h1, h2, del1, del2):    
      d = (( 2*h1+h2 ) * del1-h1*del2 ) / ( h1+h2 )
      if  ( d*del1 < 0 ) :
          d = 0
      elif  (( del1*del2 < 0 )  and  ( abs(d) > abs(3*del1) ) ) :
          d = 3*del1 
      return d

  @staticmethod
  def __bjontegaard_integral_new(rate, dist, low, high, mode="dRate"):
      if len(rate) != len(dist):  return float("nan")

      #conversion to numpy array type
      rate = numpy.array(rate)
      dist = numpy.array(dist)

      #sorting
      idx  = rate.argsort()
      rate = rate[idx]
      dist = dist[idx]
      log_rate = numpy.log10(rate)

      #print ("log_rate", log_rate)
      #print ("dist",dist)
      
      H = numpy.zeros(4)
      delta = numpy.zeros(4)
      if "dRate" in mode:            
          for i in range(0, 3):
              H[i] = dist[i + 1] - dist[i]
              delta[i] = (log_rate[i + 1] - log_rate[i]) / H[i]
      elif "dPSNR" in mode:            
          for i in range(0, 3):
              H[i] = log_rate[i + 1] - log_rate[i]
              delta[i] = (dist[i + 1] - dist[i]) / H[i]
      else:
          return None
      #print ("H", H)
      #print ("delta", delta)
     
      d = numpy.zeros(4)
      d[0] = xBjontegaardMetric.__bjontegaard_pchipend(H[0], H[1], delta[0], delta[1])
      for i in range(1, 3):
          d[i] = ( 3*H[i-1] + 3*H[i] ) / ((2*H[i]+H[i-1]) / delta[i-1] + ( H[i]+2*H[i-1]) / delta[i])
      d[3] = xBjontegaardMetric.__bjontegaard_pchipend(H[2], H[1], delta[2], delta[1])

      #print ("d", d)
      
      c = numpy.zeros(4)
      b = numpy.zeros(4)
      for i in range(0, 3):
          c[i] = ( 3 * delta[i] - 2 * d[i] - d[i + 1] )  / H[i]
          b[i] = ( d[i] - 2 * delta[i] + d[i + 1] )  /  ( H[i] * H[i] )
      #print ("c", c)
      #print ("b", b)
      # cubic function is rate(i) + s*(d(i) + s*(c(i) + s*(b(i))) where s = x - dist(i)
      # or rate(i) + s*d(i) + s*s*c(i) + s*s*s*b(i)
      # primitive is s*rate(i) + s*s*d(i)/2 + s*s*s*c(i)/3 + s*s*s*s*b(i)/4
      result = 0
      if "dRate" in mode:            
          for i in range(0, 3):
              s0 = dist[i]
              s1 = dist[i + 1]
              # clip s0 to valid range
              s0 = max(s0, low)
              s0 = min(s0, high)
              # clip s1 to valid range
              s1 = max(s1, low)
              s1 = min(s1, high)
              
              s0 = s0 - dist[i]
              s1 = s1 - dist[i]
              #print("so, s1",s0, s1)
              if  ( s1 > s0 ) :
                  result += ( s1 - s0 )  * log_rate[i]
                  result += ( s1 * s1 - s0 * s0 )  * d[i] / 2
                  result += ( s1 * s1 * s1 - s0 * s0 * s0 )  * c[i] / 3
                  result += ( s1 * s1 * s1 * s1 - s0 * s0 * s0 * s0 )  * b[i] / 4
      elif "dPSNR" in mode:            
          for i in range(0, 3):
              s0 = log_rate[i]
              s1 = log_rate[i + 1]
              # clip s0 to valid range
              s0 = max(s0, low)
              s0 = min(s0, high)
              # clip s1 to valid range
              s1 = max(s1, low)
              s1 = min(s1, high)
              
              s0 = s0 - log_rate[i]
              s1 = s1 - log_rate[i]
              #print("so, s1",s0, s1)
              if  ( s1 > s0 ) :
                  result += ( s1 - s0 )  * dist[i]
                  result += ( s1 * s1 - s0 * s0 )  * d[i] / 2
                  result += ( s1 * s1 * s1 - s0 * s0 * s0 )  * c[i] / 3
                  result += ( s1 * s1 * s1 * s1 - s0 * s0 * s0 * s0 )  * b[i] / 4
      #print ("result", result)
      return result

  @staticmethod
  def bjontegaard_integral_old(rate, dist, low, high, mode="dRate"):
      #only dRate mode supported
      if len(rate) != len(dist): return float("nan")

      #conversion to numpy array type
      rate = numpy.array(rate)
      dist = numpy.array(dist)

      #sorting
      idx = rate.argsort()
      rate = rate[idx]
      dist = dist[idx]
      log_rate = numpy.log10(rate)
      
      # Code below copy-pasted from previously provided template BJM.xla - Copyright (C) 2007 by Orange - France Telecom R&D
      # Contacts:
      #   - StŽphane Pateux, +(33)299124177, stephane.pateux@orange-ftgroup.com
      #   - Joel Jung, +(33)145295366, joelb.jung@orange-ftgroup.com

      E = numpy.zeros(4)
      F = numpy.zeros(4)
      G = numpy.zeros(4)
      H = numpy.zeros(4)
      p = numpy.zeros(4)
        
      for i in range(0, 4):
          E[i] = dist[i]
          F[i] = pow(dist[i],2)
          G[i] = pow(dist[i],3)
          H[i] = log_rate[i]
          
      DET0 = E[1] *  ( F[2] * G[3] - F[3] * G[2] )  - E[2] *  ( F[1] * G[3] - F[3] * G[1] )  + E[3] *  ( F[1] * G[2] - F[2] * G[1] )
      DET1 = - E[0] *  ( F[2] * G[3] - F[3] * G[2] )  + E[2] *  ( F[0] * G[3] - F[3] * G[0] )  - E[3] *  ( F[0] * G[2] - F[2] * G[0] )
      DET2 = E[0] *  ( F[1] * G[3] - F[3] * G[1] )  - E[1] *  ( F[0] * G[3] - F[3] * G[0] )  + E[3] *  ( F[0] * G[1] - F[1] * G[0] )
      DET3 = - E[0] *  ( F[1] * G[2] - F[2] * G[1] )  + E[1] *  ( F[0] * G[2] - F[2] * G[0] )  - E[2] *  ( F[0] * G[1] - F[1] * G[0] )
      DET = DET0 + DET1 + DET2 + DET3
      D0 = H[0] * DET0 + H[1] * DET1 + H[2] * DET2 + H[3] * DET3
      D1 = H[1] *  ( F[2] * G[3] - F[3] * G[2] )  - H[2] *  ( F[1] * G[3] - F[3] * G[1] )  + H[3] *  ( F[1] * G[2] - F[2] * G[1] )
      D1 = D1 - H[0] *  ( F[2] * G[3] - F[3] * G[2] )  + H[2] *  ( F[0] * G[3] - F[3] * G[0] )  - H[3] *  ( F[0] * G[2] - F[2] * G[0] )
      D1 = D1 + H[0] *  ( F[1] * G[3] - F[3] * G[1] )  - H[1] *  ( F[0] * G[3] - F[3] * G[0] )  + H[3] *  ( F[0] * G[1] - F[1] * G[0] )
      D1 = D1 - H[0] *  ( F[1] * G[2] - F[2] * G[1] )  + H[1] *  ( F[0] * G[2] - F[2] * G[0] )  - H[2] *  ( F[0] * G[1] - F[1] * G[0] )
      D2 = E[1] *  ( H[2] * G[3] - H[3] * G[2] )  - E[2] *  ( H[1] * G[3] - H[3] * G[1] )  + E[3] *  ( H[1] * G[2] - H[2] * G[1] )
      D2 = D2 - E[0] *  ( H[2] * G[3] - H[3] * G[2] )  + E[2] *  ( H[0] * G[3] - H[3] * G[0] )  - E[3] *  ( H[0] * G[2] - H[2] * G[0] )
      D2 = D2 + E[0] *  ( H[1] * G[3] - H[3] * G[1] )  - E[1] *  ( H[0] * G[3] - H[3] * G[0] )  + E[3] *  ( H[0] * G[1] - H[1] * G[0] )
      D2 = D2 - E[0] *  ( H[1] * G[2] - H[2] * G[1] )  + E[1] *  ( H[0] * G[2] - H[2] * G[0] )  - E[2] *  ( H[0] * G[1] - H[1] * G[0] )
      D3 = E[1] *  ( F[2] * H[3] - F[3] * H[2] )  - E[2] *  ( F[1] * H[3] - F[3] * H[1] )  + E[3] *  ( F[1] * H[2] - F[2] * H[1] )
      D3 = D3 - E[0] *  ( F[2] * H[3] - F[3] * H[2] )  + E[2] *  ( F[0] * H[3] - F[3] * H[0] )  - E[3] *  ( F[0] * H[2] - F[2] * H[0] )
      D3 = D3 + E[0] *  ( F[1] * H[3] - F[3] * H[1] )  - E[1] *  ( F[0] * H[3] - F[3] * H[0] )  + E[3] *  ( F[0] * H[1] - F[1] * H[0] )
      D3 = D3 - E[0] *  ( F[1] * H[2] - F[2] * H[1] )  + E[1] *  ( F[0] * H[2] - F[2] * H[0] )  - E[2] *  ( F[0] * H[1] - F[1] * H[0] )
      p[0] = D0 / DET
      p[1] = D1 / DET
      p[2] = D2 / DET
      p[3] = D3 / DET
      # End of copy-pasted code
      result = 0
      result = result + p[0] * high
      result = result + p[1] * high * high / 2
      result = result + p[2] * high * high * high / 3
      result = result + p[3] * high * high * high * high / 4
      result = result - p[0] * low
      result = result - p[1] * low * low / 2
      result = result - p[2] * low * low * low / 3
      result = result - p[3] * low * low * low * low / 4
      
      return result

  @staticmethod
  def bjontegaard_drate_new(rateA, distA, rateB, distB):
      #print("rateA",rateA)
      #print("rateB",rateB)
      #print("distA",distA)
      #print("distB",distB)
      minPSNR = max(min(distA), min(distB))
      maxPSNR = min(max(distA), max(distB))    
      vA = xBjontegaardMetric.__bjontegaard_integral_new(rateA, distA, minPSNR, maxPSNR, "dRate")
      vB = xBjontegaardMetric.__bjontegaard_integral_new(rateB, distB, minPSNR, maxPSNR, "dRate")
      avg = ( vB - vA )  /  ( maxPSNR - minPSNR )    
      dRate = pow(10, avg) - 1
      return dRate

  @staticmethod
  def bjontegaard_dpsnr_new(rateA, distA, rateB, distB):
      #print("rateA",rateA)
      #print("rateB",rateB)
      #print("distA",distA)
      #print("distB",distB)
      minRate = numpy.log10(max(min(rateA), min(rateB)))
      maxRate = numpy.log10(min(max(rateA), max(rateB)))    
      vA = xBjontegaardMetric.__bjontegaard_integral_new(rateA, distA, minRate, maxRate, "dPSNR")
      vB = xBjontegaardMetric.__bjontegaard_integral_new(rateB, distB, minRate, maxRate, "dPSNR")
      dPSNR = ( vB - vA )  /  ( maxRate - minRate )
      #print ("vA, vB, dPSNR", vA, vB, dPSNR)
      return dPSNR

  @staticmethod
  def bjontegaard_drate_old(rateA, distA, rateB, distB):
      minPSNR = max(min(distA), min(distB))
      maxPSNR = min(max(distA), max(distB))    
      vA = xBjontegaardMetric.__bjontegaard_integral_old(rateA, distA, minPSNR, maxPSNR, "dRate")
      vB = xBjontegaardMetric.__bjontegaard_integral_old(rateB, distB, minPSNR, maxPSNR, "dRate")
      avg = ( vB - vA )  /  ( maxPSNR - minPSNR )    
      dRate = pow(10, avg) - 1
      return dRate

#==============================================================================================================================================================
