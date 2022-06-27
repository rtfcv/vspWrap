# coding: utf-8
import openvsp as vsp
import json
from typing import Union, Any
import numpy as np

import os
import sys

theRealStdOut = sys.stdout
theRealStdErr = sys.stderr
devNull = open(os.devnull, 'w')

FUSELAGE='FUSELAGE'
BODYOFREVOLUTION='BODYOFREVOLUTION'
WING='WING'

def geomParmDict(geomID: str):
    parmIds = vsp.GetGeomParmIDs(geomID)
    return {
        vsp.GetParmName(theId): theId
        for theId in parmIds if vsp.ValidParm(theId)
    }


def pp(geom: str):
    geomParms = geomParmDict(geom)
    print(json.dumps(
        {key: vsp.GetParmVal(geomParms[key]) for key in geomParms},
        indent=2
    ))


def xsecParmDict(xsecID: str):
    parmIds = vsp.GetXSecParmIDs(xsecID)
    return {
        vsp.GetParmName(theId): theId
        for theId in parmIds if vsp.ValidParm(theId)
    }


def ppXSec(xsecID: str):
    xsecParms = xsecParmDict(xsecID)
    print(json.dumps(
        {key: vsp.GetParmVal(xsecParms[key]) for key in xsecParms},
        indent=2
    ))


class Geom:
    def getParmIDs(self):
        return geomParmDict(self.geom)

    def initXsecSurf(self):
        try:
            self.xSecSurf = XSecSurf(self)
        except BaseException as e:
            print(e.__class__.__name__, e)
            self.xSecSurf = None

    def addChildGeom(self, geomType: str):
        child = Geom(geomType, self)
        self.child.append(child)
        return child

    def addChild(self, child: 'Geom'):
        self.child.append(child)
        return child

    def addWing(self):
        child = Wing(WING, self)
        self.child.append(child)
        return child

    def insertXSec(self,
                   index: int,
                   shape):
        if self.xSecSurf is None:
            return
        vsp.InsertXSec(self.geom, index, shape)
        self.initXsecSurf()

    def _get_setter(self, parmID: str):
        def setter(value):
            vsp.SetParmValUpdate(parmID, value)
        return setter

    def _get_getter(self, parmID: str):
        def getter():
            return vsp.GetParmVal(parmID)
        return getter

    def update(self):
        # for getters
        self.parmIDs = self.getParmIDs()
        # add getters
        self.__dict__.update(
            {
                'get'+key: (self._get_getter(self.parmIDs[key]))
                for key in self.parmIDs
            }
        )

        self.parmIDs = self.getParmIDs()
        # add setters
        self.__dict__.update(
            {
                'set'+key: (self._get_setter(self.parmIDs[key]))
                for key in self.parmIDs
            }
        )

        # initialize XSecSurf
        self.initXsecSurf()

    def __init__(self, geomType: str, parent: Union['Geom', None] = None):
        if parent is None:
            self.geom = vsp.AddGeom(geomType)
        else:
            self.geom = vsp.AddGeom(geomType, parent.geom)
        self.child = []
        self.update()


class Wing(Geom):
    def setPlanForm(self, S: float, AR: float):
        b = np.sqrt(AR*S)

        cont = True
        while cont:
            self.setTotalSpan(b)
            self.setTotalArea(S)
            cont = (self.getTotalAR() - AR) > 1E-6*AR

    def changeTaper(self, taper: float):
        rc = self.getRoot_Chord()
        tc = self.getTip_Chord()
        newRc = (rc+tc)/(1+taper)
        self.setRoot_Chord(newRc)
        self.setTip_Chord(taper*newRc)

    def __init__(self,
                 dummy: Any = WING,
                 parent: Union[Geom, None] = None):
        super().__init__(WING, parent=parent)


class Nacelle(Geom):
    def ChangeBORXSecShape(self, XS_TYPE):
        vsp.ChangeBORXSecShape(self.geom, XS_TYPE)

    def __init__(self,
                 dummy: Any = BODYOFREVOLUTION,
                 parent: Union[Geom, Wing, None] = None):
        super().__init__(BODYOFREVOLUTION, parent=parent)
        self.ChangeBORXSecShape(vsp.XS_FOUR_SERIES)
        self.update()
        self.setThickChord(0.15)
        self.setCamberLoc(0.3)
        self.setCamber(0.55)
        self.setDiameter(1.25)
        self.setAngle(3)


