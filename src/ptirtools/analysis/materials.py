### Here, we provide some abstractions for the interpretation of mid-IR wavenumbers as molecular bond vibration modes. 

from dataclasses import dataclass


### vibration modes,
### e.g. stretching / bending / ...
@dataclass
class VibrationMode:
    motion : str
    mshort : str
    msymb : str
    symmetry : str = None
    sshort : str = ""
    ssymb : str = ""

    def symb(self) -> str:
        return f"{self.msymb}{self.ssymb if self.symmetry is not None else ''}"
    
    def short(self) -> str:
        #return f"{self.sshort+' ' if self.symmetry is not None else ''}{self.mshort}"
        return f"{self.sshort+' ' if self.symmetry is not None else ''}{self.motion.replace('ing','')}"
    
    def descr(self) -> str:
        return f"{self.symmetry+' ' if self.symmetry is not None else ''}{self.motion}"
    
    def __repr__(self) -> str:
        return f"<VibrationMode: '{self.descr()}' vibration / {self.symb()}(...)>"
    
    def __hash__(self) -> str:
        return hash(self.__repr__())


### library of common modes
VIBRATION_MODES = {
    VibrationMode("stretching", "str", "ν"),
    VibrationMode("stretching", "str", "ν", "asymmetric", "asym", "ₐₛ"),
    VibrationMode("stretching", "str", "ν", "symmetric", "sym", "ₛ"),
    VibrationMode("bending", "bnd", "δ"),
    VibrationMode("bending", "bnd", "δ", "asymmetric", "asym", "ₐₛ"),
    VibrationMode("bending", "bnd", "δ", "symmetric", "sym", "ₛ"),
    VibrationMode("rocking", "rck", "ρ"),
    VibrationMode("torsion", "tor", "τ"),
    VibrationMode("wagging", "wag", "γ"),
}


### Bonds
@dataclass 
class Bond:
    symb : str
    name : str

    def __repr__(self) -> str:
        return f"<Bond: '{self.name}' / {self.symb}>"


### library of common bonds
BONDS = {
    "aromatic ring" : Bond("⌬", "aromatic ring"),
    "aromatic ring C=C" : Bond("⌬ C=C", "aromatic ring C=C"),
    "C-O-C" : Bond("C–O–C", "ester"),
    "C=O" : Bond("C=O", "carbonyl"),
    "C-O" : Bond("C–O", "C–O"),
    "C=C" : Bond("C=C", "alkene"),
    "C-C" : Bond("C–C", "alkane"),
    "CH2" : Bond("CH₂", "CH₂"),
    "CH3" : Bond("CH₃", "methyl"),
    "C=N" : Bond("C=N", "azine"),
    "N-H" : Bond("N–H", "N–H"),
    "C-N" : Bond("C–N", "C–N"),
    "C-N-C" : Bond("C–N–C", "C–N–C"),
}


### functions to choose Vibration Modes and Bonds from the library
def find_bond_from_string(bond_str:str) -> Bond:
    ### first, search the dictionary by key
    if bond_str in BONDS:
        return BONDS[bond_str]
    ### if not found, then try names or symbols
    for bond in BONDS.values():
        if bond.name == bond_str or bond.symb == bond_str:
            return bond
    ### if still not found, return unknown bond
    return Bond(bond_str, bond_str)

def find_vibration_mode_from_string(vib_str:str) -> VibrationMode:
    for vib in VIBRATION_MODES:
        if vib_str.replace("ing","") in ( vib.short().replace("ing",""), vib.descr().replace("ing",""), vib.symb() ):
            return vib
    else:
        ### if no match found, return some general vibration
        return VibrationMode("vibration", "vibr", "vib")


### pairs of bonds and vibration modes
@dataclass 
class BondVibration:
    bond : Bond
    mode : VibrationMode

    def symb(self) -> str:
        return f"{self.mode.symb()}({self.bond.symb})"
    
    def short(self) -> str:
        return f"{self.bond.symb} {self.mode.short()}"

    def descr(self) -> str:
        return f"{self.bond.name} {self.mode.descr()}"

    def __repr__(self) -> str:
        return f"<BondVibration: '{self.descr()}' / {self.symb()}>"
    
    def __hash__(self):
        return hash( f"{self.bond.__repr__()} | {self.mode.__repr__()}" )

