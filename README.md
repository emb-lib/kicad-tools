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
| `scmgr.py`     |  Powerfull GUI application for schematic components properties management |
 

## Tools description

### Command-line tools

#### Connector generator utility
```
usage: conngen -n N [-p P] [-w W] [-f] [-l L]
    where:
      -n N - pin count
      -p P - part count
      -w W - symbol width
      -f   - make connector body filled with color
      -l L - pin length (default pin lenght is 200 mils)

```
Result: connector component file.
Note that pin count must be multiple of part count.

#### Integrated circuit generator utility
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

### Schematic Component Manager

Schematic Component Manager is powerfull GUI application that allows efficient way for processing of schematic components properties.

#### Features

   * Table representation of component list
   * Automating of component selection
       * Dedicated Selector tool
       * Using component property as selection criteria
       * Flexible rules for property matching: same, different, regular expression
       * Use any component as template for property list
   * Group editing of selected componets
       * Convenient Inspector tool
       * Add/Delete/Rename of component[s] properties
       * Property value substitutions
       * Property templates: generating property value using template
   * Customization of components table view
   * Delicate schematic files handling - preserve file sturcture over open/save operations
   * Multisheet schematic support
   * Automatic save/restore all GUI geometry properties

#### Usage
```
usage: scmgr.py [<schematic-filename>.sch]
```

#### Documentation

The program contains help documentation that explains the program features and usage. Besides, there is [wiki page](https://github.com/emb-lib/kicad-tools/wiki/KiCad-Schematic-Components-Manager-User's-Manual-(ru)) [ru] with more detail program description.

