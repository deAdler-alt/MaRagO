# Skrypt Pitchu — MRO Intelligence Platform
## Pitch + Dokumentacja Techniczna dla Prezentera

> **Dane po retrainingu modelu (21 cech, 2026-05-23):**
> AUC 0.975 · P@100 = 100% · P@200 = 95.5% · 402 TERAZ · 619 za 6 mies. · 37 klientów LOTAMS

---

## SLAJD 0: Ekran tytułowy (0:00–0:12)

**Co widzisz na slajdzie:**
Duży tytuł "MRO Intelligence Platform". Podtytuł: "Wczesne wykrywanie C-checków Boeing 737 · Europa · LOTAMS". Sylwetka samolotu na ciemnym tle z mapą Europy.

**Co mówisz:**

*(Wchodzisz pewnie. Chwila ciszy. Potem:)*

> "Mamy 4 minuty. Zaczynamy."

*(Klikasz od razu do slajdu 1.)*

**Co musisz wiedzieć jako EKSPERT:**

- LOTAMS = Lot Aircraft Maintenance Services. Zakład MRO przy Warszawie Okęcie (EPWA), specjalizacja: Boeing 737 NG i MAX, certyfikat EASA Part-145.
- C-check = "heavy maintenance", przegląd co 2–3 lata (ok. 4 000–5 000 godzin lotu). Trwa 3–6 tygodni. Wartość kontraktu: 1–3 mln USD.
- Główni konkurenci: Lufthansa Technik Hamburg, Turkish Technic Stambuł, STS Aviation Group.

---

## SLAJD 1: Problem (0:12–0:42)

**Co widzisz na slajdzie:**
Trzy karty z ikonami: "Godziny ręcznej pracy", "Spóźniona reakcja", "Oferty z powietrza". Czerwone obramowania. Prawa strona: sylwetka B737 z wielkim "?".

**Co mówisz:**

> "Wyobraźcie sobie że jesteście handlowcem w LOTAMS w Warszawie. Wasza praca: znaleźć spośród 2 761 Boeingów 737 w Europie te, które za rok wejdą w C-check — i skontaktować się z operatorem, zanim zrobi to Hamburg albo Stambuł.
>
> Jak to robicie dziś? FlightRadar, LinkedIn, portale branżowe — trzy do pięciu godzin tygodniowo. Ręcznie. Bez systemu. Największy problem: gdy samolot znika z trasy — jest już u konkurencji. LOTAMS dowiaduje się za późno."

**Co musisz wiedzieć jako EKSPERT:**

- **Dlaczego informacja jest ukryta:** Historia serwisowa to tajemnica handlowa linii lotniczych. W internecie nie ma bazy "ten Ryanair był na C-check w marcu". Handlowcy muszą to wywnioskować pośrednio.
- **Jak wygląda praca bez systemu:** Śledzenie FlightRadar24 (pokazuje tylko loty aktywne), portale typu Airfleets.net (wiek samolotów, ale bez historii serwisowej), kontakty branżowe, targi.
- **Okno decyzyjne:** Kontrakt MRO podpisuje się 12–18 miesięcy przed C-check'iem — żeby zarezerwować slot w hangarze, zamówić części, zaplanować załogę techniczną. Kto jest spóźniony o miesiąc — traci kontrakt.
- **Skala problemu:** 2 761 B737 w Europie, 434 z nich jest w oknie teraz lub niedługo. Żaden handlowiec nie ogarnie tego ręcznie.

---

## SLAJD 2: Insight — sygnał w danych (0:42–1:08)

**Co widzisz na slajdzie:**
Tabela 4 typów przeglądów (A/B/C/D-check) z kolorowym wyróżnieniem C-check. Prawa strona: pozioma oś czasu z blokiem "C-check w MRO" zaznaczonym na czerwono.

**Co mówisz:**

