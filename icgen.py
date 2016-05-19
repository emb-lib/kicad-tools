#!/usr/bin/python3
# coding=utf-8

import sys
import os
import getopt
import yaml

#-------------------------------------------------------------------------------
#
#    Settings
#
STEP      = 200  # mils
PIN_LEN   = 200  # mils
FONT_SIZE = 118  # mils

#-------------------------------------------------------------------------------
def namegen(fullpath, ext):
    basename = os.path.basename(fullpath)
    name     = os.path.splitext(basename)[0]
    return name + os.path.extsep + ext
#-------------------------------------------------------------------------------
def sections(d, pattern):
    res = []
    for i in d.keys():
        if pattern in i:
            res.append(i)
            
    return sorted(res)
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
def draw_pline(part, *vertexes):
    N    = int(len(vertexes[0])/2)
    C    = 0
    Th   = 0
    CC   = 'N'
    
    return join_rec( ['P', N, part, C, Th] + vertexes[0] + [CC] ) + os.linesep
    
#-------------------------------------------------------------------------------
def draw_line(part, x0, y0, x1, y1):
    N    = 2
    C    = 0
    Th   = 0
    CC   = 'N'

    return join_rec( ['P', N, part, C, Th, x0, y0, x1, y1, CC] ) + os.linesep

#-------------------------------------------------------------------------------
def draw_amp_symbol(part_id, capt):
    x0, y0 = capt[1:]
    vertexes = [x0, y0, x0+100, y0+50, x0, y0+100, x0, y0]
    
    return draw_pline(part_id, vertexes)
#-------------------------------------------------------------------------------
def draw_text(part_id, capt):
    text, x0, y0 = capt

    Orientation     = 0
    CommonBodyStyle = 0
    
    params = ['T', Orientation, x0, y0, FONT_SIZE, 0, part_id, CommonBodyStyle, text, 'Normal 0 C C']
    
    return join_rec( params) + os.linesep
#-------------------------------------------------------------------------------
def create_header(ic):
    
    header  = '#' + os.linesep
    header += '# ' + ic['Name'] + os.linesep
    header += '#' + os.linesep

    Name   = 'DEF ' + ic['Name'] 
    Ref    = ic['Ref']
    Unused = '0'
    PinNameOffset = ic['PinNameOffset']
    DrawPinNum    = 'Y'
    DrawPinName   = 'Y'
    UnitCount     = len( sections(ic, 'Part') )
    UnitsLocked   = 'L'   # L: locked; F: free
    OptionFlag    = 'N'   # N: normal; P: power

    l = [Name, Ref, Unused, PinNameOffset, DrawPinNum, DrawPinName, UnitCount, UnitsLocked, OptionFlag]
    
    header  += join_rec(l) + os.linesep
    
    return header
   
#-------------------------------------------------------------------------------
def create_field(field, name, pos_x, pos_y, font=FONT_SIZE, visibility='V'):
    l = ['F'+str(field), '"'+name+'"', pos_x, pos_y, str(font), 'H', visibility, 'L CNN']
    return join_rec(l) + os.linesep
 
#-------------------------------------------------------------------------------
def draw_pin(ic, part_id, pin, org):
    if org[0] < 0:
        orient = 'R'
    else:
        orient = 'L'    
    
    C     = '0'
    Etype = 'P'  # passive
        
    org[1] -= pin[2]*STEP
    rec = join_rec( ['X', pin[1], pin[0], org[0], org[1], ic['PinLen'], orient, FONT_SIZE, FONT_SIZE, part_id, C, Etype] ) + os.linesep
    return org, rec
    
#-------------------------------------------------------------------------------
def draw_part(ic, part_name):

    part  = ic[part_name]
    vsect = part['Sections']
    
    if ic['Filled']:
        filled = 'f'
    else:
        filled = 'n'
    
    part_id = part_name[4:]
        
    pgroups = sections(part, 'PinGroup')

    h_l = 0
    h_r = 0

    for i in pgroups:
        h = 0
        pgroup = part[i]
        for p in  pgroup['Pins']:
            if len(p) != 3:
                print( 'E: invalid pin description: ' + str(p) +\
                        ', must have 3 fields but only ' + str(len(p)) + ' found' )
                print( '   Part:     ' + part_name)
                print( '   PinGroup: ' + i)
                sys.exit(2)
                
            h += p[2]
            
        h += 1 
        
        if pgroup['Side'] == 'Left':
            h_l += h
        elif pgroup['Side'] == 'Right':
            h_r += h
        else:
            print('E: invalid PinGroup Side in ' + i)
                  
    height = max(h_l, h_r)*STEP
    width  = sum(vsect)
                  
    if filled:
        f = 'f'
    else:
        f = 'n'
    
    #-----------------------------------
    #
    #   Outline
    #  
    Type = 'S'
    X0   = '0'
    Y0   = '0'
    C    = '0'
    Th   = '0'
      
    draw  = join_rec( [Type, X0, Y0, width, -height, part_id, C, Th, filled] ) + os.linesep

    #-----------------------------------
    #
    #   Caption
    #  
    capt = part['Caption']
    if capt:
        if capt[0] == '|>':
            draw += draw_amp_symbol(part_id, capt)
        else:
            draw += draw_text(part_id, capt)
    
    #-----------------------------------
    #
    #   Vertical lines
    #  
    X = 0
    for i in range( len(vsect) - 1):
        X0   = X + vsect[i]
        Y0   = 0
        X1   = X0
        Y1   = -height
        draw += draw_line(part_id, X0, Y0, X1, Y1) 
        X = X0
                                
    #-----------------------------------
    #
    #   Pins
    #  
    sep_l_x0 = 0
    sep_l_x1 = vsect[0]
    if len(vsect) == 1:
        sep_r_x0 = 0
    elif len(vsect) == 2:
        sep_r_x0 = vsect[0]
    else:
        sep_r_x0 = sum(vsect[:-1])
        
    
    pin_org_l = [ -int(ic['PinLen']), 0]
    pin_org_r = [ width + int(ic['PinLen']), 0]
    for idx, pg_name in enumerate(pgroups, start=1):
        pgroup = part[pg_name]
        if pgroup['Side'] == 'Left':
            for p in pgroup['Pins']:
                pin_org_l, pin_rec = draw_pin(ic, part_id, p, pin_org_l)
                draw += pin_rec
        
            pin_org_l[1] += -STEP
            if pgroup['Sep']:
                draw += draw_line(part_id, sep_l_x0, pin_org_l[1], sep_l_x1, pin_org_l[1])        
        
        else:
            for p in pgroup['Pins']:
                pin_org_r, pin_rec = draw_pin(ic, part_id, p, pin_org_r)
                draw += pin_rec

            pin_org_r[1] += -STEP
            if pgroup['Sep']:
                draw += draw_line(part_id, sep_r_x0, pin_org_r[1], width, pin_org_r[1])
                
    return draw
    
