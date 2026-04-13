import unicodedata

def normalizar_diccionario(diccionario_original):
    """
    Coge un diccionario y devuelve uno nuevo con las claves en minúsculas,
    sin acentos y sin caracteres especiales.
    """
    
    def limpiar_cadena(texto):
        # 1. Convertir a minúsculas y quitar espacios sobrantes
        texto = texto.lower().strip()
        
        # 2. Eliminar el punto volado del catalán (l·l -> ll) antes de normalizar
        texto = texto.replace('·', '')
        
        # 3. Normalización NFD: separa los caracteres de sus acentos
        # Ejemplo: 'ó' se convierte en 'o' + '´'
        texto = unicodedata.normalize('NFD', texto)
        
        # 4. Filtramos: nos quedamos solo con los caracteres que NO son marcas de acento
        # 'Mn' en Unicode significa 'Nonspacing Mark' (acentos, diéresis, etc.)
        texto = "".join(c for c in texto if unicodedata.category(c) != 'Mn')
        
        # 5. Volvemos a normalizar a NFC para recomponer caracteres si fuera necesario
        return unicodedata.normalize('NFC', texto)

    # Utilizamos una "Dictionary Comprehension" para crear el nuevo diccionario
    return {limpiar_cadena(clave): valor for clave, valor in diccionario_original.items()}

# --- EJEMPLO DE USO ---

elementos_quimicos = {
    "Hidrógeno": "H",
    "Helio": "He",
    "Litio": "Li",
    "Berilio": "Be",
    "Boro": "B",
    "Carbono": "C",
    "Nitrógeno": "N",
    "Oxígeno": "O",
    "Flúor": "F",
    "Neón": "Ne",
    "Sodio": "Na",
    "Magnesio": "Mg",
    "Aluminio": "Al",
    "Silicio": "Si",
    "Fósforo": "P",
    "Azufre": "S",
    "Cloro": "Cl",
    "Argón": "Ar",
    "Potasio": "K",
    "Calcio": "Ca",
    "Escandio": "Sc",
    "Titanio": "Ti",
    "Vanadio": "V",
    "Cromo": "Cr",
    "Manganeso": "Mn",
    "Hierro": "Fe",
    "Cobalto": "Co",
    "Níquel": "Ni",
    "Cobre": "Cu",
    "Zinc": "Zn",
    "Galio": "Ga",
    "Germanio": "Ge",
    "Arsénico": "As",
    "Selenio": "Se",
    "Bromo": "Br",
    "Kriptón": "Kr",
    "Rubidio": "Rb",
    "Estroncio": "Sr",
    "Itrio": "Y",
    "Zirconio": "Zr",
    "Niobio": "Nb",
    "Molibdeno": "Mo",
    "Tecnecio": "Tc",
    "Rutenio": "Ru",
    "Rodio": "Rh",
    "Paladio": "Pd",
    "Plata": "Ag",
    "Cadmio": "Cd",
    "Indio": "In",
    "Estaño": "Sn",
    "Antimonio": "Sb",
    "Telurio": "Te",
    "Yodo": "I",
    "Xenón": "Xe",
    "Cesio": "Cs",
    "Bario": "Ba",
    "Lantano": "La",
    "Cerio": "Ce",
    "Praseodimio": "Pr",
    "Neodimio": "Nd",
    "Prometio": "Pm",
    "Samario": "Sm",
    "Europio": "Eu",
    "Gadolinio": "Gd",
    "Terbio": "Tb",
    "Disprosio": "Dy",
    "Holmio": "Ho",
    "Erbio": "Er",
    "Tulio": "Tm",
    "Iterbio": "Yb",
    "Lutecio": "Lu",
    "Hafnio": "Hf",
    "Tántalo": "Ta",
    "Tungsteno": "W",
    "Renio": "Re",
    "Osmio": "Os",
    "Iridio": "Ir",
    "Platino": "Pt",
    "Oro": "Au",
    "Mercurio": "Hg",
    "Talio": "Tl",
    "Plomo": "Pb",
    "Bismuto": "Bi",
    "Polonio": "Po",
    "Ástato": "At",
    "Radón": "Rn",
    "Francio": "Fr",
    "Radio": "Ra",
    "Actinio": "Ac",
    "Torio": "Th",
    "Protactinio": "Pa",
    "Uranio": "U",
    "Neptunio": "Np",
    "Plutonio": "Pu",
    "Americio": "Am",
    "Curio": "Cm",
    "Berkelio": "Bk",
    "Californio": "Cf",
    "Einstenio": "Es",
    "Fermio": "Fm",
    "Mendelevio": "Md",
    "Nobelio": "No",
    "Laurencio": "Lr",
    "Rutherfordio": "Rf",
    "Dubnio": "Db",
    "Seaborgio": "Sg",
    "Bohrio": "Bh",
    "Hassio": "Hs",
    "Meitnerio": "Mt",
    "Darmstadio": "Ds",
    "Roentgenio": "Rg",
    "Copernicio": "Cn",
    "Nihonio": "Nh",
    "Flerovio": "Fl",
    "Moscovio": "Mc",
    "Livermorio": "Lv",
    "Teneso": "Ts",
    "Oganesón": "Og"
}

elementos_limpios = normalizar_diccionario(elementos_quimicos)

# Imprimir resultado de forma legible
import json
print(json.dumps(elementos_limpios, indent=4, ensure_ascii=False))