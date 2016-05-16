#!/usr/bin/python3
# coding=utf-8

import sys
import os
import getopt

#-------------------------------------------------------------------------------
#
#    Settings
#
STEP      = 400  # mils
PIN_LEN   = 200  # mils
FONT_SIZE = 118  # mils
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
    PinNameOffset = '80'
    DrawPinNum    = 'N'
    DrawPinName   = 'Y'
    UnitCount     = part_count
    UnitsLocked   = 'F'   # L: locked; F: free
    OptionFlag    = 'N'   # N: normal; P: power

    l = [Name, Ref, Unused, PinNameOffset, DrawPinNum, DrawPinName, UnitCount, UnitsLocked, OptionFlag]
    
    header  += join_rec(l) + os.linesep
    
    return header
   
#-------------------------------------------------------------------------------
def create_field(field, name, pos_x, pos_y, font=118, visibility='V'):
    l = ['F'+str(field), '"'+name+'"', pos_x, pos_y, str(font), 'H', visibility, 'L CNN']
    return join_rec(l) + os.linesep
 
#-------------------------------------------------------------------------------
def create_drawings(pin_count, part_count, width, font=118):

    draw  = 'DRAW' + os.linesep
    draw += 'T 0 210 -200 118 0 0 0 Конт Normal 0 C C' + os.linesep
    draw += 'T 0 1200 -200 118 0 0 0 Цепь Normal 0 C C'  + os.linesep

    pins_chunk = int(int(pin_count)/int(part_count))
    height = str(-(pins_chunk + 1)*STEP)
    
    draw += 'S 0 0 ' + width + ' ' + height +' 0 1 0 f'  + os.linesep
    draw += 'P 2 0 1 0 420 0 420 ' + height +' N'  + os.linesep

    for i in range(1,pins_chunk+1):
        y = str(-i*STEP)
        draw += 'P 2 0 0 0 0 ' + y + ' ' + width + ' ' + y + ' N'  + os.linesep

    for n in range(1, int(part_count)+1):
        for i in range(1,pins_chunk+1):
            draw += 'X ' + str(i+(n-1)*pins_chunk) + ' ' + str(i+(n-1)*pins_chunk) + ' ' + \
                     str(-PIN_LEN) + ' ' + str( -int( (STEP/2+i*STEP) ) ) + ' ' + str(PIN_LEN) + \
                     ' R ' + str(font) + ' ' + str(font) + ' ' + str(n) + ' 1 P'  + os.linesep
        
        
    draw += 'ENDDRAW' + os.linesep

    return draw
       
#-------------------------------------------------------------------------------
def create_conn(pin_count, part_count, width):
    rec  = create_header( pin_count, part_count )
    rec += create_field( field=0, name='XP', pos_x=0, pos_y=100 )
    rec += create_field( field=1, name='CONN-'+pin_count, pos_x=1000, pos_y=100 )
    rec += create_field( field=2, name='', pos_x=700, pos_y=400, visibility='I' )
    rec += create_field( field=3, name='', pos_x=700, pos_y=400, visibility='I' )
    rec += create_drawings(pin_count, part_count, width)
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
    optlist, fld = getopt.gnu_getopt(sys.argv[1:], 'n:p:w:')


    pin_count  = 0
    part_count = 1
    width      = str(WIDTH)
    for i in optlist:
        if i[0] == '-n':
            pin_count = i[1]
        elif i[0] == '-p':
            part_count = i[1]
        elif i[0] == '-z':
            width = i[i]
    
    if int(pin_count)%int(part_count):
        print('E: pin count should be multiple of part count')
        return 1
            
    create_conn(pin_count, part_count, width)
    
if __name__ == '__main__':
    main()
