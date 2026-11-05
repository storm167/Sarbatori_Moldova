# Sărbători Moldova – Calendare .ICS 📅

Calendare gata de importat în Google Calendar, Apple Calendar sau Outlook, în **două variante** independente:

| Fișier | Conținut |
|---|---|
| **`Sarbatori_Laice_Moldova.ics`** | Sărbători naționale și laice (calendar civil): Anul Nou, 8 Martie, Ziua Muncii, Ziua Europei/Victoriei, Ziua Independenței, Limba Noastră, Crăciunul pe stil nou etc. |
| **`Sarbatori_Ortodoxe_Moldova.ics`** | Calendarul bisericesc ortodox **pe stil vechi**: praznice împărătești și ale Maicii Domnului, sfinți mari, **fiecare duminică cu numele ei**, posturi, Triodul și Penticostarul. |

Poți importa unul singur sau pe amândouă. Dacă importi ambele, nu apar duplicate: Crăciunul de pe 25 decembrie (stil nou) e în calendarul laic, iar cel de pe 7 ianuarie (stil vechi) în cel ortodox.

Intervalul implicit este **2025–2040**.

---

## Ce conține calendarul ortodox

Totul se **calculează automat** din data Paștelui ortodox, nu este scris de mână pentru fiecare an.

- **Triodul**: Duminica Vameșului și a Fariseului, Fiului Risipitor, Înfricoșătoarei Judecăți (Lăsatul secului de carne), Izgonirii lui Adam din Rai (Lăsatul secului de brânză), cele 5 duminici din Postul Mare, Sâmbăta Acatistului, Sâmbăta lui Lazăr, Floriile și toată Săptămâna Patimilor.
- **Penticostarul**: Paștele, Săptămâna Luminată, Duminica Tomii, Paștele Blajinilor, Mironosițele, Slăbănogul, Samarineanca, Orbul, Sfinții Părinți de la Sinodul I, Înălțarea, Rusaliile și Sfânta Treime.
- **Duminicile după Rusalii**: numerotate (a 1-a, a 2-a…) până la începutul Triodului. Unele au și un nume special calculat după data iuliană: Duminica Tuturor Sfinților, Duminica dinaintea/după Înălțarea Sfintei Cruci, Sfinții Părinți de la Sinodul VII, Sfinții Strămoși, Sfinții Părinți, duminica după Naștere, înainte și după Botez, Duminica Cananeencei.
- **Posturi** (ca evenimente pe mai multe zile): Postul Mare, Postul Sfinților Apostoli (există doar în anii în care Paștele nu e prea târziu), Postul Adormirii și Postul Crăciunului.
- **Praznice cu dată fixă**, trecute pe stil vechi: de exemplu, Crăciunul din 25 decembrie cade pe **7 ianuarie**. Fiecare eveniment are în descriere data pe stil vechi.

Zilele libere legale legate de biserică sunt marcate în descriere (7–8 ianuarie, Paște, Lunea Paștelui, Paștele Blajinilor).

> ⚠️ Lista zilelor libere o poți verifica în Codul muncii al Republicii Moldova (art. 111). Eu am marcat ce știam, dar legislația se mai schimbă.

---

## Cum le adaugi în calendar 🗓️

1. Descarcă fișierele `.ics`:
   - [Sarbatori_Laice_Moldova.ics](https://raw.githubusercontent.com/storm167/Sarbatori_Moldova/master/Sarbatori_Laice_Moldova.ics)
   - [Sarbatori_Ortodoxe_Moldova.ics](https://raw.githubusercontent.com/storm167/Sarbatori_Moldova/master/Sarbatori_Ortodoxe_Moldova.ics)
2. Importă-le:
   - **Google Calendar**: [calendar.google.com](https://calendar.google.com) → Setări → *Import & export* → alege fișierul și calendarul de destinație.
   - **Apple Calendar**: dublu-click pe fișier (sau trimite-l pe iPhone prin AirDrop/e-mail) → „Adaugă în Calendar”.
   - **Outlook**: Calendar → *Adaugă calendar* → *Din fișier*.

💡 Recomand să creezi un **calendar nou** pentru fiecare fișier (de exemplu „Sărbători ortodoxe”). Așa îl poți ascunde sau șterge dintr-un singur click. Evenimentele au UID stabil, deci reimportarea aceluiași fișier nu creează duplicate.

Fișierul ortodox are circa 1700 evenimente. Dacă Google Calendar refuză importul, generează un interval mai scurt (vezi mai jos).

---

## Pentru dezvoltatori 💻

Nu e nevoie de nicio bibliotecă externă, doar Python 3.

```bash
python3 generate_calendars.py                              # 2025–2040
python3 generate_calendars.py --start 2025 --end 2060      # alt interval
python3 generate_calendars.py --out-dir out                # alt folder de ieșire
```

Scriptul rulează un autotest (date cunoscute ale Paștelui, conversia iulian ↔ gregorian) înainte de a scrie fișierele.

Cum modifici conținutul, toate în `generate_calendars.py`:

- `LAICE`: sărbători laice cu dată fixă.
- `FIXE`: praznice și sfinți cu dată fixă, în data **iuliană** (25 dec, nu 7 ian). Conversia în data civilă se face singură.
- `MOBILE`: zile legate de Paște (decalaj în zile față de Paște).
- `FERESTRE_DUMINICI` și `DUMINICI_NUMITE`: nume speciale pentru duminicile de după Rusalii.

Folderul `_vechi/` conține scripturile și fișierele din prima versiune (cu bug-urile corectate acum), păstrate doar pentru referință.

### Contribuie 🙌

Ai găsit o sărbătoare lipsă sau o dată greșită? Deschide un „Issue” pe [GitHub](https://github.com/storm167/Sarbatori_Moldova/issues).