def make_bond_vibration( bond_str:str, vib_str:str ) -> BondVibration:
    return BondVibration( find_bond_from_string(bond_str), find_vibration_mode_from_string(vib_str) )
    

### info about an IR band that's associated with some bond vibration mode
@dataclass
class IRBand:
    mode : BondVibration
    center : float
    width : float

    def description(self) -> str:
        return f"{self.mode.descr()} at {self.center} ± {self.width} cm⁻¹"


### a material can have several IR bands
@dataclass
class Material:
    name : str
    shortname : str
    aliases : list[str]
    kappa : float
    c : float
    rho : float
    n : float

    bands : list[IRBand]

    def __repr__(self) -> str:
        return f"<Material '{self.name}' ({self.shortname}){' a.k.a. '+'/'.join(self.aliases)} with kappa={self.kappa}, c={self.c}, rho={self.rho}, n={self.n} and IR bands {', '.join([ b.__repr__() for b in self.bands])}>"
    ### todo: add thermal diffusivity alpha


MATERIAL_LIBRARY = [
    Material("Polystyrene", "PS", aliases=[], kappa=(0.033+0.04)/2, c=1300, rho=1050, n=1.6, bands=[
        IRBand( make_bond_vibration("C=C", "stretch"), 1602, 2.0),
        IRBand( make_bond_vibration("⌬", "vibration"), 1583, 2.0),
        IRBand( make_bond_vibration("⌬ C=C", "stretch"), 1493, 2.0),
        IRBand( make_bond_vibration("CH2", "bend"), 1451, 2.0),
    ]),
    Material("Paraffin Oil", "oil", aliases=["PÖ", "medium"], kappa=0.215, c=2130, rho=858.5, n=1.477, bands=[
        IRBand( make_bond_vibration("CH2", "bend"), 1463, 2.0),
        IRBand( make_bond_vibration("CH3", "symmetric bend"), 1379, 2.0),
        #IRBand( make_bond_vibration("C-C", "stretch"), 1115, 2.0),
    ]),
    Material("Polymethylmethacrylate", "PMMA", aliases=[], kappa=0.19, c=1460, rho=1180, n=1.4906, bands=[
        IRBand( make_bond_vibration("C=O", "stretch"), 1731, 5.0),
        IRBand( make_bond_vibration("CH2", "bend"), 1451, 2.0),
        IRBand( make_bond_vibration("C-O-C", "asym stretch"), 1273, 5.0),
        IRBand( make_bond_vibration("C-O-C", "asym stretch"), 1241, 5.0),
        IRBand( make_bond_vibration("C-O", "stretch"), 1195, 5.0),
        IRBand( make_bond_vibration("C-O-C", "sym stretch"), 1151, 5.0),
    ]),
    # Material("Melamine-formaldehyde resin", "MF", aliases=[], kappa=0.0, c=1000, rho=1000, n=1.5000, bands=[
    #     IRBand( make_bond_vibration("C=N", "stretch"), 1645, 2.0),
    #     IRBand( make_bond_vibration("N-H", "bend"), 1545, 2.0),
    #     IRBand( make_bond_vibration("C-N", "stretch"), 1460, 2.0),
    #     IRBand( make_bond_vibration("C-N-C", "sym stretch"), 1330, 2.0),
    # ]),
]