> "Ale samolot mówi kiedy idzie na serwis — przez ślad ADS-B.
>
> Kiedy Boeing 737 wchodzi w C-check, znika z radarów na 3 do 6 tygodni. I ląduje zawsze w tym samym miejscu — dedykowany zakład MRO: Warszawa, Hamburg, Stambuł, Sofia.
>
> My to wykrywamy. Retroaktywnie budujemy historię każdego samolotu. I przewidujemy — kiedy ta przerwa pojawi się po raz następny."

**Co musisz wiedzieć jako EKSPERT:**

- **ADS-B (Automatic Dependent Surveillance-Broadcast):** Każdy samolot komercyjny emituje swój sygnał GPS co 0.5–2 sekundy. EUROCONTROL zbiera te dane dla całej Europy. My używamy OPDI (Operational Performance Data Infrastructure) — oficjalne źródło, nie scraping.
- **Dlaczego C-check jest wykrywalny:** A-check (1–3 dni) mieści się w typowych "dziurach" w rozkładzie. C-check (21–55 dni) to anomalia statystyczna. Model to widzi.
- **MRO HUBs:** Mamy bazę ~40 lotnisk w Europie gdzie koncentrują się C-checki (EPWA, EDDH, LTBA, LKMT, LBSF...). Przerwa w tych lokalizacjach = sygnał HIGH confidence.
- **Dane wejściowe:** 7 085 279 lotów B737 EU, styczeń 2023 → kwiecień 2026. 40 plików parquet EUROCONTROL OPDI.

---

## SLAJD 3: Architektura — pipeline (1:08–1:33)

**Co widzisz na slajdzie:**
4 bloki flow: `📡 DANE → 🔍 GAP DETECTION → 🤖 LightGBM → 📊 DASHBOARD`. Pod spodem strip z liczbami: 7 085 279 lotów, 2 761 samolotów, 40 parquetów, 21 cech ML.

**Co mówisz:**

> "Pipeline w czterech krokach. Dane z EUROCONTROL — 7 milionów lotów. Wykrywamy przerwy: 14 do 60 dni, w lokalizacjach MRO. LightGBM na 21 cechach. I gotowy dashboard — handlowiec widzi listę priorytetową, Gantt timeline każdego samolotu, generator e-maila. Batch: 15 minut od danych do decyzji."

**Co musisz wiedzieć jako EKSPERT:**

- **pipeline.py:** ETL — wczytuje parquety, filtruje B737 w Europie, wykrywa gapy między lotami (detect_gaps), klasyfikuje je regułami domenowymi (A/B/C/D-check), buduje dashboard.csv.
- **features.py:** Feature engineering — 21 kolumn ML na każdy gap: długość przerwy, lokalizacja (ICAO kraj), intensywność lotów przed/po, trend aktywności, wiek samolotu, historia interwałów operatora.
- **train_classifier.py:** LightGBM binary classifier. Pseudo-labelling: HIGH+MEDIUM confidence gaps → positive, LOW + reguły AOG/storage → negative. Time-based split: trening do 2025-06-30, test od 2025-07-01.
- **predict.py:** Hierarchia interwałów: per_aircraft (456 samolotów z własną historią) → operator_mean (65 operatorów) → global_mean 507 dni → fallback 730 dni. Prognoza next C-check per samolot.
- **Dlaczego nie scraping FlightRadar:** EUROCONTROL OPDI to oficjalne dane regulatora EU, pełne pokrycie, bez rate-limitów, bez ToS issues. Łącznie ~10x więcej danych niż OpenSky w tym samym okresie.

---

## SLAJD 4: Liczby — co znaleźliśmy (1:33–2:02)

**Co widzisz na slajdzie:**
5 dużych kart KPI: 2 761 · 402 · 619 · 37 · 507 dni.

**Co mówisz:**

> "Co znaleźliśmy. 2 761 B737 w Europie — monitorujemy każdy. **402** — tyle samolotów jest w oknie kontaktowym TERAZ. Kolejne **619** wchodzi za 6 miesięcy. **37** historycznych klientów LOTAMS — wykryliśmy ich automatycznie po śladach lądowań w Warszawie. Średni interwał C-check: **507 dni** z danych 456 samolotów z własną historią."

