#
# Compute evaluation indices for power line segmentation
# that measure difference between ground truth G and test segmentation S
# Options:
#   -tc   for TriplClust output S, which marks multiple segment
#         memberships with a semicolon like "3;1;5"
#   -v    be verbose and print debug info
#   -vv   be more verbose and write debug files *.csv of read data
#

Usage = "python3 compare_files.py <Gfile> <Sfile> [-tc] [-v[v]]"

import sys
import os
import laspy
import pandas
import numpy

import evaluate

# point coordinates are floats => for comparisons, we must round
digits = 2

# parse command line
Gfile = None
Sfile = None
opt_tc = False
opt_v = 0
for i in range(1,len(sys.argv)):
    if sys.argv[i] == "-tc":
        opt_tc = True
    elif sys.argv[i] == "-v":
        opt_v = 1
    elif sys.argv[i] == "-vv":
        opt_v = 2
    elif sys.argv[i][0] == "-":
        sys.exit(Usage)
    else:
        if Gfile is None:
            Gfile = sys.argv[i]
        elif Sfile is None:
            Sfile = sys.argv[i]
        else:
            sys.exit(Usage)
if not (os.path.exists(Gfile) and os.path.exists(Sfile)):
    sys.exit(Usage)

# read points and labels from las or csv file
def points_from_file(filename):
    # try LAS format first
    # assumption: labels stored in UserData
    try:
        points = laspy.read(filename)
        if opt_v:
            print(filename, "is LAS file")
        return(pandas.DataFrame({'x': [round(p,digits) for p in points.x],
                                 'y': [round(p,digits) for p in points.y],
                                 'z': [round(p,digits) for p in points.z],
                                 'label': points.user_data}))
    except Exception:
        pass
    # if not LAS, try CSV format
    # assumption: labels stored in fourth column
    try:
        points = pandas.read_csv(filename, usecols=[0,1,2,3])
        points.columns = ['x', 'y', 'z', 'label']
        if opt_v:
            print(filename, "is CSV file")
        return(pandas.DataFrame({'x': [round(p,2) for p in points.iloc[:,0]],
                                 'y': [round(p,2) for p in points.iloc[:,1]],
                                 'z': [round(p,2) for p in points.iloc[:,2]],
                                 'label': points.iloc[:,3]}))
    except Exception:
        sys.exit("file '" + filename + "' seems to be neither LA(S|Z) or CSV")


#
# main program
#-------------

# read from files and do evaluation
Gpoints = points_from_file(Gfile)
Spoints = points_from_file(Sfile)

if opt_v > 1:
    Gpoints.to_csv("Gdebug.csv")
    Spoints.to_csv("Sdebug.csv")

#
# match point coordinates between G and S and add None for missing S matches
#
Gdup = Gpoints.duplicated(subset=['x', 'y', 'z'])
nGdup = Gdup.sum()
Sdup = Spoints.duplicated(subset=['x', 'y', 'z'])
nSdup = Sdup.sum()
if nGdup > 0:
    print("Warning: %i duplicates found in G. Example:" % nGdup)
    print(Gpoints.iloc[Gdup.to_list().index(True),:])
    Gpoints = Gpoints.drop_duplicates(subset=['x', 'y', 'z'])
if nSdup > 0:
    print("Warning: %i duplicates found in S. Example:" % nSdup)
    print(Spoints.iloc[Sdup.to_list().index(True),:])
    Spoints = Spoints.drop_duplicates(subset=['x', 'y', 'z'])
if nGdup > 0 or nSdup > 0:
    print("Duplicates have been removed")

# left join dataframes into G and S
matching = pandas.merge(Gpoints, Spoints, 
    on=['x', 'y', 'z'], 
    how='left', 
    suffixes=('_G', '_S'),
    validate='one_to_one')
G = matching['label_G'].tolist()
S = []
for s in matching['label_S']:
    if pandas.isna(s): 
        S.append(None) 
    else: 
        S.append(s)

if opt_v > 0:
    print("type(G) = %s" % type(G))
    print("len(G) = %i" % len(G))
    print("type(G[0] = %s" % type(G[0]))
    print("type(S) = %s" % type(S))
    print("len(S) = %i" % len(S))
    print("type(S[0] = %s" % type(S[0]))
if opt_v > 1:
    matching.to_csv("Joindebug.csv")

#
# take care of multiple assignments for TriplClust
# by adding a pair for each additional assignment
#
if opt_tc:
    Gext = []
    Sext = []
    for i, Si in enumerate(S):
        if Si is not None and ";" in str(Si):
            labels = str(Si).split(";")
            S[i] = labels[0]
            Gext.extend([G[i] for x in labels[1:]])
            Sext.extend(labels[1:])
    G.extend(Gext)
    S.extend(Sext)
            
#
# report results
#
mean_iou = evaluate.meanIoU(G, S)
correct, miss, split, merge, splitmerge = evaluate.segmentation_error(G, S)
print("meanIoU:", mean_iou)
print("correct:", correct)
print("miss:", miss)
print("split:", split)
print("merge:", merge)
print("splitmerge:", splitmerge)