MATERIAL_LIBRARY += [
    Material("Polydimethylsiloxane", "PDMS", aliases=["Sylgard", "silicone oil"], 
        kappa=0.15, c=1460, rho=965, n=1.40, bands=[
            IRBand(make_bond_vibration("Si–CH3", "asym stretch"), 2962, 3.0),
            IRBand(make_bond_vibration("Si–CH3", "sym stretch"), 2905, 3.0),
            IRBand(make_bond_vibration("CH3", "bend"), 1411, 3.0),
            IRBand(make_bond_vibration("Si–O–Si", "asym stretch"), 1260, 3.0),
            IRBand(make_bond_vibration("Si–C", "stretch"), 802, 3.0),
            IRBand(make_bond_vibration("Si–O–Si", "bend"), 1096, 3.0),
    ]),

    Material("Bovine Serum Albumin", "BSE", aliases=["protein standard", "albumin"], 
        kappa=0.20, c=1800, rho=1350, n=1.45, bands=[
            IRBand(make_bond_vibration("C=O (amide I)", "stretch"), 1650, 3.0),
            IRBand(make_bond_vibration("N–H (amide II)", "bend"), 1545, 3.0),
            IRBand(make_bond_vibration("C–N (amide III)", "stretch/bend"), 1240, 3.0),
            IRBand(make_bond_vibration("CH2", "bend"), 1450, 3.0),
    ]),

    Material("Water", "H₂O", aliases=["H2O"], 
        kappa=0.60, c=4182, rho=997, n=1.333, bands=[
            IRBand(make_bond_vibration("O–H", "stretch"), 3400, 10.0),
            IRBand(make_bond_vibration("H–O–H", "bend"), 1640, 5.0),
    ]),

    Material("Toluene", "Tol", aliases=["C7H8", "methylbenzene"], 
        kappa=0.13, c=1700, rho=867, n=1.496, bands=[
            IRBand(make_bond_vibration("⌬ C–H", "stretch"), 3030, 3.0),
            IRBand(make_bond_vibration("C–H", "stretch"), 2925, 3.0),
            IRBand(make_bond_vibration("⌬ C=C", "stretch"), 1605, 2.0),
            IRBand(make_bond_vibration("⌬ C=C", "stretch"), 1495, 2.0),
            IRBand(make_bond_vibration("CH3", "bend"), 1377, 2.0),
            IRBand(make_bond_vibration("C–H", "out-of-plane bend"), 730, 3.0),
    ]),
]

def get_material(identifier:str) -> Material:
    for mat in MATERIAL_LIBRARY:
        if identifier in ( mat.name, mat.shortname, *mat.aliases ) or identifier in mat.aliases:
            return mat
    return None


### this kind of IR band has its wavenumber as the primary identifier and various vibration modes & materials that it could belong to
@dataclass
class AmbiguousIRBand:
    wavenumber : float
    modes_on_materials : dict

    def descr(self) -> str:
        return ', '.join([ f"{mode.descr()} ({(' / '.join(mats))})" for mode, mats in self.modes_on_materials.items()])
    
    def short(self) -> str:
        return ', '.join([ f"{mode.short()} ({(' / '.join(mats))})" for mode, mats in self.modes_on_materials.items()])
    
    def multiline(self) -> str:
        return f"{self.wavenumber}cm⁻¹\n" + '\n'.join([ f"{mode.short()}\n({(' / '.join(mats))})" for mode, mats in self.modes_on_materials.items()])
    
    def symb(self) -> str:
        return ', '.join([ f"{(' / '.join(mats))} {mode.symb()}" for mode, mats in self.modes_on_materials.items()])
    
    def materials(self) -> set:
        return { mat for mats in self.modes_on_materials.values() for mat in mats }

    def modes(self) -> set:
        return { mode for mode in self.modes_on_materials.keys() }
    
    def __repr__(self) -> str:
        modes_on_mats_str = ", ".join( [ f"{mode.__repr__()} : {mats}" for mode,mats in self.modes_on_materials.items() ] )
        return f"<AmbiguousIRBand at {self.wavenumber} with modes / mats {modes_on_mats_str}>"
    
    def __hash__(self):
        return hash(self.__repr__())

### testing

WAVENUMBERS_UNICODE_STR = "cm⁻¹"

def test():
    print(f"Library of Vibration Modes:\n  " + "\n  ".join( [ vib.__repr__() for vib in VIBRATION_MODES ] ))
    print(f"Library of Molecular Bonds:\n  " + "\n  ".join( [ bond.__repr__() for bond in BONDS.values() ] ))
    print(f"Library of Materials:\n  " + "\n  ".join( [ mat.__repr__() for mat in MATERIAL_LIBRARY ] ))


if __name__ == "__main__":
    test()

