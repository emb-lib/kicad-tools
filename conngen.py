#!/usr/bin/python3
# coding=utf-8

#-------------------------------------------------------------------------------
#
#    Project: KiCad Tools
#    
#    Name:    Connector Symbols Generator
#   
#    Purpose: Create schematic connector symbols
#
#    Copyright (c) 2016-2017, emb-lib Project Team
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining  a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
#    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------------

import sys
import os
import getopt

#-------------------------------------------------------------------------------
#
#    Settings
#
STEP      = 400  # mils
PIN_LEN   = 200  # mils
FONT_SIZE = 100  # mils
WIDTH     = 2000 # mils

#-------------------------------------------------------------------------------
def join_rec(l):
    res = ''
    for idx, i in enumerate(l, start = 1):
        sep = ' '
        if idx == len(l):
            sep = ''
        res += str(i) + sep
        
    return res
#-------------------------------------------------------------------------------
def create_header(pin_count, part_count):
    
    header  = '#' + os.linesep
    header += '# CONN-' + pin_count + os.linesep
    header += '#' + os.linesep

    Name   = 'DEF CONN-' + pin_count 
    Ref    = 'XP'
    Unused = '0'
    if int(pin_count) < 100:
        PinNameOffset = '80'
    else:
        PinNameOffset = '70'
    DrawPinNum    = 'N'
    DrawPinName   = 'Y'
    UnitCount     = part_count
    UnitsLocked   = 'F'   # L: locked; F: free
    OptionFlag    = 'N'   # N: normal; P: power

    l = [Name, Ref, Unused, PinNameOffset, DrawPinNum, DrawPinName, UnitCount, UnitsLocked, OptionFlag]
    
    header  += join_rec(l) + os.linesep
    
    return header
   
#-------------------------------------------------------------------------------
def create_field(field, name, pos_x, pos_y, font=FONT_SIZE, visibility='V'):
    l = ['F'+str(field), '"'+name+'"', pos_x, pos_y, str(font), 'H', visibility, 'L CNN']
    return join_rec(l) + os.linesep
 
#-------------------------------------------------------------------------------
def create_drawings(pin_count, part_count, width, filled, pinlen, font=FONT_SIZE):

    if filled:
        f = 'f'
    else:
        f = 'n'
    
    if pinlen < 0:
        pinlen = PIN_LEN
            
    cir_width = int(width) - 420
    cir_pos   = str(420 + int(cir_width/2))
    draw  = 'DRAW' + os.linesep
    draw += 'T 0 210 -200 '             + str(FONT_SIZE) + ' 0 0 0 Конт Normal 0 C C' + os.linesep
    draw += 'T 0 ' + cir_pos + ' -200 ' + str(FONT_SIZE) + ' 0 0 0 Цепь Normal 0 C C' + os.linesep

    pins_chunk = int(int(pin_count)/int(part_count))
    height = str(-(pins_chunk + 1)*STEP)
    
    draw += 'S 0 0 ' + width + ' ' + height +' 0 1 0 ' + f  + os.linesep
    draw += 'P 2 0 1 0 420 0 420 ' + height +' N'  + os.linesep

    for i in range(1,pins_chunk+1):
        y = str(-i*STEP)
        draw += 'P 2 0 0 0 0 ' + y + ' ' + width + ' ' + y + ' N'  + os.linesep

    for n in range(1, int(part_count)+1):
        for i in range(1,pins_chunk+1):
            draw += 'X ' + str(i+(n-1)*pins_chunk) + ' ' + str(i+(n-1)*pins_chunk) + ' ' + \
                     str(-pinlen) + ' ' + str( -int( (STEP/2+i*STEP) ) ) + ' ' + str(pinlen) + \
                     ' R ' + str(font) + ' ' + str(font) + ' ' + str(n) + ' 1 P'  + os.linesep
        
    draw += 'ENDDRAW' + os.linesep

    return draw
       
#-------------------------------------------------------------------------------
def create_conn(pin_count, part_count, width, filled, pinlen):
    rec  = create_header( pin_count, part_count )
    rec += create_field( field=0, name='XP', pos_x=0, pos_y=100 )
    rec += create_field( field=1, name='CONN-'+pin_count, pos_x=700, pos_y=100 )
    rec += create_field( field=2, name='', pos_x=700, pos_y=400, visibility='I' )
    rec += create_field( field=3, name='', pos_x=700, pos_y=400, visibility='I' )
    rec += create_drawings(pin_count, part_count, width, filled, pinlen)
    rec += 'ENDDEF' + os.linesep

    cname = 'conn-' + pin_count + '.cmp'
    print('I: create component file ' + cname)
    with open(cname, 'wb') as f:
        f.write( bytes(rec, 'UTF-8') )
    
    
def main():
    #-------------------------------------------------
    #
    #    Process options
    #
    optlist, fld = getopt.gnu_getopt(sys.argv[1:], 'n:p:w:fl:')


    pin_count  = 0
    part_count = 1
    width      = str(WIDTH)
    filled     = False
    pinlen     = -1
    for i in optlist:
        if i[0] == '-n':
            pin_count = i[1]
        elif i[0] == '-p':
            part_count = i[1]
        elif i[0] == '-w':
            width = i[1]
        elif i[0] == '-f':
            filled = True
        elif i[0] == '-l':
            pinlen = int(i[1])
    
    if pin_count == 0:
        print('E: pin count must be specified')
        print('usage: conngen.py -n <pin-count> [-p <part-count>] [-w <width>] [-f <filled>]' + os.linesep)
        sys.exit(1)
        
    if int(pin_count)%int(part_count):
        print('E: pin count should be multiple of part count')
        sys.exit(1)
            
    create_conn(pin_count, part_count, width, filled, pinlen)
    
if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
    
