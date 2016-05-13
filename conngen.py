#!/usr/bin/python
# coding=utf-8

##
## CONN-2
##
#DEF CONN-2 XP 0 80 N Y 1 F N
#F0 "XP" 150 100 118 H V C CNN
#F1 "CONN-2" 1100 100 118 H V C CNN
#F2 "" 700 400 118 H V C CNN
#F3 "" 700 400 118 H V C CNN
#DRAW
#T 0 200 -200 118 0 0 0 Конт Normal 0 C C
#T 0 1200 -200 118 0 0 0 Цепь Normal 0 C C
#P 2 0 0 0 0 -800 2000 -800 N
#S 0 0 2000 -1200 0 1 0 f
#P 2 0 1 0 0 -400 2000 -400 N
#P 2 0 1 0 420 0 420 -1200 N
#X 1 1 -200 -600 200 R 118 118 1 1 P
#X 2 2 -200 -1000 200 R 118 118 1 1 P
#ENDDRAW
#ENDDEF

import sys
import os

if len(sys.argv) < 2:
    print 'E: pin count should be specified'
    sys.exit(1)
    
N = sys.argv[1]  # pin count

if not N.isdigit():
    print 'E: pin count is not number'
    sys.exit(1)
    
    
N = int(N)    

#-------------------------------------------------------------------------------
#
#    Header
#
header  = '#' + os.linesep
header += '# CONN-' + str(N) + os.linesep
header += '#' + os.linesep

Name   = 'CONN-' + str(N) + ' '
Ref    = 'XP '
Unused = '0 '
PinNameOffset = '80 '
DrawPinNum    = 'N '
DrawPinName   = 'Y '
UnitCount     = '1 '
UnitsLocked   = 'F '  # L: locked; F: free
OptionFlag    = 'N'   # N: normal; P: power

header  += 'DEF ' + Name + Ref + Unused + PinNameOffset + DrawPinNum + DrawPinName + UnitCount + UnitsLocked + OptionFlag + os.linesep

#-------------------------------------------------------------------------------
#
#    Fields
#
f0 = 'F0 "XP" 150 100 118 H V C CNN' + os.linesep
f1 = 'F1 "CONN-' + str(N) + '" 1100 100 118 H V C CNN' + os.linesep
f2 = 'F2 "" 700 400 118 H V C CNN' + os.linesep
f3 = 'F3 "" 700 400 118 H V C CNN' + os.linesep

#-------------------------------------------------------------------------------
#
#    Drawings
#
step    = 400 # mils
pin_len = 200 # mils
height = str(-(N + 1)*step)

draw  = 'DRAW' + os.linesep
draw += 'T 0 210 -200 118 0 0 0 Конт Normal 0 C C' + os.linesep
draw += 'T 0 1200 -200 118 0 0 0 Цепь Normal 0 C C'  + os.linesep
draw += 'S 0 0 2000 ' + height +' 0 1 0 f'  + os.linesep
draw += 'P 2 0 1 0 420 0 420 ' + height +' N'  + os.linesep

for i in range(1,N+1):
    y = str(-i*step)
    draw += 'P 2 0 0 0 0 ' + y + ' 2000 ' + y + ' N'  + os.linesep
    draw += 'X ' + str(i) + ' ' + str(i) + ' ' + str(-pin_len) + ' ' + str(-(200+i*step)) + ' ' + str(pin_len) + ' R 118 118 1 1 P'  + os.linesep
    
draw += 'ENDDRAW' + os.linesep

sout = header + f0 + f1 + f2 + f3 + draw + 'ENDDEF' + os.linesep
                                                                                                                  
with open('conn-' + str(N) + '.lib', 'wb') as f:
    f.write(sout) 
