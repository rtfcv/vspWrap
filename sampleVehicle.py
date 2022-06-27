import openvsp as vsp
# import vehicle as v
import vspWrap as v

# PARAMETERS
h_fus = 3.0
b_fus = 2.5
l_fus = 30.0

AR_wing = 10
S_wing = 90

# fuselage ################################################################
fus = v.EasyFuselage(v.FUSELAGE)

# doing this messes things up..., which shouldn't happen
fus.setLBH(l_fus, b_fus, h_fus)

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

# make it symmetrical across XZ plane
nacelle.setSym_Planar_Flag(vsp.SYM_XZ)

nacelle.setY_Rel_Location(0.25*l_fus)
nacelle.setX_Rel_Location(0.38*l_fus)
nacelle.setZ_Rel_Location(-0.5*h_fus)

# set length
nacelle.setChord(2)

# export ##################################################################
vsp.ExportFile('sampleVehicle.stl', 0, vsp.EXPORT_STL)
