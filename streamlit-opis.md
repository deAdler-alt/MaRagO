# Przewodnik po Demo — MRO Intelligence Platform
## Co mówić na każdym panelu Streamlit

---

## STRONA 1: Executive Overview (`main.py`)

> To jest C-level view — 4 sekundy i wiadomo co robić.

### KPI tiles (górny rząd — 5 liczb)

> "Monitorujemy 2 761 samolotów B737 w całej Europie. Z tego 1 469 aktywnych. Te **402 czerwone** — to są twoi klienci na dziś. Nie za miesiąc — dziś."

### Donut chart (rozkład priorytetów)

> "Każdy sektor to pilność kontaktu. Czerwony to okno zagrożone — C-check się zbliża lub minął. Żółty to idealne okno prospectingowe — 6 do 12 miesięcy, handlowiec ma czas zbudować relację przed przetargiem."

### Metodologia (prawe boksy — 4 action boxy)

> "TERAZ zaległe znaczy: nasz model przewidział C-check, a samolot nadal lata. Albo check się odbył i nie mamy sygnału ADS-B bo lotnisko nie jest w naszej bazie. Dzwonisz i pytasz.
>
> TERAZ to ostatnie okno — kontrakty MRO podpisuje się 12 miesięcy przed terminem. Jesteś spóźniony, ale jeszcze możesz.
>
> 6 miesięcy to idealne okno. Wysyłasz wstępną ofertę, potwierdzasz slot, budujesz relację zanim klient pójdzie do Hamburga lub Stambułu."

### Top 10 tabela

> "To jest lista zadań dla handlowca na ten tydzień. Posortowana według terminu — im wyżej, tym pilniej. Czerwone wiersze oznaczają: dzwonisz dziś."

### Operator breakdown (dolny bar chart)

> "A tu widzisz który operator ma największą koncentrację samolotów w oknie decyzyjnym. Ryanair, Turkish Airlines, Wizz Air — to są twoje cele kontraktowe. Nie jeden samolot — pakiet na kilka lat."

---

## STRONA 2: Fleet Priority (`01_fleet.py`)

> To jest narzędzie do codziennej pracy handlowca.

### Sidebar — filtry

> "Handlowiec rano otwiera system, filtruje po swoim regionie — powiedzmy Polska, Czechy, Węgry — i widzi dokładnie ile samolotów w jego obszarze potrzebuje serwisu w najbliższych miesiącach. Slider ML probability pozwala mu zobaczyć tylko te z najwyższą pewnością modelu — zero szumu."

### Tabela (główna)

> "Każdy wiersz to jeden samolot. Kolor mówi wszystko — red, żółty, niebieski.
>
> Mamy: rejestrację, operatora, kiedy był ostatni C-check, kiedy jest prognoza, ile miesięcy zostało. Generacja samolotu — MAX vs NG vs Classic — bo interwały są różne, MAX lata dłużej między przeglądami. MRO w której samolot był ostatnio — czyli wiemy u kogo jest nasza konkurencja i możemy przygotować kontrargumenty."

### Donut mini + confidence bar (prawa strona)

> "Małe wykresy po prawej dają instant view na jakość listy po filtrach — ile z tych samolotów mamy z HIGH confidence, czyli faktycznie wykrytych w dedykowanym zakładzie MRO. HIGH confidence to niemal pewny C-check, nie szacunek."

### Eksport

> "Jeden klik i masz CSV który możesz wrzucić do Salesforce, wysłać mailem do teamu, czy zaimportować do dowolnego systemu CRM. Nie trzeba przepisywać niczego ręcznie."

---

## STRONA 3: Aircraft Deep Dive (`02_aircraft.py`)

> To jest due-diligence przed rozmową z klientem. Wchodzisz tutaj zanim zadzwonisz.

### Gantt timeline (oś czasu samolotu)

> "To jest historia tego samolotu z ostatnich 3 lat, w jednym widoku.
>
> Zielone paski to okresy aktywnych lotów. Kolorowe prostokąty to wykryte przerwy w aktywności ADS-B. Zielony prostokąt — HIGH confidence — byliśmy w dedykowanym MRO, prawie pewny C-check. Żółty prostokąt — ambiguous, ale ML ocenił jako C-check na podstawie 21 cech. Żółty wąski — storage lub AOG, model odrzucił jako C-check.
>
> Czerwona pionowa linia — prognoza kiedy następny C-check. Szara przerywana — dziś.
>
> Proszę zwrócić uwagę: ten samolot był w Warszawie w 2024 roku. To nasz historyczny klient. Wraca za X miesięcy. Wiemy o tym zanim on sam wysłał zapytanie ofertowe."

### 6 KPI kart (górny rząd)

> "Ostatni C-check — kiedy i gdzie dokładnie. Prognoza — kiedy następny, z dokładnością do kwartału. 'Za miesięcy' — ile zostało od dziś. Interwał — i to jest ważne — skąd pochodzi ta liczba: z historii tego konkretnego samolotu, ze średniej jego operatora, czy z globalnej średniej dla B737. Wiemy jak dokładna jest nasza predykcja."

### Kontekst sprzedażowy (prawa kolumna)

> "To jest brief przed rozmową. Historyczna analiza — ile przerw wykryliśmy dla tego samolotu, jaki najwyższy ML probability. I sugerowany termin kontaktu — 12 miesięcy przed prognozowanym C-check'iem. System mówi ci kiedy wysłać pierwszą ofertę, żebyś nie był spóźniony."

---

## STRONA 4: Commercial Alerts (`03_alerts.py`)

> To jest centrum dowodzenia całego działu sprzedaży.

### Tab 1 — Lista alertów