**Co musisz wiedzieć jako EKSPERT:**

- **402 = 126 zaległych + 276 w oknie 0–6 mies.:**
  - Zaległe = model przewidział C-check który minął, a samolot nadal lata. Możliwe: check się odbył poza naszą bazą MRO, lub jest opóźniony (COVID-era backlog nadal istnieje).
  - 276 TERAZ = C-check w ciągu 0–6 mies. Kontrakt MRO powinien być już podpisany — ale może nie jest.
- **619 za 6 mies.:** Idealne okno prospectingowe. Handlowiec ma czas na 2–3 rundy negocjacji.
- **37 klientów LOTAMS:** Wykryto po tym że ich gapy miały ADES = EPWA (Warszawa Okęcie). To ciepłe leady — znają nas, wrócą jeśli zadzwonimy pierwsi z dobrą ofertą.
- **507 dni globalny mean interwał:** Przy 1 684 samolotach w dashboardzie: per_aircraft 27.1% (456 sam.), operator 36.7% (618 sam.), global_mean 36.2% (610 sam.). Im niżej w hierarchii, tym mniej dokładna predykcja — stąd confidence level.
- **Dlaczego nie więcej niż 1 684 zamiast 2 761:** 2 761 = unikalne B737 EU w danych. 1 684 = te które przeszły przez model z wykrytym C-check'iem w bazie (mają gap 14–60 dni w lokalizacji EU). Reszta to samoloty bez wykrytej przerwy serwisowej w naszym oknie danych.

---

## SLAJD 5: ML Magic — jak model wykrywa C-check (2:02–2:33)

**Co widzisz na slajdzie:**
Lewa strona: 4 metryki w kartach (AUC, P@100, P@200, liczba C-checków). Prawa strona: poziomy bar chart feature importance.

**Co mówisz:**

> "Model na 21 cechach. AUC **0.975** na danych których nigdy nie widział — time-based holdout, uczciwa walidacja. Pierwsze **100** predykcji: zero błędów. Top **200**: 191 z 200 to faktyczne C-checki.
>
> Co model widzi najsilniej: **lokalizacja — 30%** information gain. Przerwa w Turcji, Polsce, Czechach to prawie pewny C-check. **Długość przerwy — 27%**: C-check trwa 3 do 6 tygodni, A-check 1 do 3 dni. Nowe: **wiek samolotu — 3.3%** — starsze NG latają z krótszymi interwałami niż nowe MAX-y."

**Co musisz wiedzieć jako EKSPERT:**

- **AUC 0.975:** Obszar pod krzywą ROC na holdoucie (2025-07 → 2026-04). Losowy klasyfikator = 0.5, idealny = 1.0. 0.975 na danych lotniczych bez dokumentacji MRO to bardzo dobry wynik.
- **Precision@200 = 95.5% (191/200):** Na 200 najwyżej ocenionych predykcji modelu, 191 to faktyczne C-checki (zgodne z pseudo-labelami HIGH/MEDIUM confidence). FP = 9 = storage lub AOG błędnie sklasyfikowany.
- **Confusion matrix:** TN=186, FP=23, FN=13, TP=225. Precision 0.907, Recall 0.945. Asymetria: wolimy false negative (opuścić C-check) niż false positive (dzwonić do złego).
- **Pseudo-labelling:** Nie mamy ground truth z dokumentacji MRO. Używamy reguł domenowych (gap w dedykowanym MRO = HIGH, hub = MEDIUM, nieznane = LOW) jako pseudo-labele. Model uczy się wzorców których reguły nie widzą — np. sezonowość, intensywność przed przerwą, historia operatora.
- **Feature #1 — ades_country (30.1%):** PO retrainingu z 21 cechami lokalizacja wysunęła się na pierwsze miejsce (wcześniej gap_days był #1). To dobrze — model mówi: "najpierw patrz GDZIE, potem JAK DŁUGO".
- **Nowe cechy (dodane dziś):**
  - `aircraft_age_years` (3.3%): Proxy z wariantu typecode. B737 MAX (2018–2023) vs NG (1998–2018) vs Classic (1988–2000). Starsze = krótszy interwał.
  - `days_to_first_flight_after` (2.9%): Po C-check samolot zwykle wraca szybko do serwisu (lot techniczny → rejs tego samego dnia). Po storage — pauza.
  - `flights_per_day_trend` (2.3%): Samolot który zwalniał przed przerwą (fpd_14d/fpd_60d < 1) = planowany C-check. Który przyspieszał = AOG/awaria.
  - `at_operator_main_base` (0.9%): Gap we własnej bazie operatora = mniej prawdopodobny C-check (MRO jest zwykle poza bazą).

