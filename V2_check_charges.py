import argparse
import os
import regex as re
import numpy as np
from datetime import datetime
import sys

def charge_duplicate_indexes(sequence, searchterm):
    start = -1
    duplicates = []
    while True:
        try:
            duplicate = sequence.index(searchterm, start + 1)
        except ValueError:
            break
        else:
            duplicates.append(duplicate)
            start = duplicate
    return duplicates

def length_a_b(coords_A, coords_B):
    """fct. calculates distance between two coordinates"""
    import numpy as np
    vectorAB = np.subtract(coords_A, coords_B)
    length = np.sqrt(np.dot(vectorAB, vectorAB))
    return length

now = datetime.now()
dd_mm_yy = now.strftime("%d_%m_%Y")
time = now.strftime("%H:%M:%S")
#argparser to select the grofile, topfile, and output file
working_dir = os.path.dirname(os.path.realpath(__file__))
parser = argparse.ArgumentParser(description='check charge numbers and radius of a topfile, return distances')
parser.add_argument('-top', nargs='?', help='topfile', required=True)
parser.add_argument('-gro', nargs='?', help='grofile', required=True)
parser.add_argument('-o', nargs='?', help='output file')

args = parser.parse_args()

#open files
print("Reading files...")
topfile = open(args.top, 'r')
grofile = open(args.gro, 'r')
outputfile = args.o
if outputfile is None:
    outputname = time + "_" + dd_mm_yy + '_output.o'
    filepath = os.path.join(working_dir, outputname)
    os.mknod(filepath)
    outputfile = filepath

output = open(outputfile, 'w')

#read files
write_toplines = topfile.readlines()
grolines = grofile.readlines()
topflag = False
print("Done.")

#create temp topfile with only atom info in:
print("Creating temporary topfile...")
tmp_topfile = time + "_" + dd_mm_yy + args.top + ".tmp"
tmppath = os.path.join(working_dir, tmp_topfile)
os.mknod(tmppath)
writeflag = False
with open(tmppath, 'w') as f:
    for i in write_toplines:
            #find line with atoms
            match = re.match(r'\[ atoms \]', i, flags=re.MULTILINE)
            if match:
                writeflag = True
            if writeflag:
                endatommatch = re.match(r'\r?\n', i, flags=re.MULTILINE)
                if endatommatch:
                    writeflag = False
                    break
                f.writelines(i)
print("Done.")
topfile.close()

tmpfile = open(tmppath, 'r')
toplines = tmpfile.readlines()

chargegroup_list = []
atomIDs = []

print("Reading chargegroups from topfile...")
for i in toplines:
    match = re.match(r'\[ atoms \]', i, flags=re.MULTILINE)
    if match:
        continue
    search = re.search(r'^(.{10})(.{7})(.{7})(.{7})(.{8})(.{9})(.{8})(.*)', i, flags=re.MULTILINE)
    chargegroup = int("".join(search.group(6).split()))
    chargegroup_list.append(chargegroup)
    atomID = int("".join(search.group(1).split()))
    atomIDs.append(atomID)
print("Done.")
CG_dup_atomIDs = []

print("Checking for duplicate chargegroups...")
for i in chargegroup_list:
    atoms = charge_duplicate_indexes(chargegroup_list, i)
    #print(atoms)
    if len(atoms) == 1:
        continue
    for i in atoms:
        if atomIDs[i] not in CG_dup_atomIDs:
            CG_dup_atomIDs.append(atomIDs[i])

print(str(len(CG_dup_atomIDs)) + " atoms found with duplicate chargegroups.")
print("Calculating distances for atoms within the same chargegroup...")
for id, i in enumerate(grolines):
    gro_CG = ""
    if id < 2:
        continue
    #groID = id + 240127 - 2
    groID = id - 1
    if groID not in CG_dup_atomIDs:
        continue
    topflag = False
    search = re.search(r'^(.{5})(.{5})(.{5})(.{5})\s*([-]*\d+\.*\d*)\s*([-]*\d+\.*\d*)\s*([-]*\d+\.*\d*)', i, flags=re.MULTILINE)
    atomtype = "".join(search.group(3).split())
    curr_x_coords = float(search.group(5)) * 10
    curr_y_coords = float(search.group(6)) * 10
    curr_z_coords = float(search.group(7)) * 10
    pos_v_INIT = np.array([curr_x_coords, curr_y_coords, curr_z_coords])
    same_chargegroup = [groID]
    residue = "".join(search.group(2).split())
    for i in toplines:
        match = re.match(r'\[ atoms \]', i, flags=re.MULTILINE)
        if match:
            topflag = True
            continue
        if topflag:
            endatommatch = re.match(r'\r?\n', i, flags=re.MULTILINE)
            if endatommatch:
                toplineflag = False
                break
            search = re.search(r'^(.{10})(.{7})(.{7})(.{7})(.{8})(.{9})(.{8})(.*)', i, flags=re.MULTILINE)
            atomID = int("".join(search.group(1).split()))
            #topatomtype = "".join(search.group(5).split())
            chargegroup = int("".join(search.group(6).split()))

            if atomID == groID:
                gro_CG = chargegroup
                txtline = "Checking atom " + str(groID) + " in grofile, with chargegroup " + str(chargegroup) + " in topfile."
                print(txtline)
                continue
            if chargegroup == gro_CG and not atomID == groID:
                same_chargegroup.append(atomID)            
    if len(same_chargegroup) == 1:
        print("Atom number: " + str(groID) + " shares no chargegroup. Continuing...")
        continue
    print("Atom number: " + str(groID) + " has " + str(len(same_chargegroup)) + " atoms with the same chargegroup.")
    print(atomtype + " Atom: " + str(groID) + " in residue: " + residue + " shares a chargegroup with: " + str("".join(str(same_chargegroup))), file=output)
    for id, i in enumerate(grolines):
        if id < 2:
            continue
        search = re.search(r'^(.{5})(.{5})(.{5})(.{5})\s*([-]*\d+\.*\d*)\s*([-]*\d+\.*\d*)\s*([-]*\d+\.*\d*)', i, flags=re.MULTILINE)
        curr_groID = id - 1
        if groID == curr_groID:
            continue
        if curr_groID in same_chargegroup:
            curr_atomtype = "".join(search.group(3).split())
            x_coords = float(search.group(5)) * 10
            y_coords = float(search.group(6)) * 10
            z_coords = float(search.group(7)) * 10
            vector = np.array([x_coords, y_coords, z_coords])
            distance = length_a_b(pos_v_INIT, vector)
            dist_txtline = "Atom: " + atomtype + " Atom: " + str(groID) + " and " + curr_atomtype + " Atom: " + str(curr_groID) + " is: " + str(distance) + " Angstroms\n"  
            output.write(dist_txtline)
    output.write('\n')
print("Done.")
print("Cleaning up files...")
if os.path.exists(tmppath):
    os.remove(tmppath)

grofile.close()
tmpfile.close()
output.close()
print("Done.")