#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 08:33:13 2020

@author: root
"""
import sys
import numpy as np
import pandas as pd


def parse2411(lines):
    xyz = np.zeros((len(lines)/2, 3))
    idx = np.arange(1, (len(lines)/2+1))
    for i, l in enumerate(lines[::2]):
        k = 2*i+1
        ll = lines[k]
        xyz[i] = np.float64(ll.split())
    d = pd.DataFrame(data=xyz, index=idx, columns=["X", "Y", "Z"])
    return d


class unvMesh:
    def __init__(self, fileName):
        f = open(fileName, "r")
        self.fileName = fileName
        self.lines = f.readlines()
        self.Parser = {"2411": self.parse2411,
                       "2412": self.parse2412,
                       "164": self.parse164,
                       "2420": self.parse2420,
                       "2467": self.parse2467}
        self.getGroups()

    def getGroups(self):
        grps = []
        for i, l in enumerate(self.lines[:]):
            e = l.replace(" ", "").replace("\t", "").replace("\n", "")
            if "-1" == e:
                grps.append(i)
        self.grps = grps
        lineGroups = {}
        for start, end in zip(self.grps[::2], self.grps[1::2]):
            startLine = self.lines[start+1].replace(" ", "").\
                        replace("\t", "").replace("\n", "")
            lineGroups[startLine] = self.lines[start+2:end]
        self.lineGroups = lineGroups
        for l in lineGroups.keys():
            if l in self.Parser.keys():
                self.Parser[l](lineGroups[l])

    def parse2411(self, lines):
        xyz = np.zeros((int(len(lines)/2), 3))
        idx = np.arange(1, (len(lines)/2+1), dtype=int)
        for i, l in enumerate(lines[::2]):
            k = 2*i+1
            ll = lines[k]
            xyz[i] = np.float64(ll.split())
        d = pd.DataFrame(data=xyz, index=idx, columns=["X", "Y", "Z"])
        self.dxyz = d

    def parse164(self, lines):
        self.UnitsLine = lines

    def parse2420(self, lines):
        self.CoordLine = lines

    def parse2412(self, lines):
        elements = {}
        i = 0
        elem2d = 0
        elem3d = 0
        while i < len(lines):
            qq = lines[i].split()
            if int(qq[1]) == 11:  # Linear Element
                elts = np.int32(lines[i+2].split())
                eltID = int(qq[0])
                elements[eltID] = [3, elts]  # Lin
                i += 3
                elem2d += 1
            elif int(qq[1]) == 41:
                elts = np.int32(lines[i+1].split())
                eltID = int(qq[0])
                elements[eltID] = [5, elts]  # Tri
                i += 2
                elem2d += 1

            elif int(qq[1]) == 44:
                elts = np.int32(lines[i+1].split())
                eltID = int(qq[0])
                elements[eltID] = [9, elts]  # Quad
                i += 2
                elem2d += 1

            elif int(qq[1]) == 112:
                # print(qq)
                elts = np.int32(lines[i+1].split())
                eltID = int(qq[0])
                elements[eltID] = [13, elts]  # Prism
                i += 2
                elem3d += 1

            elif int(qq[1]) == 111:
                # print(qq)
                elts = np.int32(lines[i+1].split())
                eltID = int(qq[0])
                elements[eltID] = [10, elts]  # Tets
                i += 2
                elem3d += 1
        self.elem2d = elem2d
        self.elem3d = elem3d
        self.elements = elements

    def parse2467(self, lines):
        groups = {}
        i = 1
        while i < len(lines):
            q = lines[i].split()
            if len(q) == 1:
                key = q[0]
                print(key)
                test = True
                elements = []
                while test:
                    i += 1
                    if i < len(lines):
                        if len(lines[i].split()) > 1:
                            q = lines[i].split()
                            if q[-1] == "0":
                                if len(q) > 4:
                                    elements += [int(q[1]), int(q[5])]
                                else:
                                    elements += [int(q[1])]
                            else:
                                test = False
                            # if i <len(lines):
                            #    q = lines[i].split()
                            #    test = q[0]=="8"
                            # else:
                            #    test = False
                        else:
                            test = False
                    else:
                        test = False
                groups[key] = elements
            i += 1
        print(groups.keys())
        self.groups = groups

    def dump_su2(self):
        txt = "NDIME= 3\n"

        #  txt += "NELEM= %d\n"%(len(self.elements.keys()))
        elemText = "NELEM= %d\n" % (self.elem3d)
        k = 0
        for e in sorted(self.elements.keys()):
            if self.elements[e][0] > 9:
                line = "%d\t" % (self.elements[e][0])
                for el in self.elements[e][1]:
                    line += "%d\t" % (el-1)
                line += "%d\n" % (k)
                k += 1
                elemText += line
        txt += elemText
        self.elemText = elemText

        pointsText = "NPOIN= %d\n" % (len(self.dxyz.index))
        for idx in self.dxyz.index:
            line = ""
            for k in ["X", "Y", "Z"]:
                line += "%15.14e\t" % self.dxyz[k][idx]
            line += "%d\n" % (idx-1)
            pointsText += line
        txt += pointsText
        self.pointsText = pointsText
        markText = "NMARK= %d\n" % len(self.groups.keys())
        for grp in self.groups.keys():
            markText += "MARKER_TAG= %s\n" % grp
            markText += "MARKER_ELEMS= %d\n" % len(self.groups[grp])
            for k in sorted(self.groups[grp]):
                basic_element = self.elements[k]
                line = "%d\t" % basic_element[0]
                for el in basic_element[1]:
                    line += "%d\t" % (el-1)
                line = line[:-1]+"\n"
                markText += line
        markText += """NPERIODIC= 1
PERIODIC_INDEX= 0
0.000000000000000e+00   0.000000000000000e+00   0.000000000000000e+00
0.000000000000000e+00   0.000000000000000e+00   0.000000000000000e+00
0.000000000000000e+00   0.000000000000000e+00   0.000000000000000e+00
"""
        txt += markText
        self.markText = markText

        newName = self.fileName+".su2"
        f = open(newName, "w")
        f.write(txt)
        f.close()


fileName = r"/home/philippe/SW/SU2/Learning/Duct/Mesh_1.unv"
fileName = r"/home/philippe/SW/SU2/Learning/BuildingCFD/BuildingVF_SU2.unv"
fileName = r"/home/philippe/SW/SU2/Learning/WhirlPool/Mesh_1.unv"
fileName = r"/home/philippe/SW/SU2/Learning/BuildingCFD/FarfieldBuilding.unv"
fileName = r"/home/philippe/SW/SU2/Learning/House/Mesh_1.unv"

print(sys.argv)

if len(sys.argv) < 2:
    e = unvMesh(fileName)
    e.dump_su2()
    f = open(fileName+".mark", "w")
    f.write(e.markText)
    f.close()
else:  # e = unvMesh(fileName)
    fileName = sys.argv[-1]
    e = unvMesh(fileName)
    e.dump_su2()
