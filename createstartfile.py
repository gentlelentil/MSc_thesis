#!/usr/bin/python3

import argparse
import os
import subprocess
import sys
from datetime import date
import time
import configparser

def create_start_sh(gmx2qmmm_args, startpath, GMXLIB, nodes=1, ntasks=32, time='1=00:00:00', jobname='samplename', mailuser='n.smith@fu-berlin.de', memory='4096'):
    from itertools import chain
    ifile = open(startpath, 'w')
    interpreter = "#!/bin/bash \n"
    #change for different DIRS
    gmx2qmmm_dir = dirname
    SBATCH = [
        '#SBATCH --mail-user=' + str(mailuser) + '\n', 
        '#SBATCH --mail-type=end\n',
        '#SBATCH --nodes=' + str(nodes) +'\n',
        '#SBATCH --ntasks=' + str(ntasks) +'\n',
        '#SBATCH --mem-per-cpu=' + str(memory) +'\n',
        '#SBATCH --time=' + time +'\n',
        '#SBATCH --qos=standard' +'\n',
        '#SBATCH --job-name=' + str(jobname) +'\n',
        '\n',
    ]
    MODULES = [
        'module load gaussian/g16_A03' +'\n',
        'module load GROMACS/2019-foss-2018b # GROMACS' +'\n',
        'module unload python' +'\n',
        'module load Python/2.7.15-foss-2018b' +'\n',
        'export GMXLIB=' + str(GMXLIB) + '\n',
    ]
    #temp directory:
    tempdir = [
        'export TMPDIR=/scratch/$USER/tmp_calc/tmp.$SLURM_JOBID # tmp_calc should exist' +'\n',
        'if [ -d $TMPDIR ]; then' +'\n',
        '\techo "$TMPDIR exists; double job start; exit"' +'\n',
        '\texit 1' +'\n',
        'fi' +'\n',
        'mkdir -p $TMPDIR',
        '\n',
    ]
    project = [
        'export PROJECT=`pwd`' + '\n',
        'set -e' + '\n',
        '\n',
    ]
    #copy to temp dir
    copylines = [
        'cp -r -p $PROJECT/* $TMPDIR' +'\n',
        'rm $TMPDIR/slurm-*.out' +'\n',
        'cd $TMPDIR' +'\n',
        '\n',
    ]
    runcalc = 'python2.7 ' + gmx2qmmm_dir + " " + gmx2qmmm_args
    remove = 'mv * $PROJECT\n'
    ifile.write(interpreter)
    filelines = list(chain(SBATCH, MODULES, tempdir, project, copylines))
    ifile.writelines(filelines)
    ifile.write(runcalc)
    ifile.write(remove)
    ifile.close()

def main():
    today = date.today()
    dd_mm_yy = today.strftime("%d_%m_%Y")
    function_description = "Creates folder with required files to run calculations. Will set up start.sh, active.ndx, index.ndx, qm.dat, qmmm.dat, path.dat"
    working_directory = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description=function_description)
    parser.add_argument('-jobname', nargs='?', help='Job name of calculation', required=True)
    parser.add_argument('-resid', nargs='?', help='RESID to be optimised', required=True)
    parser.add_argument('-settings', nargs='?', help='settings.ini file to determine qm.dat, qmmm.dat, path.dat, start.sh files', required=True)
    parser.add_argument('-dirname', nargs='?', help='existing dirname', required=True)

    args = parser.parse_args()

    print("Today's date is: " + dd_mm_yy)
    jobname = args.jobname
    resid = args.resid
    dirname = args.dirname
    settings_file =  os.path.join(working_directory, args.settings)
    config = configparser.ConfigParser()
    config.read(settings_file)
    path_settings = config.items('PATH_SETTINGS')

    #new folder
    new_dirname = dirname
    new_dirpath = os.path.join(working_directory, new_dirname)
    startfile = os.path.join(new_dirpath, "start.sh")
    os.mknod(startfile)
    set_gmx2qmmm_args = "-c " + grofile + " -p " + topfile +  ' -act ' + "active_" + resid + ".ndx" + '-n ' + "index_" + resid + ".ndx " + '-path ' + "path.dat " + "\n"
    
    create_start_sh(set_gmx2qmmm_args, startfile, config.get('START_SH_SETTINGS', 'gmxlib'), config.get('START_SH_SETTINGS', 'nodes'), config.get('START_SH_SETTINGS', 'ntasks'), config.get('START_SH_SETTINGS', 'time'), jobname)


if __name__ == "__main__":
    main()