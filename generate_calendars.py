#!/usr/bin/env python3
"""Generator de calendare .ics pentru Republica Moldova.

Produce două fișiere (doar bibliotecă standard, fără dependențe):

  * Sarbatori_Laice_Moldova.ics    – sărbători naționale / laice (date fixe, calendar civil)
  * Sarbatori_Ortodoxe_Moldova.ics – calendarul bisericesc ortodox pe STIL VECHI (iulian):
        praznice, sfinți, duminici cu nume, posturi, Triod și Penticostar,
        toate calculate automat din data Paștelui.

Utilizare:
    python3 generate_calendars.py                  # 2025-2040
    python3 generate_calendars.py --start 2025 --end 2060 --out-dir out
"""
import argparse
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple, Optional

LUNI = ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie",
        "august", "septembrie", "octombrie", "noiembrie", "decembrie"]

# ---------------------------------------------------------------------------
# Calendar iulian <-> gregorian (prin numărul zilei iuliene, valabil oricând)
# ---------------------------------------------------------------------------

def julian_to_gregorian(y: int, m: int, d: int) -> date:
    """Data din calendarul iulian (stil vechi) -> data civilă (gregoriană)."""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - 32083
    return date.fromordinal(jdn - 1721425)


def gregorian_to_julian(dt: date) -> tuple:
    """Data civilă (gregoriană) -> (an, lună, zi) în calendarul iulian."""
    jdn = dt.toordinal() + 1721425
    c = jdn + 32082
    d4 = (4 * c + 3) // 1461
    e = c - 1461 * d4 // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = d4 - 4800 + m // 10
    return year, month, day


def orthodox_easter(year: int) -> date:
    """Paștele ortodox (data civilă gregoriană) – algoritmul Meeus pentru calendarul iulian."""
    a, b, c = year % 4, year % 7, year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = (d + e + 114) % 31 + 1
    return julian_to_gregorian(year, month, day)


def _selftest() -> None:
    known = {2025: date(2025, 4, 20), 2026: date(2026, 4, 12), 2027: date(2027, 5, 2),
             2028: date(2028, 4, 16), 2029: date(2029, 4, 8), 2030: date(2030, 4, 28),
             2032: date(2032, 5, 2), 2040: date(2040, 5, 6), 2043: date(2043, 5, 3)}
    for y, expected in known.items():
        assert orthodox_easter(y) == expected, (y, orthodox_easter(y), expected)
        assert orthodox_easter(y).weekday() == 6, "Paștele trebuie să fie duminică"
    assert julian_to_gregorian(2025, 12, 25) == date(2026, 1, 7)
    assert gregorian_to_julian(date(2026, 1, 7)) == (2025, 12, 25)


# ---------------------------------------------------------------------------
# Model de eveniment + scriere ICS
# ---------------------------------------------------------------------------

class Ev(NamedTuple):
    start: date
    end: Optional[date]      # exclusiv (convenția iCalendar); None = o singură zi
    summary: str
    desc: str
    cat: str


def _esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
                .replace(",", "\\,").replace("\n", "\\n"))


def _fold(line: str) -> str:
    """Împarte liniile la max. 75 de octeți (RFC 5545) fără a tăia caractere UTF-8."""
    data = line.encode("utf-8")
    parts, limit = [], 75
    while len(data) > limit:
        cut = limit
        while (data[cut] & 0xC0) == 0x80:
            cut -= 1
        parts.append(data[:cut].decode("utf-8"))
        data, limit = data[cut:], 74
    parts.append(data.decode("utf-8"))
    return "\r\n ".join(parts)


def _slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:40]