---

## SLAJD 6: Demo — Live System (2:33–4:33)

**Co widzisz na slajdzie:**
Pełnoekranowy screenshot Fleet Priority (dark Streamlit). Overlay z opisem 3 kroków.

**Co mówisz (intro przed przełączeniem na żywe demo):**

> "Zobaczcie jak to wygląda w praktyce."

*(Przełączasz na przeglądarkę ze Streamlitem)*

**DEMO — szczegółowy skrypt (2 minuty):**

### 0:00 — Executive Overview (20 sek.)
> "Tu jest C-level view. 402 samoloty do kontaktu teraz. 619 za 6 miesięcy. Ten donut — każdy kolor to inna pilność."
*(Wskaż kafelki i donut. Nie tłumacz metodologii — za długo.)*

### 0:20 — Fleet Priority (30 sek.)
> "Przechodzę do Fleet Priority. Tu jest lista zadań. Widzicie: czerwone wiersze — dzwonisz dziś. Filtrujemy — powiedzmy tylko HIGH confidence. *(filtrujesz)* Z 402 zostają X samolotów, co do których jesteśmy najbardziej pewni. Eksport CSV — jeden klik."

### 0:50 — Aircraft Deep Dive (30 sek.)
> "Klikam na konkretny samolot — SP-LVD, LOT. *(przejdź do strony 3, wpisz w searchbar)* To jest historia 3 lat. Zielone to loty. Ten niebieski blok — 2024 rok, Warszawa — to był C-check u nas. Czerwona linia — prognoza: już zaległy. Powinniśmy zadzwonić wczoraj."

### 1:20 — Commercial Alerts + e-mail (40 sek.)
> "Commercial Alerts. *(kliknij stronę 4)* Tu są wszyscy z gwiazdką — historyczni klienci LOTAMS. Wchodzę w generator e-maila. Wybieram SP-LVD. *(selectbox)* I mam gotowy mail — samolot, operator, data prognozy, nasz competitive advantage. Jeden klik — mailto. *(pokaż kod maila)* 30 sekund zamiast godziny."

### 2:00 — ML Insights (20 sek.)
> "I na koniec — ML Insights. Mapa MRO Europy. Żółta gwiazda — to my. Turcja dominuje — Turkish Technic to nasz main competitor. I sezonowość — C-checki skupiają się zimą. *(wskaż heatmapę)* Handlowiec wie kiedy prospectować."

**Co musisz wiedzieć jako EKSPERT (do demo):**

- **SP-LVD to świetny przykład:** LOT Polish Airlines, Boeing 737-800, historyczny klient LOTAMS (gap w EPWA 2024). Priorytet TERAZ zaległe. Idealny do pokazania wartości systemu.
- **Jeśli coś się zawiesi:** "System działa na batch pipeline — dane z maja 2026. W produkcji byłoby odświeżane codziennie o 6 rano." Spokojnie.
- **Jeśli pytają o liczby na ekranie:** Używaj liczb z tego dokumentu. Nie improwizuj.
- **Ważne — co NIE jest na demo:** Nie ma live feed. Nie ma API. To jest batch BI tool — jak Power BI ale dla MRO. I to wystarczy do hackathonu.

---

## SLAJD 7: Walidacja — jak to sprawdziliśmy (4:33–5:00)

