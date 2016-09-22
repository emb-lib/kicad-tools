# coding: utf-8


import sys
import os
import shutil
import re
                   
from PyQt5.QtCore import QSettings
                  
#-------------------------------------------------------------------------------
class ComponentField:
    
    #--------------------------------------------------------------
    def __init__(self, comp, rec):

        self.InnerCode = rec[0]
        
        if self.InnerCode == '0':
            self.Name = 'Ref'
        elif self.InnerCode == '1':
            self.Name = 'Value'
        elif self.InnerCode == '2':
            self.Name = 'Footprint'
        elif self.InnerCode == '3':
            self.Name = 'DocSheet'
        else:
            self.Name = rec[11]
            
        self.Text        = rec[1]
        self.Orientation = 'Horizontal' if rec[2] == 'H' else 'Vertical'
        self.PosX        = str( int(rec[3]) - int(comp.PosX) )
        self.PosY        = str( int(rec[4]) - int(comp.PosY) )
        self.FontSize    = rec[5]
        self.Visible     = 'Yes'  if int(rec[6]) == 0 else 'No'
        self.HJustify    = 'Left' if rec[7]  == 'L' else 'Center' if rec[7] == 'C' else 'Right'
        self.VJustify    = 'Top'  if rec[8]  == 'T' else 'Center' if rec[8] == 'C' else 'Bottom'
        self.FontItalic  = 'Yes'  if rec[9]  == 'I' else 'No'
        self.FontBold    = 'Yes'  if rec[10] == 'B' else 'No'
    
    #--------------------------------------------------------------
    @classmethod
    def default(cls, comp, name, Fn = None):
        if not Fn:
            Fn = len(comp.Fields)
            
        rec = []
        rec.append( str(Fn) )
        rec.append( '~' )
        rec.append( 'H' )
        rec.append( comp.PosX )
        rec.append( comp.PosY )
        rec.append( comp.Fields[0].FontSize )
        rec.append( '0001' )
        rec.append( 'C' )
        rec.append( 'C' )
        rec.append( 'N' )
        rec.append( 'N' )
        rec.append( name )
        return cls(comp, rec)
        
   #--------------------------------------------------------------
    def dump(self):
        print('Text        : ' + self.Text)
        print('Orientation : ' + self.Orientation)
        print('X           : ' + self.PosX)
        print('Y           : ' + self.PosY)
        print('Visible     : ' + self.Visible)
        print('H Justify   : ' + self.HJustify)
        print('V Justify   : ' + self.VJustify)
        print('Font Size   : ' + self.FontSize)
        print('Font Italic : ' + self.FontItalic)
        print('Font Bold   : ' + self.FontBold)
        
    #--------------------------------------------------------------
    def dump_line(self):
        print(self.Name        + ' '*(12 - len(self.Name)) +
              self.Text[0:11]  + ' '*(12 - len(self.Text[0:11])) +
              self.Orientation + ' '*(14 - len(self.Orientation)) + 
              self.PosX        + ' '*(6  - len(self.PosX)) + 
              self.PosY        + ' '*(6  - len(self.PosY)) + 
              self.Visible     + ' '*(8  - len(self.Visible)) + 
              self.HJustify    + ' '*(9  - len(self.HJustify)) + 
              self.VJustify    + ' '*(9  - len(self.VJustify)) + 
              self.FontSize    + ' '*(7  - len(self.FontSize)) + 
              self.FontItalic  + ' '*(8  - len(self.FontItalic)) + 
              self.FontBold    + ' '*(5  - len(self.FontBold)) + 
              'F' + self.InnerCode)
        
