import ics

def merge_ics_files(base_ics, easter_ics, output_ics):
    """Unește două fișiere .ics: sărbători fixe și Paștele ortodox"""
    with open(base_ics, "r") as f:
        base_calendar = ics.Calendar(f.read())
    
    with open(easter_ics, "r") as f:
        easter_calendar = ics.Calendar(f.read())

    # Adaugă evenimentele Paștelui ortodox în calendarul principal
    base_calendar.events.update(easter_calendar.events)

    # Salvează noul fișier .ics
    with open(output_ics, "w") as f:
        f.write(str(base_calendar))
    
    print(f"Fișierul combinat a fost salvat ca {output_ics}")

# Exemplu de utilizare
merge_ics_files("festivitati_Original.ics", "paste_ortodox.ics", "Festivități Moldova.ics")
