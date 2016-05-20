# KiCad Tools

## Purpose

A set of tools to simplify and automate workflow with `KiCad`

## Contents

Currently, the following utilities are offered:

| Name           | Description |
|----------------| ------------|
| `conngen.py`   |  Connector generator utility. Allows to generate arbitrary connector component |
| `icgen.py`     |  Integrated circuit generator utility. Intended to create IC component from `YAML` description |
| `merge-lib.sh` |  Simple shell script for merging component files into library.  |
 

## Tools description

### Command-line tools

#### Connector generator utility
```
usage: conngen -n N [-p P -w W -f]
    where:
      -n N - pin count
      -p P - part count
      -w W - symbol width
      -f   - make connector body filled with color

```
Result: connector component file.
Note that pin count must be multiple of part count.

#### Integrated circuit generator 
```
usage: icgen [-o PATH -s] filename.yml
    where:
      -o PATH - path for output files (component file and component 
                documentation file), by default output files are
                placed in current directory
      -s      - silent operation
```
Result: component (`.cmp`) and component documetation (`.dcmp`) files

#### Merge library script utility
```
usage: merge-lib.sh libname
    where libname - base name for generated files
```
Result: `libname.lib` and `libname.dcm` files.
Note: the script utility merges all `.cmp` files in current directory to 
`.lib` file and all `.dcmp` files in current directory to `.dcm` file.