#-------------------------------------------------------------------------------
class Component:
    
    def __init__(self, sheet = 0):
        self.Ref     = '~'
        self.LibRef = '~'
        self.Sheet   = sheet
        
    def parse_comp(self, rec):
        self.rec = rec
        r = re.search('L ([\w-]+) ([\w#]+)', rec)
        if r:
            self.LibRef, self.Ref = r.groups()
        else:
            print('E: invalid component L record, rec: "' + rec + '"')
            sys.exit(1)
           
        if not re.match( '\D+\d+',  r.group(2) ):
            print('E: schematic must be annotated before loading in Component Manager' + os.linesep*2 + rec)
            sys.exit(2)
            
        r = re.search('U (\d+) (\d+) ([\w\d]+)', rec)

        if r:
            self.PartNo, self.mm, self.Timestamp = r.groups()
        else:
            print('E: invalid component U record, rec: "' + rec + '"')
            sys.exit(1)

        r = re.search('P (\d+) (\d+)', rec)
        if r:
            self.PosX, self.PosY = r.groups()
        else:
            print('E: invalid component P record, rec: "' + rec + '"')
            sys.exit(1)
            
        cfre = re.compile('F\s+(\d+)\s+\"(.*?)\"\s+(H|V)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([LRCBT])\s+([LRCBT])([NI])([NB])\s+(?:\"(.*)\")*')
        r = re.findall(cfre, rec)
        
        r.sort(key=lambda x: int(x[0]))
        #print(r)
        
        self.Fields = []
        for i in r:
            self.Fields.append( ComponentField(self, i) )
        
        r = re.search('([ \t]+\d+\s+\d+\s+\d+\s+-*[01]\s+-*[01]\s+-*[01]\s+-*[01]\s+)', rec)
        if r:
            self.Trailer = r.groups()[0]
        else:
            print('E: invalid component trailer record, rec: "' + rec + '"')
            sys.exit(1)
         
        
#       if self.Ref == 'A1':
#           self.dump()

    #--------------------------------------------------------------
    def field(self, fname):
        for f in self.Fields:
            if fname == f.Name:
                return f
                
        return None
        
    #--------------------------------------------------------------
    def add_field(self, f):
        self.Fields.append(f)
        
    #--------------------------------------------------------------
    def remove_field(self, f):
        self.Fields.remove(f)
        
    #--------------------------------------------------------------
    def renumerate_fields(self):
        FIELD_NUM = 4
        for num, f in enumerate(self.Fields[FIELD_NUM:], start=FIELD_NUM):
            f.InnerCode = str(num)
        
    #--------------------------------------------------------------
    def property_value(self, pname):
        if hasattr(self, pname):
            return getattr(self, pname)
        else:
            f = self.field(pname)
            if f:
                return f.Text
            else:
                return None
    #--------------------------------------------------------------
    def get_str_from_pattern(self, pattern):
        subs = re.findall('\$(\w+)', pattern)

        for sub in subs:
            pval = self.property_value(sub)
            if pval:
                pattern = re.sub('\$' + sub, pval, pattern)

        return pattern
    #--------------------------------------------------------------
    def dump(self):
        if int(self.PartNo) > 1:
            part = '.' + self.PartNo
        else:
            part = ''
            
        print('===================================================================================================')
        print('Ref       : ' + self.Ref + part)
        print('LibRef    : ' + self.LibRef)
        print('X         : ' + self.PosX)
        print('Y         : ' + self.PosY)
        print('Timestump : ' + self.Timestamp)
        
        print('--------------------------------------------------------------------------------------------------')
        print('Name         Text       Orientation    X     Y   Visible  H Align  V Align  Font  Italic  Bold  ID')
        print('--------------------------------------------------------------------------------------------------')
        for f in self.Fields:
            f.dump_line()
            #f.dump()
   
        print('===================================================================================================')
        
    #--------------------------------------------------------------
    def join_rec(self, l, s = ' ', no_last_sep = True):
        res = ''
        for idx, i in enumerate(l, start = 1):
            sep = s
            if no_last_sep and idx == len(l):
                sep = ''
            res += str(i) + sep

        return res

    #--------------------------------------------------------------
    def create_cmp_rec(self):
        #print(self.Ref)
        rec_list = []
        rec_list.append('L ' + self.LibRef + ' ' + self.Ref)
        rec_list.append('U ' + self.PartNo  + ' ' + self.mm + ' ' + self.Timestamp)
        rec_list.append('P ' + self.PosX + ' ' + self.PosY)
        
        for f in self.Fields:
            frec = ['F', 
                    f.InnerCode,
                    '"' + f.Text +'"',
                    f.Orientation[0],
                    int(self.PosX) + int(f.PosX),
                    int(self.PosY) + int(f.PosY),
                    '{:<3}'.format(f.FontSize),
                    '0000' if f.Visible == 'Yes' else '0001',
                    f.HJustify[0],
                    f.VJustify[0] + ('I' if f.FontItalic == 'Yes' else 'N') + ('B' if f.FontBold == 'Yes' else 'N'),
                    '"' + f.Name + '"' if f.Name not in ['Ref', 'Value', 'Footprint', 'DocSheet'] else '']
            
            rec_list.append( self.join_rec(frec).strip() )
            
            
        pattern = '([ \t]+\d+\s+)\d+(\s+)\d+(\s+-*[01]\s+-*[01]\s+-*[01]\s+-*[01]\s+)'
        r = re.match(pattern, self.Trailer).groups()
        self.Trailer = r[0] + str(self.PosX) + r[1] + str(self.PosY) + r[2]
        
        rec_list.append(self.Trailer)
        
        rec = self.join_rec(rec_list, os.linesep)
        
        return rec
                