#-------------------------------------------------------------------------------
def create_drawings(ic):
        
    parts = sections(ic, 'Part')
    
    draw  = 'DRAW' + os.linesep
    
    for i in parts:
        draw += draw_part(ic, i)

    draw += 'ENDDRAW' + os.linesep        
    return draw
#-------------------------------------------------------------------------------
def check_cmp_params(ic):
    
    params = ['Name', 'Ref', 'PinLen', 'PinNameOffset', 'Filled']
    
    success = True
    for i in params:
        if not i in ic.keys():
            print('E: component description has no "' + i + '" parameter')
            success = False
            
    parts = sections(ic, "Part")
    part_params = ['Caption', 'Sections']
    for part_name in parts:
        part = ic[part_name]
        for p in part_params:
            if not p in part.keys():
                print('E: "' + part_name + '" part description has no "' + p + '" parameter')
                success = False
           
        sect_count = len(part['Sections'])             
        if sect_count < 1 or sect_count > 3:
            print('E: "' + part_name + '" part has invalid sections count: ' + str(sect_count) + ' (must be 1..3)')
            success = False
            
        pgroups = sections(part, 'PinGroup')
        pgroup_params = ['Side', 'Sep', 'Pins']
        for pg_name in pgroups:
            pgroup = part[pg_name]
            for p in pgroup_params:
                if not p in pgroup.keys():
                    print('E: "' + pg_name + '" pin group description has no "' + p + '" parameter')
                    success = False
            
    return success

#-------------------------------------------------------------------------------
def create_cmp_desc(ic, infile, outpath):

    desc = 'Description' in ic.keys()
    kwd  = 'Keywords' in ic.keys()
    
    if not desc and not kwd:
        return
        
    dcmp  = '#' + os.linesep
    
    dcmp += '$CMP ' + ic['Name']  + os.linesep
    if desc:
        dcmp += 'D ' + ic['Description'] + os.linesep

    if kwd:
        dcmp += 'K ' + ic['Keywords'] + os.linesep
    
    dcmp += '$ENDCMP' + os.linesep
    
    cname = namegen(infile, 'dcmp')
    
    with open( os.path.join(outpath, cname), 'wb' ) as f:
        f.write( bytes(dcmp, 'UTF-8') )
    
        
#-------------------------------------------------------------------------------
def create_cmp(yml, outpath, silent):

    ic = yaml.load( open(yml) )
    
    if not check_cmp_params(ic):
        sys.exit(2)
        
    name = ic['Name']
    if 'NameOffset' in ic.keys():
        name_offset = ic['NameOffset']
    else:
        name_offset = 1000   # default offset

    rec  = create_header(ic)
    rec += create_field( field=0, name=ic['Ref'],     pos_x=0,           pos_y=100 )
    rec += create_field( field=1, name=ic['Name'],    pos_x=name_offset, pos_y=100 )
    rec += create_field( field=2, name='',            pos_x=700,         pos_y=400, visibility='I' )
    rec += create_field( field=3, name='',            pos_x=700,         pos_y=400, visibility='I' )
    rec += create_drawings(ic)
    rec += 'ENDDEF' + os.linesep

    cname = namegen(yml, 'cmp')
    if not silent:
        print('I: create component file ' + cname)
    with open( os.path.join(outpath, cname ), 'wb') as f:
        f.write( bytes(rec, 'UTF-8') )
    
    create_cmp_desc(ic, yml, outpath)
    
def main():
    #-------------------------------------------------
    #
    #    Process options
    #
    optlist, fl = getopt.gnu_getopt(sys.argv[1:], 'o:s')

    yml = fl[0]
    
    if not yml:
        print('I: usage: icgen.py [options] <filename.yml>')
        print('    where options are:')
        print('      -o: directory for output files')
        sys.exit(1)
            
    outpath = ''
    silent  = False
    for i in optlist:
        if i[0] == '-o':
            outpath = i[1]
        if i[0] == '-s':
            silent = True
            
    create_cmp(yml, outpath, silent)
    
if __name__ == '__main__':
    main()
