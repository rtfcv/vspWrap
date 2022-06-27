import openvsp as vsp
# import vehicle as v
import vspWrap as v
from pprint import pprint

# PARAMETERS
h_fus = 3.0
b_fus = 2.5
l_fus = 30.0

AR_wing = 10
S_wing = 90

D_eng = 1.25
l_eng = 2

# fuselage ################################################################
fus = v.EasyFuselage(v.FUSELAGE)

# doing this messes things up..., which shouldn't happen
fus.setLBH(l_fus, b_fus, h_fus)

fus.setTess_U(16.0 * 3)
fus.setTess_W(17.0 * 3)
fus.setCapUMinTess(9 * 2)

fus.xSecSurf.xSecs[1].setSectTess_U(6.0*3.0)

# v.ppXSec(fus.xSecSurf.xSecs[0])
v.pp(fus)

# wing ####################################################################
wing = fus.addWing()
wing.setX_Rel_Location(0.3*l_fus)
wing.setZ_Rel_Location(-0.36*h_fus)

wing.setPlanForm(S_wing, AR_wing)

# hstab ###################################################################
hStab = fus.addWing()
hStab.setX_Rel_Location(0.86*l_fus)
hStab.setZ_Rel_Location(0.36*h_fus)

hStab.setPlanForm(S_wing/3, AR_wing/2)
hStab.changeTaper(0.3)
hStab.setSweep(32)

# vstab ###################################################################
vStab = fus.addWing()
vStab.setX_Rel_Location(0.83*l_fus)
vStab.setZ_Rel_Location(0.36*h_fus)

vStab.setPlanForm(S_wing/2.5, AR_wing/3)
vStab.changeTaper(0.4)
vStab.setSweep(36)

vStab.setX_Rel_Rotation(90)

# nacelle #################################################################
nacelle = wing.addChild(v.Nacelle(v.BODYOFREVOLUTION, wing))

nacelle.setTess_U(16.0 * 2)
nacelle.setTess_W(17.0 * 2)

# make it symmetrical across XZ plane
nacelle.setSym_Planar_Flag(vsp.SYM_XZ)

nacelle.setY_Rel_Location(0.25*l_fus)
nacelle.setX_Rel_Location(0.38*l_fus)
nacelle.setZ_Rel_Location(-0.5*h_fus)

# set length
nacelle.setDiameter(D_eng)
nacelle.setChord(l_eng)

# export ##################################################################
vsp.ExportFile('sampleVehicle.stl', 0, vsp.EXPORT_STL)
