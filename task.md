# Kompendium Projektu: MRO Prediction Platform

## 🎯 Cel Projektu
Zbuduj szczegółowy dashboard, który dla każdego samolotu Boeing 737 w Europie:
- pokazuje historię aktywności lotniczej,
- wykrywa okresy bez lotów (potencjalne przeglądy serwisowe),
- klasyfikuje ich typ (A-check, B-check, C-check, D-check),
- **przewiduje:** kiedy, który samolot i jakiej linii lotniczej będzie w następnym oknie serwisowym.

---

## 🚨 Problem do rozwiązania
- **Brak automatyzacji:** LOTAMS wie, że samoloty potrzebują serwisu. Jednak ręczne znalezienie *KIEDY* i *KTÓRY* z ponad 2 000 samolotów w Europie wchodzi w okno serwisowe, to godziny analizy portali, baz danych i poleganie na intuicji handlowca.
- **Utracone szanse i spóźniona reakcja:** Gdy samolot znika z trasy na 3-6 tygodni - jest już za późno (jest już u konkurencji). Brak systemu wczesnego wykrywania.
- **Żmudny prospecting:** Szukanie klientów bez usystematyzowanych danych to cotygodniowy maraton przeglądania portali, LinkedIn i newsów branżowych.
- **Czasochłonne wyceny:** Przygotowywanie ofert pochłania kolejne godziny (manualne zbieranie danych o flocie klienta, historii przeglądów, kalkulacja zakresu prac).

---

## 🛠️ Stan obecny vs Proponowane rozwiązania

### ❌ Jak to wygląda dziś (Ścieżka biznesowa / PM)
- Ręczne przeszukiwanie portali, LinkedIn, FlightRadar.
- Decyzja "do kogo dzwonić" oparta na intuicji i doświadczeniu.
- Historia serwisów samolotu to w branży tajemnica handlowa. **Otwartych danych o tym nie ma.**

### ✅ Przykładowe rozwiązania (Ścieżka techniczna)
- **Dashboard per samolot** – agregacja historii lotów ADS-B, wykryte okresy bez aktywności, automatyczna klasyfikacja typu check.
- **Tabela priorytetowa** – lista B737 w Europie posortowana według zbliżającego się okna decyzyjnego na najważniejszy `C-check`.
- **Wykres osi czasu** – wizualizacja pokazująca kiedy dany samolot latał, kiedy miał przerwy i jak długo (aby odróżnić krótki A-check od długiego C-check).
- **Alert handlowy** – powiadomienia o maszynach wchodzących w okno decyzyjne w ciągu najbliższych 6–12 miesięcy, wraz z sugerowaną datą pierwszego kontaktu.

---

## ✈️ Klasyfikacja typu przeglądu (Na podstawie przerw w danych ADS-B)

| Typ | Częstotliwość | Przerwa w ADS-B | Sygnał w danych | Wartość dla LOTAMS |
|---|---|---|---|---|
| **A-check** | co 500–600 h (kilka tygodni) | **1–3 dni** | Krótka przerwa, samolot wraca na tę samą bazę, brak zmiany lokalizacji. | **Brak** - LOTAMS nie wykonuje A-check. |
| **B-check** | co 4–8 mies. (coraz rzadszy) | **4–5 dni** | Przerwa kilkudniowa; wiele linii eliminuje B-check i łączy z C-check. | **Rzadki** - większość linii go pomija. |
| **C-check ⭐️** | co 2–3 lata (~4k–5k h) | **3–6 tygodni** | Długa przerwa bez lotów; samolot pojawia się w lokalizacji MRO (np. Warszawa, Hamburg, Stambuł). | **Główny produkt LOTAMS - to tu leżą pieniądze i kontrakt.** |
| **D-check** | co ~12 lat (25k+ h) | **1–3 miesiące** | Bardzo długa przerwa; samolot może nie wrócić do poprzedniego operatora (lease return/złomowanie). | **Rzadki** - jeden raz w życiu samolotu. |

---

## 📊 Przykładowy Output Dashboardu (Boeing 737 w Europie)

*(Dane poglądowe - rzeczywiste dane należy pobrać z OpenSky Network i Airfleets.net)*

| Rejestracja | Operator | Wiek | Ostatnie okno | Czas trwania | Typ check | Prognoza C-check | Priorytet |
|---|---|---|---|---|---|---|---|
| **EI-FRK** | Ryanair | 8 lat | Mar 2024 | 29 dni | `C-check` | **Q1 2027** | 🔴 TERAZ |
| **SP-LVB** | LOT Polish | 6 lat | Nov 2023 | 34 dni | `C-check` | **Q2 2026** | 🟡 6 mies. |
| **OE-LNT** | TUI Fly | 5 lat | Jan 2024 | 2 dni | `A-check` | **Q4 2026** | 🔵 12 mies. |
| **G-JZHF** | Jet2 | 11 lat | Sep 2022 | 26 dni | `C-check` | **Q3 2025** | 🔴 TERAZ |
| **OO-JAX** | TUI Fly BE| 9 lat | Lut 2024 | 4 dni | `B-check` | **Q1 2026** | 🟡 6 mies. |
| **TC-JFF** | SunExpress| 14 lat| Dec 2021 | 89 dni | `D-check` | **2030+** | ⚪ Daleko |

---

## 💡 O czym pamiętać (Kluczowe założenia hackathonu)
1. **Sygnał pośredni:** Dane ADS-B to nie jest twarda dokumentacja. Wnioskujesz o serwisie na podstawie anomalii – przerw w aktywności lotniczej.
2. **Skup się na C-check:** To najważniejszy produkt dla LOTAMS (duże zyski). A-check linie robią przeważnie samodzielnie.
3. **Okno decyzyjne:** Konieczność wyprzedzenia rynku. LOTAMS musi wiedzieć o C-checku **6–18 miesięcy przed przeglądem** (podejście proaktywne, a nie reaktywne).
4. **Zakres MVP:** Tylko model **Boeing 737** i tylko **Europa**. Zbiór ponad 2000 maszyn to idealny, wystarczający i domknięty dataset na 24 godziny pracy.

---

## 🗄️ Kluczowe dane (Darmowe)

* **OpenSky Network:** Historyczne archiwum danych ADS-B (dostępne przez REST API).
* **ADS-B Exchange:** Surowe, niefiltrowane dane bez ukrywania samolotów.
* **Airfleets.net:** Metadane – floty poszczególnych linii, wiek maszyn, daty dostaw.
* **EASA Type Certificates:** Oficjalne interwały serwisowe dla samolotów z rodziny 737.
* **Simple Flying:** Uzupełniające newsy branżowe, informacje o dostawach i zmianach operatorów.

### 💻 Proponowany Tech Stack:
- `Python / Pandas` (agregacja i obróbka danych czasowych)
- `Streamlit / Plotly` (szybkie budowanie interaktywnego interfejsu i dashboardu)
- `OpenSky API` (surowe pozycje i trajektorie)
- `Predykcja ML` (algorytmy klasyfikujące przerwy i modelujące przyszłe okna serwisowe)
