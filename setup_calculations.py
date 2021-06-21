#!/usr/bin/python3

import argparse
import os
import subprocess
import sys
from datetime import date
import time
import configparser
import shutil

#setup files
def setup_files(new_dirpath, working_directory, qm_settings, qmmm_settings, path_settings, mm_settings, grofile, topfile, jobname):
    grofilepath = os.path.join(working_directory, grofile)
    topfilepath = os.path.join(working_directory, topfile)
    shutil.copy(grofilepath, new_dirpath)
    shutil.copy(topfilepath, new_dirpath)
    #create pathfile
    pathfile = os.path.join(new_dirpath, "path.dat")
    os.mknod(pathfile)
    #write qm info to qmfile
    with open(pathfile, 'w') as path_file:
        for i in path_settings:    
            line = i[0] + '=' + i[1] + '\n'
            path_file.write(line)
    #create QM.dat
    qmfile = os.path.join(new_dirpath, "qm.dat")
    os.mknod(qmfile)
    #write qm info to qmfile
    with open(qmfile, 'w') as qm_file:
        for i in qm_settings:    
            line = i[0] + '=' + i[1] + '\n'
            qm_file.write(line)
    #create MM.dat
    mmfile = os.path.join(new_dirpath, "mm.dat")
    os.mknod(mmfile)
    with open(mmfile, 'w') as mm_file:
        for i in mm_settings:    
            line = i[0] + '=' + i[1] + '\n'
            mm_file.write(line)
    #create QMMM.dat
    qmmmfile = os.path.join(new_dirpath, "qmmm.dat")
    os.mknod(qmmmfile)
    qmmm_settings.insert(0, jobname)
    with open(qmmmfile, 'w') as qmmm_file:
        for id, i in enumerate(qmmm_settings):
            if id == 0:
                line = 'jobname=' + i + '\n'
                qmmm_file.write(line)
                continue    
            line = i[0] + '=' + i[1] + '\n'
            qmmm_file.write(line)
    #create START.SH
    startfile = os.path.join(new_dirpath, "start.sh")
    os.mknod(startfile)
    return startfile

def create_start_sh(gmx2qmmm_args, startpath, GMXLIB, nodes=1, ntasks=32, time='1=00:00:00', jobname='samplename', mailuser='n.smith@fu-berlin.de', memory='4096'):
    from itertools import chain
    ifile = open(startpath, 'w')
    interpreter = "#!/bin/bash \n"
    #change for different DIRS
    gmx2qmmm_dir = 'gmx2qmmm_location'
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

