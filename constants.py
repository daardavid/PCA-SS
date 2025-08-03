#constants.py (antes estaban en main)

# --- DICCIONARIO DE MAPEO PARA NOMBRES DE INDICADORES ---
MAPEO_INDICADORES = {
    # --- NUEVOS INDICADORES (donde el nombre de la hoja es el nombre descriptivo) ---
    'Compulsory education': 'Ed_ob/Añ',
    'GDP growth (annual %)': 'PIB_cr/%',
    'GDP per capita growth (annual %': 'PIB_ca/%',
    'GDP per capita, PPP (constant 2': 'PIB_ca/ppp21',
    'Gov exp on educ % GDP': 'Go_Ed/%PIB',
    'Poverty headcount ratio at $6.8': 'Po_$6.85/%T',
    'Poverty headcount ratio at soci': 'Po_So/%T',
    'R&d expendi % GDP': 'I&D/%PIB',
    'School enroll, tertiy, fem': 'Ma_Tr_Mu/%T',
    'Carbon intensity of GDP': 'In_CO2/ppp21',
    'Energy intensity PPP GDP': 'In_En/ppp17',
    'School enroll terti total': 'Ma_Tr/%T',
    'Researchers in R&D (per million': 'Inv_I&D/Hab' 
    # Asegurarse que la CLAVE sea EXACTAMENTE el nombre de la hoja en el EXCEL :).
}


# --- DICCIONARIO DE GRUPOS DE PAÍSES ---
COUNTRY_GROUPS = {
    # Neoliberales Avanzados
    'AUS': 'Neoliberales Avanzados', 'BEL': 'Neoliberales Avanzados', 'CAN': 'Neoliberales Avanzados',
    'FRA': 'Neoliberales Avanzados', 'DEU': 'Neoliberales Avanzados',
    'LUX': 'Neoliberales Avanzados', 'NLD': 'Neoliberales Avanzados', 'ESP': 'Neoliberales Avanzados',
    'CHE': 'Neoliberales Avanzados', 'GBR': 'Neoliberales Avanzados', 'USA': 'Neoliberales Avanzados',
    'NZL': 'Neoliberales Avanzados', 'AUT': 'Neoliberales Avanzados', 'ITA': 'Neoliberales Avanzados',

    # Neoliberales tardíos
    'GRC': 'Neoliberales Tardíos', 'HUN': 'Neoliberales Tardíos', 'IRL': 'Neoliberales Tardíos',
    'LVA': 'Neoliberales Tardíos', 'MEX': 'Neoliberales Tardíos', 'POL': 'Neoliberales Tardíos',
    'PRT': 'Neoliberales Tardíos', 'SVK': 'Neoliberales Tardíos', 'SVN': 'Neoliberales Tardíos',
    'TUR': 'Neoliberales Tardíos', 'CHL': 'Neoliberales Tardíos', 'EST': 'Neoliberales Tardíos',
    'HRV': 'Neoliberales Tardíos', 'LTU': 'Neoliberales Tardíos', 'CZE': 'Neoliberales Tardíos',

    # Escandinavos
    'FIN': 'Escandinavos', 'DNK': 'Escandinavos', 'NOR': 'Escandinavos', 'SWE': 'Escandinavos',
    'ISL': 'Escandinavos',

    # Asiáticos
    'CHN': 'Asiáticos', 'IND': 'Asiáticos', 'IDN': 'Asiáticos', 'JPN': 'Asiáticos',
    'KOR': 'Asiáticos', 'SGP': 'Asiáticos', 'MYS': 'Asiáticos', 'THA': 'Asiáticos', 'VNM': 'Asiáticos',
    
    # Otros (Latinoamérica, etc.)
    'ARG': 'Otros', 'BRA': 'Otros', 'COL': 'Otros', 'CRI': 'Otros',
    'ECU': 'Otros', 'PER': 'Otros', 'URY': 'Otros'
}

# --- DICCIONARIO PARA MAPEAR CÓDIGOS A NOMBRES ---
# Se usa para mostrar un menú amigable al usuario.
CODE_TO_NAME = {
    'ARG': 'Argentina', 'AUS': 'Australia', 'AUT': 'Austria', 'BEL': 'Belgium', 
    'BRA': 'Brazil', 'CAN': 'Canada', 'CHE': 'Switzerland', 'CHL': 'Chile',
    'CHN': 'China', 'COL': 'Colombia', 'CRI': 'Costa Rica', 'HRV': 'Croatia', 
    'CZE': 'Czechia', 'DEU': 'Germany', 'DNK': 'Denmark', 'ECU': 'Ecuador',
    'ESP': 'Spain', 'EST': 'Estonia', 'FIN': 'Finland', 'FRA': 'France', 
    'GBR': 'United Kingdom', 'GRC': 'Greece', 'HUN': 'Hungary', 'IDN': 'Indonesia',
    'IND': 'India', 'ITA': 'ITALIA', 'IRL': 'Ireland', 'ISL': 'Iceland', 'ITA': 'Italy', 'JPN': 'Japan',
    'KOR': 'Korea, Rep.', 'LVA': 'Latvia', 'LUX': 'Luxembourg', 'MEX': 'Mexico',
    'MYS': 'Malaysia', 'NLD': 'Netherlands', 'NOR': 'Norway', 'NZL': 'New Zealand',
    'PER': 'Peru', 'POL': 'Poland', 'PRT': 'Portugal', 'SGP': 'Singapore', 
    'SVK': 'Slovak Republic', 'SVN': 'Slovenia', 'SWE': 'Sweden', 'THA': 'Thailand',
    'TUR': 'Turkiye', 'URY': 'Uruguay', 'USA': 'United States', 'VNM': 'Viet Nam', 'LTU': 'Lithuania', 'GBR': 'United Kingdom'
    # Agrega más códigos si es necesario
}

# --- DICCIONARIO DE COLORES PARA LOS GRUPOS (ESTÁ BIEN COMO LO TENÍAS) ---
GROUP_COLORS = {
    'Neoliberales Avanzados': 'blue',
    'Neoliberales Tardíos': 'green',
    'Escandinavos': 'purple',
    'Asiáticos': 'orange',
    'Otros': 'gray'
}