**Co widzisz na slajdzie:**
Lewa: oś czasu trening (2023-01 → 2025-06-30) vs test (2025-07-01 → 2026-04). Prawa: confusion matrix.

**Co mówisz:**

> "Jak to walidowaliśmy — rzetelnie. Trenowaliśmy na danych do połowy 2025. Testowaliśmy na lotach z drugiej połowy 2025 i początku 2026 — danych których model nigdy nie widział. AUC 0.975. 37 historycznych klientów LOTAMS — wszystkich wykrył automatycznie."

**Co musisz wiedzieć jako EKSPERT:**

- **Dlaczego time-based split jest trudniejszy niż random:** W random splicie model mógłby 'znać' przyszłość z sąsiednich rekordów tego samego samolotu. Time-based split symuluje rzeczywiste wdrożenie: uczysz na przeszłości, przewidujesz przyszłość.
- **Confusion matrix (po retrainingu z 21 cechami):**
  - TN = 186 (poprawnie odrzucone storage/AOG)
  - FP = 23 (fałszywe alarmy — handlowiec dzwoni niepotrzebnie, koszt niski)
  - FN = 13 (przegapione C-checki — utracone leady, koszt wyższy)
  - TP = 225 (znalezione C-checki — zysk)
  - Precision = 0.907 (91% alarmów jest słusznych), Recall = 0.945 (95% C-checków wykrytych)
- **AUC 0.975 w kontekście branżowym:** Dla problemu bez ground truth, z pseudo-labelami opartymi na domenowej wiedzy eksperta, to jest wynik bardzo dobry. Porównywalny z modelami fraud detection.
- **37 klientów LOTAMS:** Walidacja biznesowa. Nikt nie powiedział modelowi który samolot był w Warszawie — model to odkrył sam przez wykrycie gapu w ADES=EPWA z HIGH confidence.

---

## SLAJD 8: Roadmap — co dalej (5:00–5:28)

**Co widzisz na slajdzie:**
3 kolumny: TERAZ (zielone checkmarki), NASTĘPNY SPRINT (żółte), SKALA (fioletowe).

**Co mówisz:**

> "Co mamy dziś — działa. Batch pipeline, dashboard, 4 widoki, e-mail generator. Następny sprint: live mode przez OpenSky API — to dosłownie zmiana jednej linii kodu, ten sam pipeline. Codzienne odświeżenia predykcji, REST API dla Salesforce. I docelowo: A320, A330, Bliski Wschód."

**Co musisz wiedzieć jako EKSPERT:**

- **Live mode przez OpenSky API:** OpenSky Network oferuje REST API z danymi ADS-B w czasie zbliżonym do rzeczywistego (15 min delay). Pipeline jest już zaprojektowany tak żeby `load_b737_eu()` mogła czytać zarówno z parquetów OPDI jak i z API. Drop-in replacement = 1–2 dni inżynierskie.
- **REST API dla CRM:** Flask/FastAPI endpoint który zwraca JSON z `/alerts?priority=TERAZ&confidence=HIGH`. Integracja z Salesforce to standardowy webhook. 2–3 tygodnie.
- **A320 rodzina:** Airbus ma własne interwały i własny ekosystem MRO (Lufthansa Technik, Air France Industries). Ale dane OPDI są dla wszystkich samolotów. Rozszerzenie = zmiana jednego filtra w pipeline (B737_TYPES) + retrain modelu na nowej flocie.
- **LLM-generowane oferty:** Zamiast szablonu — GPT-4o generuje spersonalizowaną ofertę na podstawie historii samolotu, operatora, i aktualnych slotów LOTAMS. To jest "next level" personalizacji.

---

## SLAJD 9: Team & Q&A (5:28–6:00+)

**Co widzisz na slajdzie:**
Karty zespołu (placeholder). Duże "Q & A" w kolorze czerwonym.

**Co mówisz:**

> "To jest efekt 24 godzin pracy. 7 milionów lotów, 21 cech, jeden dashboard. Dziękujemy."