> "Wszystkie samoloty w oknie decyzyjnym, w jednym widoku, posortowane według priorytetu. Gwiazdka oznacza historycznego klienta LOTAMS — to nasz priorytet absolutny. Znamy ich samoloty, znamy interwały serwisowe, oni znają jakość naszej pracy. To jest ciepły lead, nie zimny."

### Tab 2 — Per operator

> "Podejście account-based. Ryanair ma X samolotów w oknie decyzyjnym — to jest okazja do negocjacji kontraktu na pakiet, nie pojedyncze zlecenia. Tu widzisz z którym VP of Engineering rozmawiasz i jak duże jest to potencjalne zamówienie. Frame rozmowy zmienia się zupełnie."

### Tab 3 — Generator e-mail

> "To jest to co najbardziej podoba się handlowcom w terenie. Wybierasz rejestrację z listy, klikasz — i dostajesz gotowy, spersonalizowany mail. Wstawia konkretny samolot, operatora, prognozowaną datę C-check'u, ostatni check z lokalizacją, nasz competitive advantage versus Hamburg czy Stambuł. Jeden klik — mailto link i otwiera się klient pocztowy z wypełnionym tematem i treścią. Handlowiec wysyła w 30 sekund."

### Weekly digest

> "Eksport Markdown — można wkleić bezpośrednio na Slacka lub Teams jako tygodniowy brief dla całego działu sprzedaży. Kto ma zadzwonić do kogo, w tym tygodniu, z jakimi argumentami. Zero overhead administracyjnego."

---

## STRONA 5: ML Insights (`04_insights.py`)

> To jest transparentność modelu — dla jury, dla CTO, dla każdego kto pyta "skąd wiecie".

### Mapa MRO Europy

> "Każda bańka to lotnisko gdzie wykryliśmy C-checki B737 w danych. Rozmiar bańki proporcjonalny do liczby wykrytych przeglądów. Żółta gwiazda to my — LOTAMS Warszawa.
>
> Turcja dominuje — Turkish Technic w Stambule to jest nasz główny competitor w Europie Środkowej. To widać wprost w danych. Wielka Brytania, Niemcy, Holandia — tam są kolejne koncentracje. Ta mapa to jest nasz competitive landscape."

### Heatmapa sezonowości

> "C-checki mają wyraźną sezonowość — widać ją w tym heatmapie. Szczyt zimowy — październik do marca. Lato to minimum, bo samoloty latają non-stop i zarabiają, nie serwisują. To znaczy jedno dla handlowca: prospectuj aktywnie w sezonie jesienno-zimowym na C-checki planowane rok później. Nie latem — wtedy jest za późno."

### Feature Importance (wykres poziomy)

> "Model mówi nam dlaczego podjął decyzję — to jest pełna transparentność.
>
> Najsilniejszy sygnał — 31% information gain: długość przerwy. C-check trwa 21 do 55 dni, A-check 1 do 3 dni. To jest fundamentalne rozróżnienie.
>
> Drugi sygnał — 28%: kraj lotniska MRO. Przerwa w Turcji, Polsce, Czechach, Wielkiej Brytanii to niemal pewny C-check — to są kraje ze specjalistycznym MRO B737.
>
> Trzeci sygnał — 9%: intensywność lotów przed przerwą. Charter który lata 6 lotów dziennie a potem nagle staje — to storage zimowy. Samolot który zwalniał stopniowo — to planowany C-check. Model to widzi.
>
> AUC 0.975 na danych których model nigdy nie widział — to jest time-based holdout, nie random split. Uczciwa walidacja."

### Histogram predykcji

> "Ten dwumodalny rozkład to jest wizualny dowód że model działa. Dwa wyraźne klastry — szare po lewej to storage i AOG, czerwone po prawej to C-checki. Próg 0.7 odcina nam 95% precyzji na top 200 predykcjach. 191 z 200 najlepszych predykcji to faktyczne C-checki."

---

## JEDNO ZDANIE NA KONIEC DEMO

> "Handlowiec LOTAMS zamiast 3 godzin dziennie na FlightRadarze i LinkedIn — otwiera dashboard, 5 sekund, wie kto potrzebuje serwisu, kiedy zadzwonić i co napisać. To jest efekt tej platformy."

---

## PYTANIA Z SALI — gotowe odpowiedzi

**"Skąd macie dane?"**
> "EUROCONTROL OPDI — to jest oficjalne źródło danych o ruchu lotniczym w Europie, nie scraping FlightRadar. 7 milionów lotów B737, od 2023 do dziś. Pełne pokrycie EU plus Turcja, Ukraina, Afryka Północna."

**"Jak pewni jesteście predykcji?"**
> "AUC 0.975 na time-based holdout — to znaczy trenowaliśmy na danych do połowy 2025, testowaliśmy na lotach z drugiej połowy 2025 i początku 2026. Model nigdy nie widział tych danych. 191 z 200 top predykcji to faktyczne C-checki. Nie mamy dokumentacji MRO — używamy sygnału ADS-B jako proxy, co zaznaczamy wprost w footerze każdego widoku."

**"Co z konkurencją — inne systemy to robią?"**
> "Systemy MRO-tracking istnieją dla linii lotniczych — AMOS, OASES — ale to systemy wewnętrzne operatorów. Żaden zakład MRO nie ma narzędzia do proaktywnego prospectingu opartego na zewnętrznych danych ADS-B. To jest nasza nisza."

**"Jak szybko można to wdrożyć produkcyjnie?"**
> "Batch pipeline działa już teraz — 15 minut od pobrania danych do zaktualizowanego dashboardu. Następny krok to live mode przez OpenSky API — drop-in replacement, ten sam kod. Dwa tygodnie inżynierskie."
