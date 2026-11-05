from datetime import date, timedelta
import ics

def orthodox_easter(year):
    """Calculează data Paștelui ortodox în calendarul gregorian"""
    equinox = date(year, 3, 21)  # Echinocțiul de primăvară (fix pe 21 martie)
    
    # Determinarea primei luni pline după echinocțiu
    a = year % 19
    b = year % 7
    c = year % 4
    d = (19 * a + 15) % 30
    e = (2 * c + 4 * b + 6 * d + 6) % 7
    f = d + e

    if f <= 26:
        day = f + 4
    else:
        day = f - 26

    # Calculul datei lunii pline pascale
    lunar_full_moon = date(year, 4, day)

    # Paștele ortodox este în prima duminică după luna plină pascală
    # Dacă luna plină cade într-o duminică, Paștele se mută în duminica următoare
    easter_day = lunar_full_moon + timedelta(days=(6 - lunar_full_moon.weekday()))
    
    return easter_day


def generate_orthodox_easter_ics(start_year, end_year, filename="paste_ortodox.ics"):
    """Generează un fișier .ics cu datele Paștelui ortodox și alte sărbători asociate"""
    calendar = ics.Calendar()
    
    for year in range(start_year, end_year + 1):
        easter = orthodox_easter(year)
        
        # Listează sărbătorile legate de Paște
        events = [
            ("Paște Ortodox", easter),  # Ziua Paștelui
            ("Intrarea Domnului în Ierusalim", easter - timedelta(days=7)),  # 7 zile înainte de Paște (Floriile)
            ("Înălțarea Domnului", easter + timedelta(days=40)),  # 40 de zile după Paște
            ("Ziua Sfintei Treimi", easter + timedelta(days=50))  # 50 de zile după Paște (Rusaliile)
        ]
        
        # Adaugă fiecare sărbătoare în calendar
        for name, date_event in events:
            event = ics.Event()
            event.name = name
            event.begin = date_event.strftime("%Y%m%d")
            event.description = f"Sărbătoare ortodoxă - {name}"
            calendar.events.add(event)
    
    # Salvează calendarul într-un fișier .ics
    with open(filename, "w") as f:
        f.write(str(calendar))
    
    print(f"Fișierul {filename} a fost generat cu succes!")

# Exemplu de utilizare
generate_orthodox_easter_ics(2025, 2050)