def create_qm_active(grofile, resid, new_dirpath):
    #check vmd exists
    print("Checking for VMD...")
    try:
        devnull = open(os.devnull)
        subprocess.Popen(["which", "vmd"], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print("VMD does not exist on this machine!")
            print("exiting...")
            sys.exit()
    else:
        print("Found.")
    finally:
        devnull.close()

    #atom selects
    qm_atomselect = "\"((same residue as (within 3 of (resid " +  resid + " and name MG))) or resid " + resid + ") and not (name C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C20 H2 1H4 2H4 3H4 1H5 2H5 1H6 2H6 1H7 2H7 H8 1H9 2H9 3H9 1H10 2H10 1H11 2H11 1H12 2H12 H13 1H14 2H14 3H14 1H15 2H15 1H16 2H16 1H17 2H17 H18 1H19 2H19 3H19 1H20 2H20 3H20 and resid "+ resid + ")\""
    active_atomselect = "\"same residue as within 3 of ((same residue as (within 3 of (resid " + resid + " and name MG)) or resid " + resid + ") and not (name C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C20 H2 1H4 2H4 3H4 1H5 2H5 1H6 2H6 1H7 2H7 H8 1H9 2H9 3H9 1H10 2H10 1H11 2H11 1H12 2H12 H13 1H14 2H14 3H14 1H15 2H15 1H16 2H16 1H17 2H17 H18 1H19 2H19 3H19 1H20 2H20 3H20 and resid " + resid + "))\""

    indexpath = os.path.join(new_dirpath, "index.ndx")
    activepath = os.path.join(new_dirpath, "active.ndx")

    #write new vmd scripts to file:
    tcl_line1 = "mol new " + grofile + " type gro first 0 last -1 step 1 filebonds 1 \\\n"
    tcl_line2 = "\t\tautobonds 1 waitfor all\n"
    #remember to write a blank line
    #QM
    QM_tcl_line4 = "set sel1 [atomselect top " + qm_atomselect + "]\n"
    qm_tcl_line5 = "set ch1 [open " + indexpath + " w]\n"
    #Active
    active_tcl_line4 = "set sel1 [atomselect top " + active_atomselect + "]\n"
    active_tcl_line5 = "set ch1 [open " + activepath + " w]\n"

    tcl_line6 = "puts $ch1 \"[$sel1 get serial]\"\n"
    tcl_line7 = "close $ch1\n"
    tcl_line8 = "exit\n"

    #check if scripts already exist:
    qm_tcl_filepath = os.path.join(new_dirpath, "get_QM_atoms.tcl")
    active_tcl_filepath = os.path.join(new_dirpath, "get_active_atoms.tcl")

    if os.path.isfile(qm_tcl_filepath):
        print("qm .tcl file already exists!")
        print("Exiting program as no wish to delete created scripts...")
        sys.exit()

    if os.path.isfile(active_tcl_filepath):
        print("active .tcl file already exists!")
        print("Exiting program as no wish to delete created scripts...")
        sys.exit()

    #write qm script
    qm_filelines = list((tcl_line1, tcl_line2, "\n", QM_tcl_line4, qm_tcl_line5, tcl_line6, tcl_line7, "\n", tcl_line8))
    qm_vmdscript = open(qm_tcl_filepath, 'w')
    qm_vmdscript.writelines(qm_filelines)
    qm_vmdscript.close()

    #write active script
    active_filelines = list((tcl_line1, tcl_line2, "\n", active_tcl_line4, active_tcl_line5, tcl_line6, tcl_line7, "\n", tcl_line8))
    active_vmdscript = open(active_tcl_filepath, 'w')
    active_vmdscript.writelines(active_filelines)
    active_vmdscript.close()

    #run vmd script to obtain active and index atoms:
    

    #qm
    subprocess.call(['vmd', '-dispdev', 'text' ,'-e', qm_tcl_filepath])
    print("Checking for index.ndx...")
    if os.path.isfile(indexpath):
        print("index.ndx created successfully")
    else:
        print("index file not created for some reason.")
        print("Exiting...")
        sys.exit()

    #active
    subprocess.call(['vmd', '-dispdev', 'text' ,'-e', active_tcl_filepath])

    print("Checking for active.ndx...")
    if os.path.isfile(activepath):
        print("active.ndx created successfully")
    else:
        print("active file not created for some reason.")
        print("Exiting...")
        sys.exit()

    #delete scripts created
    subprocess.call(['rm', qm_tcl_filepath])
    subprocess.call(['rm', active_tcl_filepath])

def main():
    today = date.today()
    dd_mm_yy = today.strftime("%d_%m_%Y")
    function_description = "Creates folder with required files to run calculations. Will set up start.sh, active.ndx, index.ndx, qm.dat, qmmm.dat, path.dat"
    #obtain the directory of the script
    working_directory = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description=function_description)
    parser.add_argument('-jobname', nargs='?', help='Job name of calculation', required=True)
    parser.add_argument('-resid', nargs='?', help='RESID to be optimised', required=True)
    parser.add_argument('-gro', nargs='?', help='Grofile used for the calculation', required=True)
    parser.add_argument('-top', nargs='?', help='Topology file used for the calculation', required=True)
    parser.add_argument('-settings', nargs='?', help='settings.ini file to determine qm.dat, qmmm.dat, path.dat, start.sh files', required=True)

    args = parser.parse_args()

    print("Today's date is: " + dd_mm_yy)
    #directory_name = args.dirname
    jobname = args.jobname
    resid = args.resid
    grofile = args.gro
    topfile = args.top
    settings_file =  os.path.join(working_directory, args.settings)
    config = configparser.ConfigParser()
    config.read(settings_file)
    qm_settings = config.items('QM_SETTINGS')
    qmmm_settings = config.items('QMMM_SETTINGS')
    path_settings = config.items('PATH_SETTINGS')
    mm_settings = config.items('MM_SETTINGS')

    #new folder
    new_dirname = dd_mm_yy + "_" + jobname + "_" + resid
    new_dirpath = os.path.join(working_directory, new_dirname)
    try:
        os.mkdir(new_dirpath)
    except FileExistsError:
        try:
            os.rmdir(new_dirpath)
        except OSError:
            print("Directory is not empty!\nPlease check contents then delete")
            sys.exit()
    set_gmx2qmmm_args = "-c " + grofile + " -p " + topfile +  ' -act ' + "active.ndx " + '-n ' + "index.ndx " + '-path ' + "path.dat " + "\n"
    
    startfile = setup_files(new_dirname, working_directory, qm_settings, qmmm_settings, path_settings, mm_settings, grofile, topfile, jobname)
    create_start_sh(set_gmx2qmmm_args, startfile, config.get('START_SH_SETTINGS', 'gmxlib'), config.get('START_SH_SETTINGS', 'nodes'), config.get('START_SH_SETTINGS', 'ntasks'), config.get('START_SH_SETTINGS', 'time'), jobname)
    create_qm_active(grofile, resid, new_dirpath)


if __name__ == "__main__":
    main()