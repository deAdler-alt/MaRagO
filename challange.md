# MRO Prediction Platform

Zbuduj szczegółowy dashboard który dla każdego Boeinga 737 w Europie pokazuje historię aktywności lotniczej, wykrywa okresy bez lotów (potencjalne przeglądy), klasyfikuje ich typ i przewiduje - kiedy, który samolot, jakiej linii będzie w następnym oknie serwisowym.

## PROBLEM DO ROZWIĄZANIA

* LOTAMS wie że samoloty potrzebują serwisu - ale znalezienie KIEDY i KTÓRY z 2 000+ samolotów w Europie to godziny ręcznej analizy portali, baz danych i intuicji handlowca
* Gdy samolot znika z trasy na 3-6 tygodni - jest już u konkurencji. LOTAMS dowiaduje się za późno, nie ma systemu wczesnego wykrywania
* Sporą częścią pracy handlowca jest szukanie klientów i szans - prospecting bez systemu to tygodniowy maraton przeglądania portali, LinkedIn i newsów branżowych
* Pisanie wycen pochłania kolejne godziny - każda oferta wymaga manualnego zebrania danych flotowych klienta, historii przeglądów i kalkulacji zakresu prac

Ścieżka Techniczna / Ścieżka Biznesowa / PM

## JAK TO WYGLĄDA DZIŚ

* Ręczne przeszukiwanie portali, LinkedIn, FlightRadar
* Decyzja "do kogo dzwonić" - z intuicji i doświadczenia
* Historia serwisów samolotu = tajemnica handlowa. Danych nie ma.

## PRZYKŁADOWE ROZWIĄZANIA

* Dashboard per samolot - historia lotów ADS-B, wykryte okresy bez aktywności, klasyfikacja typu check
* Tabela priorytetowa - lista 737 w Europie posortowana według zbliżającego się okna decyzyjnego C-check
* Wykres osi czasu - wizualizacja kiedy każdy samolot latał, kiedy miał przerwy i jak długo - by odróżnić A od C-check
* Alert handlowy - samoloty wchodzące w okno decyzyjne w ciągu 6–12 miesięcy, z sugerowaną datą pierwszego kontaktu

## JAK ODRÓŻNIĆ TYP PRZEGLĄDU NA PODSTAWIE PRZERWY W DANYCH ADS-B

| Typ | Częstotliwość | Przerwa w ADS-B | Sygnał w danych | Wartość dla LOTAMS |
| :--- | :--- | :--- | :--- | :--- |
| A-check | co 500–600 h<br>kilka tygodni | 1–3 dni | Krótka przerwa, samolot wraca na tę samą bazę, brak zmiany lokalizacji | Brak - LOTAMS nie wykonuje A-check |
| B-check | co 4–8 mies.<br>coraz rzadszy | 4–5 dni | Przerwa kilkudniowa; wiele linii eliminuje B-check i łączy z C | Rzadki - większość linii go pomija |
| C-check ★ | co 2–3 lata<br>~4 000–5 000 h | 3–6 tygodni | Długa przerwa bez żadnych lotów; samolot pojawia się w lokalizacji MRO (Warszawa, Hamburg, Stambuł) | Główny produkt LOTAMS - to tu jest kontrakt |
| D-check | co ~12 lat<br>25 000+ h | 1–3 miesiące | Bardzo długa przerwa; samolot może nie wrócić do poprzedniego operatora (lease return lub złomowanie) | Rzadki - jeden raz w życiu samolotu |

## PRZYKŁADOWY OUTPUT DASHBOARDU - BOEING 737 W EUROPIE

Dane poglądowe

| Rejestracja | Operator | Wiek | Ostatnie okno | Czas trwania | Typ check | Prognoza C-check | Priorytet |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| EI-FRK | Ryanair | 8 lat | Mar 2024 | 29 dni | C-check | Q1 2027 | TERAZ |
| SP-LVB | LOT Polish | 6 lat | Nov 2023 | 34 dni | C-check | Q2 2026 | 6 mies. |
| OE-LNT | TUI Fly | 5 lat | Jan 2024 | 2 dni | A-check | Q4 2026 | 12 mies. |
| G-JZHF | Jet2 | 11 lat | Sep 2022 | 26 dni | C-check | Q3 2025 | TERAZ |
| OO-JAX | TUI Fly BE | 9 lat | Lut 2024 | 4 dni | B-check | Q1 2026 | 6 mies. |
| TC-JFF | SunExpress | 14 lat | Dec 2021 | 89 dni | D-check | 2030+ | Daleko |

Dane poglądowe - rejestracje i daty przykładowe. Rzeczywiste dane do pobrania z OpenSky Network i Airfleets.net.

## O CZYM PAMIĘTAĆ

* Dane ADS-B to pośredni sygnał - wnioskujesz z przerw w aktywności lotniczej, nie z dokumentacji serwisowej samolotu
* Okno decyzyjne to 6–18 miesięcy przed przeglądem - sygnał musi być wczesny, nie reaktywny
* Skup się na C-check - A-check robi linia samodzielnie bez MRO. C-check to produkt LOTAMS, tu są pieniądze
* Zakres: tylko Boeing 737, tylko Europa - 2 000+ samolotów to wystarczający dataset na 24 godziny hackathonu

## KLUCZOWE DANE (DARMOWE)

* OpenSky Network (ADS-B · historyczne archiwum · REST API)
* ADS-B Exchange (Niefiltrowane · bez ukrywania)
* Airfleets.net (Floty linii · wiek samolotów · dostawy)
* EASA Type Certificates (Oficjalne interwały serwisowe 737)
* Simple Flying (Newsy · dostawy · zmiany operatorów)

Python / pandas / Streamlit / Plotly / OpenSky API / Predykcja ML