class EasyFuselage(Geom):
    def insertXSec(self,
                   index: int,
                   shape):
        return AttributeError(geom, index, shape)

    def update(self):
        super().update()

        l_fus = self.l_fus
        b_fus = self.b_fus
        h_fus = self.h_fus
        
        nose_ratio = self.nose_ratio
        tail_ratio = self.tail_ratio

        fus = self
        fus.setLength(l_fus)

        fus.setCapUMinOption(vsp.ROUND_END_CAP)
        fus.setCapUMaxOption(vsp.ROUND_END_CAP)

        # change shape for nose and tail
        fus.xSecSurf.ChangeXSecShape(0, vsp.XS_ELLIPSE)
        fus.xSecSurf.ChangeXSecShape(4, vsp.XS_ELLIPSE)

        for sec in self.xSecSurf.xSecs:
            sec.setEllipse_Height(h_fus)
            sec.setEllipse_Width(b_fus)

        # # nose
        fus.xSecSurf.xSecs[0].setEllipse_Height(h_fus/3)
        fus.xSecSurf.xSecs[0].setEllipse_Width(b_fus/3)
        fus.xSecSurf.xSecs[0].setZLocPercent(-h_fus/6/l_fus)

        fus.xSecSurf.xSecs[0].setTBSym(0)
        fus.xSecSurf.xSecs[0].setBottomRAngleSet(0)
        fus.xSecSurf.xSecs[0].setBottomLAngle(30)
        fus.xSecSurf.xSecs[0].setRightRAngleSet(0)
        fus.xSecSurf.xSecs[0].setRightLAngle(45)

        fus.xSecSurf.xSecs[1].setXLocPercent(nose_ratio * h_fus/l_fus)

        fus.xSecSurf.xSecs[3].setXLocPercent(1 - tail_ratio * h_fus/l_fus)

        # # tail
        fus.xSecSurf.xSecs[4].setEllipse_Height(h_fus/3)
        fus.xSecSurf.xSecs[4].setEllipse_Width(b_fus/6)
        fus.xSecSurf.xSecs[4].setZLocPercent(h_fus/3/l_fus)

        fus.xSecSurf.xSecs[4].setTBSym(0)
        # # # this has to be top in order to work
        fus.xSecSurf.xSecs[4].setTopRAngleSet(0)
        fus.xSecSurf.xSecs[4].setTopLAngle(0)
        fus.xSecSurf.xSecs[4].setBottomRAngleSet(0)
        fus.xSecSurf.xSecs[4].setBottomLAngle(-30)
        # # # this has to be right in order to work
        fus.xSecSurf.xSecs[4].setRightRAngleSet(0)
        fus.xSecSurf.xSecs[4].setRightLAngle(-10)

    def setLBH(self, l, b, h):
        self.l_fus=l
        self.b_fus=b
        self.h_fus=h

        self.update()

    def setTailRatio(sefl, tail_ratio):
        self.tail_ratio=tail_ratio
        self.update()

    def setNoseRatio(self, nose_ratio):
        self.nose_ratio=nose_ratio
        self.update()

    def __init__(self,
                 dummy: Any = FUSELAGE,
                 parent: Union[Geom, None] = None):
        self.tail_ratio=3.0
        self.nose_ratio=1.5
        self.h_fus=3.0
        self.b_fus=2.5
        self.l_fus=30
        super().__init__(FUSELAGE, parent=parent)
        self.update()


class XSecSurf:
    def fillXSec(self):
        self.xSecs = []
        for i in range(100):
            newXSec = XSec(self, i)
            if newXSec.xsec == '':
                break

            self.xSecs.append(newXSec)

    def ChangeXSecShape(self, index: int, shape):
        vsp.ChangeXSecShape(self.xsecSurf, index, shape)
        self.xSecs[index] = XSec(self, index)

    def __init__(self, geom: Geom):
        self.xsecSurf = vsp.GetXSecSurf(geom.geom, 0)

        if self.xsecSurf == '':
            raise BaseException(
                f'XSecSurf for geom: {geom.geom}, index: {0} was not found.'
            )

        self.fillXSec()


class XSec:
    def _get_setter(self, parmID: str):
        def setter(value):
            vsp.SetParmValUpdate(parmID, value)
        return setter

    def _get_getter(self, parmID: str):
        def getter():
            vsp.GetParmVal(parmID)
        return getter

    def getParmIDs(self):
        return xsecParmDict(self.xsec)

    def update(self):
        self.parmIDs = self.getParmIDs()

        self.__dict__.update({
            'get'+key: self._get_getter(self.parmIDs[key])
            for key in self.parmIDs
        })

        self.__dict__.update({
            'set'+key: self._get_setter(self.parmIDs[key])
            for key in self.parmIDs
        })

    def __init__(self, xsecSurf: XSecSurf, xsecIndex=0):
        self.xsec = ''

        tmpXSec = vsp.GetXSec(xsecSurf.xsecSurf, xsecIndex)
        if tmpXSec == '':
            # xsec was nonExistent
            return

        self.xsec = tmpXSec
        self.update()