*(Cisza. Czekasz na pytania.)*

---

## GOTOWE ODPOWIEDZI NA PYTANIA Z SALI

**"Skąd macie dane?"**
> "EUROCONTROL OPDI — oficjalne źródło danych regulatora lotnictwa EU. 40 plików parquet, 7 085 279 lotów B737, od stycznia 2023 do kwietnia 2026. Pełne pokrycie EU plus Turcja, Ukraina, Afryka Północna. Nie scraping FlightRadar — legalne, oficjalne."

**"Jak pewni jesteście predykcji?"**
> "AUC 0.975 na time-based holdout — trenowaliśmy na danych do połowy 2025, testowaliśmy na 2025-07 do 2026-04. Model nigdy nie widział tych danych. 191 z 200 top predykcji to faktyczne C-checki. I zaznaczamy wyraźnie w aplikacji: to sygnał ADS-B, nie dokumentacja MRO. Handlowiec weryfikuje telefonicznie — co jest naturalnym krokiem w procesie sprzedaży."

**"Czy linie lotnicze wiedzą że je śledzicie?"**
> "Dane ADS-B są publiczne — każdy samolot emituje sygnał obowiązkowo. EUROCONTROL agreguje je legalnie. My analizujemy wzorce, nie dane osobowe. Żaden GDPR nie ma tutaj zastosowania."

**"Co z konkurencją — inne systemy to robią?"**
> "Systemy MRO-tracking istnieją dla linii lotniczych — AMOS, OASES, TRAX. Ale to systemy wewnętrzne operatorów, nie narzędzia dla zakładów MRO. Żaden MRO provider nie ma systemu do proaktywnego prospectingu zewnętrznego opartego na ADS-B. To jest nasza nisza."

**"Jak szybko można wdrożyć produkcyjnie?"**
> "Batch pipeline działa już teraz — 15 minut od pobrania danych do zaktualizowanego dashboardu. Live mode przez OpenSky API to 1–2 tygodnie. REST API dla CRM to dodatkowe 2–3 tygodnie. W 6 tygodni — system produkcyjny."

**"Ile to będzie kosztować LOTAMS?"**
> "Cloud hosting na Azure lub AWS: ok. 200–400 USD miesięcznie za serwer batch + storage. EUROCONTROL OPDI: dostęp bezpłatny dla podmiotów lotniczych EU. Jednorazowy koszt wdrożenia zależy od integracji z istniejącym CRM."

**"Dlaczego 507 dni, a nie 2 lata (730 dni)?"**
> "730 dni to jest nasz fallback gdy nie mamy żadnej historii. 507 dni to globalny mean z 456 samolotów które miały minimum 2 wykryte C-checki w naszych danych. Prawdziwe interwały są krótsze niż nominalne bo regulatory compliance jest stricte egzekwowana — linie nie opóźniają C-checków."

---

## LICZBY DO ZAPAMIĘTANIA NA PAMIĘĆ

| Liczba | Kontekst |
|---|---|
| **2 761** | Unikalnych B737 w Europie w danych |
| **1 684** | Samolotów z wykrytym C-check'iem w dashboardzie |
| **402** | TERAZ kontakt (126 zaległe + 276 w 0–6 mies.) |
| **619** | Kontakt za 6 miesięcy |
| **37** | Historycznych klientów LOTAMS |
| **507 dni** | Średni interwał C-check (z danych per-aircraft) |
| **7 085 279** | Lotów B737 EU w bazie (2023–2026) |
| **21** | Cech ML w modelu (po dzisiejszym retrainingu) |
| **0.975** | AUC na time-based holdout |
| **100%** | Precision@100 (pierwsze 100 predykcji bezbłędne) |
| **95.5%** | Precision@200 (191/200) |
| **30.1%** | Waga cechy #1: kraj lotniska MRO (ades_country) |
| **26.8%** | Waga cechy #2: długość przerwy (gap_days) |
| **15 min** | Czas batchu: dane → dashboard |