#-------------------------------------------------------------------------------
class ComponentManager:
    
    def __init__(self):
        pass
        
    #---------------------------------------------------------------------------
    def set_curr_file_path(self, fname):
        self.current_file_path = fname
        
    #---------------------------------------------------------------------------
    def curr_file_path(self):
        return self.current_file_path

    #---------------------------------------------------------------------------
    def read_file(self, fname):
        with open(fname, 'rb') as f:
            b = f.read()

        return b.decode()
    
    #---------------------------------------------------------------------------
    def raw_cmp_list(self, s):
        pattern = '\$Comp\s((?:.*\s)+?)\$EndComp'
        res = re.findall(pattern, s)

        return res
        
    #---------------------------------------------------------------------------
    def load_file(self, fname):
        self.sheets = [ os.path.basename(fname) ]
        self.schdata = [self.read_file(fname)]
        
        pattern = '\$Sheet\s.+\s.+\sF0.+\sF1\s\"(.+)\".+\s\$EndSheet'
        self.dirname  =   os.path.dirname(fname)
        self.sheets  +=   re.findall(pattern, self.schdata[0])
        sheets_paths  = [ os.path.join(self.dirname, filepath) for filepath in self.sheets ]
        
        for sheet in sheets_paths[1:]:
            self.schdata.append(self.read_file(sheet))
        
        Settings = QSettings('kicad-tools', 'Schematic Component Manager')
        if Settings.contains('component-ignore'):
            ipl = Settings.value('component-ignore')
        else:
            ipl = []
            
        cmp_dict = { }
        rcls = []
        for schdata in self.schdata:
            rcls.append( self.raw_cmp_list(schdata) )             # rcl - raw component list

        cmp_dict = self.create_cmp_dict( rcls, ipl )
            
        self.current_file_path = fname
        self.cmp_dict = cmp_dict
        return cmp_dict
            
    #---------------------------------------------------------------------------
    def create_cmp_dict(self, rcls, ipl):   # rcls: raw component lists; 
                                            # ipl:  ignore patterns list
        cdict = {}

        for sheet_num, rcl in enumerate(rcls):
            for i in rcl:
                cmp = Component(sheet_num)
                cmp.parse_comp(i)
                ignore = False
                for ip in ipl:
                    r = re.search(ip+'.*\d+', cmp.Ref)
                    if r:
                        ignore = True
                        continue
    
                if ignore:
                    continue
    
                if not cmp.Ref in cdict:
                    cdict[cmp.Ref] = []
    
                cdict[cmp.Ref].append(cmp)

        return cdict

    #---------------------------------------------------------------------------
    def save_file(self, fname):
        
        refs = list(self.cmp_dict.keys())
        refs.sort()
        for ref in refs:
            clist = self.cmp_dict[ref]
            if len(clist) > 1:
                for c in clist:
                    print('Sheet:', c.Sheet, 'Part:', c.PartNo)
                
            for c in clist:
                c.renumerate_fields()
                crec = c.create_cmp_rec()
                self.schdata[c.Sheet] = re.sub(re.escape(c.rec), crec, self.schdata[c.Sheet] )
                c.rec = crec
                #print(c.Ref, self.schdata[c.Sheet][311:320])
#               if c.Ref == 'A1':
#                   print(repr(c.rec))
#                   print(repr(crec))
                
        dirname  = os.path.dirname(fname)
        basename = os.path.basename(fname)
        
        namelist = [basename] + self.sheets[1:]
        
        for sheet, name in enumerate(namelist):
            print(sheet, name)
            dst_path  = os.path.join(dirname, name)
            if os.path.exists(dst_path):
                n = os.path.splitext(name)[0]
                backup_name  = n + os.path.extsep + '~'
                backup_path  = os.path.join(dirname, backup_name)
                shutil.copy(dst_path, backup_path)


            print(self.schdata[sheet][311:320])
            with open(dst_path, 'wb') as f:
                f.write(self.schdata[sheet].encode('utf-8'))
                print(dst_path, len(self.schdata[sheet].encode('utf-8')))
        
#-------------------------------------------------------------------------------
CmpMgr = ComponentManager()
#-------------------------------------------------------------------------------