def write_ics(path: Path, cal_id: str, name: str, description: str, events: list) -> None:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//storm167//Sarbatori Moldova//RO",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{_esc(name)}", f"X-WR-CALDESC:{_esc(description)}"]
    seen = set()
    for ev in sorted(events, key=lambda e: (e.start, e.summary)):
        uid = f"{cal_id}-{ev.start:%Y%m%d}-{_slug(ev.summary)}@sarbatori-moldova"
        assert uid not in seen, f"UID duplicat: {uid}"
        seen.add(uid)
        end = ev.end or (ev.start + timedelta(days=1))
        lines += ["BEGIN:VEVENT", f"UID:{uid}", "DTSTAMP:20250101T000000Z",
                  f"DTSTART;VALUE=DATE:{ev.start:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{end:%Y%m%d}",
                  f"SUMMARY:{_esc(ev.summary)}"]
        if ev.desc:
            lines.append(f"DESCRIPTION:{_esc(ev.desc)}")
        lines += [f"CATEGORIES:{_esc(ev.cat)}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(_fold(l) for l in lines) + "\r\n", encoding="utf-8", newline="")


# ---------------------------------------------------------------------------
# 1) SĂRBĂTORI LAICE / NAȚIONALE (calendar civil, date fixe)
# ---------------------------------------------------------------------------

OFF = "Zi liberă legală în Republica Moldova (verifică Codul muncii, art. 111)."

# (lună, zi, titlu, descriere, categorie, zi_liberă)
LAICE = [
    (1, 1, "Anul Nou", "Prima zi a anului.", "Zi liberă", True),
    (2, 24, "Dragobete", "Sărbătoare populară a iubirii.", "Tradiție", False),
    (3, 1, "Ziua Mărțișorului", "Începutul primăverii; se oferă mărțișoare.", "Tradiție", False),
    (3, 8, "Ziua Internațională a Femeii", "", "Zi liberă", True),
    (4, 27, "Ziua Drapelului de Stat", "Ziua Drapelului de Stat al Republicii Moldova.", "Zi națională", False),
    (5, 1, "Ziua Internațională a Muncii", "", "Zi liberă", True),
    (5, 9, "Ziua Europei / Ziua Victoriei",
     "Ziua Europei, Ziua Victoriei și a comemorării eroilor căzuți pentru Patrie.", "Zi liberă", True),
    (6, 1, "Ziua Internațională a Copilului", "", "Zi comemorativă", False),
    (7, 29, "Ziua Constituției", "Ziua Constituției Republicii Moldova.", "Zi națională", False),
    (8, 27, "Ziua Independenței", "Declarația de Independență a Republicii Moldova (1991).", "Zi liberă", True),
    (8, 31, "Limba Noastră", "Ziua Limbii Române.", "Zi liberă", True),
    (10, 14, "Hramul orașului Chișinău",
     "Ziua orașului Chișinău, sărbătorită de Acoperământul Maicii Domnului.", "Zi festivă", False),
    (12, 25, "Crăciunul pe stil nou", "Nașterea Domnului pe stil nou.", "Zi liberă", True),
]


def build_laice(start: int, end: int) -> list:
    events = []
    for y in range(start, end + 1):
        for m, d, title, desc, cat, off in LAICE:
            text = " ".join(x for x in (desc, OFF if off else "") if x)
            events.append(Ev(date(y, m, d), None, title, text, cat))
        # Ziua Națională a Vinului: primul weekend din octombrie (sâmbătă–duminică)
        first = date(y, 10, 1)
        saturday = first + timedelta(days=(5 - first.weekday()) % 7)
        events.append(Ev(saturday, saturday + timedelta(days=2), "Ziua Națională a Vinului",
                         "Primul weekend din octombrie.", "Tradiție"))
    return events


# ---------------------------------------------------------------------------
# 2) CALENDARUL ORTODOX PE STIL VECHI
# ---------------------------------------------------------------------------

IMP = "Praznic Împărătesc"
MD = "Praznic al Maicii Domnului"
SF = "Sfinți"
DUM = "Duminică"
TRI = "Triod"
PEN = "Penticostar"
POST = "Post"

# Praznice cu dată fixă. Data e cea din calendarul bisericesc (iulian);
# în calendarul civil cade cu 13 zile mai târziu (25 dec -> 7 ian).
# (lună, zi, titlu, categorie, descriere)
FIXE = [
    (1, 1, "Tăierea împrejur a Domnului · Sf. Vasile cel Mare", IMP,
     "Tăierea împrejur a Domnului și pomenirea Sf. Ierarh Vasile cel Mare, Arhiepiscopul Cezareei Capadociei."),
    (1, 6, "Botezul Domnului (Boboteaza)", IMP, "Epifania, Teofania sau Arătarea Domnului."),
    (1, 7, "Soborul Sf. Ioan Botezătorul", SF, "Sf. Ioan Botezătorul, Proorocul și Înainte-Mergătorul Domnului."),
    (1, 30, "Sfinții Trei Ierarhi", SF, "Vasile cel Mare, Grigorie Teologul și Ioan Gură de Aur (Trisfetitele)."),
    (2, 2, "Întâmpinarea Domnului (Stretenia)", IMP, "La 40 de zile de la Nașterea Domnului."),
    (3, 9, "Sfinții 40 de Mucenici din Sevastia", SF, "Mucenicii (Mucenicii)."),
    (3, 25, "Buna Vestire (Blagoveștenia)", MD, "Praznic al Maicii Domnului și praznic împărătesc."),
    (4, 23, "Sf. Mare Mucenic Gheorghe", SF, "Purtătorul de biruință (Sângeorz)."),
    (5, 9, "Sf. Nicolae de vară", SF, "Aducerea moaștelor Sf. Ierarh Nicolae."),
    (5, 21, "Sf. Împărați Constantin și Elena", SF, "Întocmai cu Apostolii."),
    (6, 24, "Nașterea Sf. Ioan Botezătorul", SF, "Sânziene / Drăgaica."),
    (6, 29, "Sf. Apostoli Petru și Pavel", SF, "Sânpetru."),
    (7, 20, "Sf. Prooroc Ilie Tesviteanul", SF, "Sântilie."),
    (7, 27, "Sf. Mare Mucenic Pantelimon", SF, ""),
    (8, 1, "Aflarea Sfintei Cruci", SF, "Scoaterea cinstitelor lemne ale Sfintei Cruci; începe Postul Adormirii."),
    (8, 6, "Schimbarea la Față a Domnului", IMP, ""),
    (8, 15, "Adormirea Maicii Domnului (Sf. Maria Mare)", MD, ""),
    (8, 29, "Tăierea capului Sf. Ioan Botezătorul", SF, "Zi de post."),
    (9, 8, "Nașterea Maicii Domnului (Sf. Maria Mică)", MD, ""),
    (9, 14, "Înălțarea Sfintei Cruci", IMP, "Zi de post."),
    (9, 26, "Sf. Apostol și Evanghelist Ioan Teologul", SF, ""),
    (10, 1, "Acoperământul Maicii Domnului", MD, "Pocrov."),
    (10, 14, "Sf. Cuvioasă Parascheva", SF, ""),
    (10, 26, "Sf. Mare Mucenic Dimitrie (Sâmedru)", SF, ""),
    (11, 8, "Soborul Sf. Arhangheli Mihail și Gavriil", SF, "Sfinții Voievozi."),
    (11, 21, "Intrarea în Biserică a Maicii Domnului", MD, "Vovidenia / Ovedenia."),
    (11, 25, "Sf. Mare Muceniță Ecaterina", SF, ""),
    (11, 30, "Sf. Apostol Andrei", SF, "Cel Întâi Chemat."),
    (12, 6, "Sf. Ierarh Nicolae", SF, "Arhiepiscopul Mirelor Lichiei."),
    (12, 12, "Sf. Ierarh Spiridon", SF, ""),
    (12, 25, "Nașterea Domnului (Crăciunul)", IMP, "Crăciunul pe stil vechi."),
    (12, 26, "Soborul Maicii Domnului", MD, ""),
    (12, 27, "Sf. Arhidiacon și Întâiul Mucenic Ștefan", SF, ""),
]

# Zile libere legale legate de calendarul bisericesc: (lună iuliană, zi) / decalaj față de Paște
ZILE_LIBERE_FIXE = {(12, 25), (12, 26)}          # 7 și 8 ianuarie în calendarul civil
ZILE_LIBERE_PASTE = {0, 1, 8}                     # Paște, Lunea Paștelui, Paștele Blajinilor

# Posturi cu dată fixă: (zi/lună început, zi/lună sfârșit inclusiv, titlu)
POSTURI_FIXE = [
    ((8, 1), (8, 14), "Postul Adormirii Maicii Domnului"),
    ((11, 15), (12, 24), "Postul Nașterii Domnului (Postul Crăciunului)"),
]

# Duminici fără nume propriu din ciclul Triodului/Penticostarului (decalaj față de Paște)
MOBILE = [
    (-70, "Duminica Vameșului și a Fariseului", TRI, "Începe perioada Triodului."),
    (-63, "Duminica Fiului Risipitor", TRI, ""),
    (-57, "Sâmbăta morților (Moșii de iarnă)", TRI, "Sâmbăta pomenirii morților."),
    (-56, "Duminica Înfricoșătoarei Judecăți (Lăsatul secului de carne)", TRI, "Ultima zi de mâncare de carne."),
    (-49, "Duminica Izgonirii lui Adam din Rai (Lăsatul secului de brânză)", TRI,
     "Duminica Iertării; mâine începe Postul Mare."),
    (-43, "Sâmbăta Sf. Teodor Tiron (a coliivei)", TRI, "Prima sâmbătă din Postul Mare."),
    (-42, "Duminica I din Post (a Ortodoxiei)", TRI, "Triumful Ortodoxiei."),
    (-35, "Duminica a II-a din Post (Sf. Grigorie Palama)", TRI, ""),
    (-28, "Duminica a III-a din Post (a Sfintei Cruci)", TRI, "Închinarea Sfintei Cruci."),
    (-21, "Duminica a IV-a din Post (Sf. Ioan Scărarul)", TRI, ""),
    (-15, "Sâmbăta Acatistului", TRI, "Acatistul Maicii Domnului."),
    (-14, "Duminica a V-a din Post (Sf. Maria Egipteanca)", TRI, ""),
    (-8, "Sâmbăta lui Lazăr", TRI, "Învierea dreptului Lazăr."),
    (-7, "Intrarea Domnului în Ierusalim (Floriile)", IMP, "Duminica Floriilor."),
    (-6, "Lunea Mare", TRI, "Săptămâna Patimilor."),
    (-5, "Marțea Mare", TRI, "Săptămâna Patimilor."),
    (-4, "Miercurea Mare", TRI, "Săptămâna Patimilor."),
    (-3, "Joia Mare", TRI, "Cina cea de Taină; Spălarea picioarelor."),
    (-2, "Vinerea Mare (a Patimilor)", TRI, "Răstignirea și îngroparea Domnului. Zi de post aspru."),
    (-1, "Sâmbăta Mare", TRI, "Coborârea la iad; noaptea are loc Slujba Învierii."),
    (0, "Sfintele Paști – Învierea Domnului", IMP, "Sărbătoarea sărbătorilor și praznicul praznicelor."),
    (1, "Lunea Paștelui (a doua zi de Paște)", PEN, ""),
    (2, "Marțea Paștelui (a treia zi de Paște)", PEN, ""),
    (5, "Vinerea Izvorul Tămăduirii", PEN, "Praznic al Maicii Domnului."),
    (7, "Duminica Tomii (Duminica Nouă)", PEN, "Duminica a II-a după Paști."),
    (8, "Paștele Blajinilor", PEN, "Pomenirea morților (Radonița)."),
    (14, "Duminica Mironosițelor", PEN, "Duminica a III-a după Paști."),
    (21, "Duminica Slăbănogului", PEN, "Duminica a IV-a după Paști."),
    (24, "Mijlocul Praznicului Cincizecimii", PEN, ""),
    (28, "Duminica Samarinencei", PEN, "Duminica a V-a după Paști."),
    (35, "Duminica Orbului", PEN, "Duminica a VI-a după Paști."),
    (39, "Înălțarea Domnului", IMP, "Joi, la 40 de zile după Paști."),
    (42, "Duminica Sfinților Părinți de la Sinodul I Ecumenic", PEN, "Duminica a VII-a după Paști."),
    (48, "Sâmbăta morților (Moșii de vară)", PEN, "Sâmbăta dinaintea Rusaliilor."),
    (49, "Rusaliile (Pogorârea Sfântului Duh)", IMP, "Duminica Mare; la 50 de zile după Paști."),
    (50, "Sfânta Treime (Lunea Sfântului Duh)", IMP, "Lunea după Pogorârea Sfântului Duh."),
]

# Ferestre (data iuliană) în care duminica primește un nume special.
# (lună, zi început, lună, zi sfârșit, nume)
FERESTRE_DUMINICI = [
    (9, 7, 9, 13, "Duminica dinaintea Înălțării Sfintei Cruci"),
    (9, 15, 9, 21, "Duminica după Înălțarea Sfintei Cruci"),
    (10, 11, 10, 17, "Duminica Sfinților Părinți de la Sinodul VII Ecumenic"),
    (12, 11, 12, 17, "Duminica Sfinților Strămoși"),
    (12, 18, 12, 24, "Duminica Sfinților Părinți (dinaintea Nașterii Domnului)"),
    (12, 26, 12, 31, "Duminica după Nașterea Domnului"),
    (1, 2, 1, 5, "Duminica dinaintea Botezului Domnului"),
    (1, 7, 1, 13, "Duminica după Botezul Domnului"),
]

# Duminici numerotate după Rusalii cu nume tradițional
DUMINICI_NUMITE = {
    1: "Duminica Tuturor Sfinților",
    17: "Duminica Cananeencei",
}

OFF_BISERICA = "Zi liberă legală în Republica Moldova (verifică Codul muncii, art. 111)."


def _stil_vechi(m: int, d: int) -> str:
    return f"{d} {LUNI[m - 1]}"


def _sunday_after_pentecost_events(jy: int) -> list:
    """Toate duminicile de la Rusalii (anul bisericesc jy) până la Duminica Vameșului din anul următor."""
    events = []
    pentecost = orthodox_easter(jy) + timedelta(days=49)
    limit = orthodox_easter(jy + 1) - timedelta(days=70)
    n, sunday = 1, pentecost + timedelta(days=7)
    while sunday < limit:
        _, jm, jd = gregorian_to_julian(sunday)
        special = [name for (m1, d1, m2, d2, name) in FERESTRE_DUMINICI
                   if (m1, d1) <= (jm, jd) <= (m2, d2)]
        nume = DUMINICI_NUMITE.get(n)
        ordinal = f"a {n}-a după Rusalii"
        # numele legat de o dată fixă (Crăciun, Botez, Înălțarea Crucii...) are prioritate
        principal = special[0] if special else nume
        titlu = f"{principal} ({ordinal})" if principal else f"Duminica {ordinal}"
        extra = f"{nume}. " if (nume and special) else ""
        desc = f"{extra}Duminica a {n}-a după Rusalii. Stil vechi: {_stil_vechi(jm, jd)}."
        events.append(Ev(sunday, None, titlu, desc, DUM))
        n += 1
        sunday += timedelta(days=7)
    return events


def build_ortodoxe(start: int, end: int) -> list:
    events = []
    for jy in range(start - 1, end + 1):
        easter = orthodox_easter(jy)

        # Praznice și sfinți cu dată fixă
        for m, d, titlu, cat, desc in FIXE:
            civil = julian_to_gregorian(jy, m, d)
            parts = [desc] if desc else []
            if (m, d) in ZILE_LIBERE_FIXE:
                parts.append(OFF_BISERICA)
            parts.append(f"Stil vechi: {_stil_vechi(m, d)}.")
            events.append(Ev(civil, None, titlu, " ".join(parts), cat))

        # Sâmbăta lui Dimitrie (Moșii de toamnă)
        for d in range(19, 26):
            civil = julian_to_gregorian(jy, 10, d)
            if civil.weekday() == 5:
                events.append(Ev(civil, None, "Sâmbăta lui Dimitrie (Moșii de toamnă)",
                                 f"Sâmbăta pomenirii morților dinaintea Sf. Dimitrie. "
                                 f"Stil vechi: {_stil_vechi(10, d)}.", DUM))

        # Zile mobile în funcție de Paște
        for off, titlu, cat, desc in MOBILE:
            parts = [desc] if desc else []
            if off in ZILE_LIBERE_PASTE:
                parts.append(OFF_BISERICA)
            events.append(Ev(easter + timedelta(days=off), None, titlu, " ".join(parts), cat))

        # Duminici de după Rusalii
        events += _sunday_after_pentecost_events(jy)

        # Perioade (evenimente pe mai multe zile)
        events.append(Ev(easter - timedelta(days=48), easter, "Postul Mare",
                         "Postul Sfintelor Paști (de la Lunea Curată până în Sâmbăta Mare).", POST))
        events.append(Ev(easter - timedelta(days=55), easter - timedelta(days=48),
                         "Săptămâna brânzei (Lăsatul secului de brânză)",
                         "Se mănâncă lactate și ouă, fără carne.", TRI))
        events.append(Ev(easter, easter + timedelta(days=7), "Săptămâna Luminată",
                         "Săptămâna de după Paști; nu se ține post.", PEN))
        apostles_start = easter + timedelta(days=57)
        apostles_end = julian_to_gregorian(jy, 6, 28)
        if apostles_start <= apostles_end:
            events.append(Ev(apostles_start, apostles_end + timedelta(days=1),
                             "Postul Sfinților Apostoli Petru și Pavel",
                             "Durează până în 28 iunie (stil vechi). Unii ani nu au acest post.", POST))
        for (m1, d1), (m2, d2), titlu in POSTURI_FIXE:
            events.append(Ev(julian_to_gregorian(jy, m1, d1),
                             julian_to_gregorian(jy, m2, d2) + timedelta(days=1), titlu,
                             f"Stil vechi: {_stil_vechi(m1, d1)} – {_stil_vechi(m2, d2)}.", POST))

    lo, hi = date(start, 1, 1), date(end, 12, 31)
    return [e for e in events if lo <= e.start <= hi]


# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=int, default=2025, help="primul an (implicit 2025)")
    parser.add_argument("--end", type=int, default=2040, help="ultimul an (implicit 2040)")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="folderul de ieșire")
    args = parser.parse_args()
    if args.start > args.end:
        parser.error("--start trebuie să fie <= --end")

    _selftest()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    laice = build_laice(args.start, args.end)
    path = args.out_dir / "Sarbatori_Laice_Moldova.ics"
    write_ics(path, "laic", "Sărbători laice Moldova",
              "Sărbători naționale și laice din Republica Moldova (calendar civil).", laice)
    print(f"{path}: {len(laice)} evenimente")

    ortodoxe = build_ortodoxe(args.start, args.end)
    path = args.out_dir / "Sarbatori_Ortodoxe_Moldova.ics"
    write_ics(path, "ortodox", "Sărbători ortodoxe Moldova (stil vechi)",
              "Calendarul bisericesc ortodox pe stil vechi: praznice, sfinți, duminici, posturi.", ortodoxe)
    print(f"{path}: {len(ortodoxe)} evenimente")


if __name__ == "__main__":
    main()
