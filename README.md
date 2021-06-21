Collection of scripts I have written as part of fulfilling my MSc Thesis in computational/theoretical Chemistry

createstartfile is designed to create a start.sh file commonly used in job schedulers (in this case slurm) for the purposes of using the gmx2qmmm program

setup_calculations uses the createstartfile program entirely, alongside other functions designed to select a QM and MM region of atoms with a VMD script.

check_charges will take a grofile and a topfile as arguments, check the atoms for identical chargegroups, then return the distances between the atoms in the same chargegroups. 