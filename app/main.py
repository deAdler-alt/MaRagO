from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="MRO Prediction Platform | LOTAMS",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("MRO Prediction Platform")
st.caption("Boeing 737 · Europa · wczesne wykrywanie okien C-check dla LOTAMS")

st.markdown(
    """
    **Problem:** Gdy samolot znika z trasy na 3–6 tygodni, kontrakt C-check jest już u konkurencji
    (Lufthansa Technik, AFI KLM E&M, Turkish Technic). Ten dashboard daje sygnał **6–18 miesięcy wcześniej**.

    **Uwaga:** Klasyfikacja opiera się na przerwach w danych lotniczych (OPDI/EUROCONTROL) —
    to sygnał pośredni, nie potwierdzenie dokumentacji MRO.
    """
)

st.info("Użyj menu bocznego: **Fleet Priority**, **Aircraft Detail**, **Commercial Alerts**.")

col1, col2, col3 = st.columns(3)
col1.metric("Zakres", "Boeing 737", "Europa")
col2.metric("Produkt LOTAMS", "C-check", "priorytet sprzedaży")
col3.metric("Okno decyzyjne", "6–18 mies.", "przed przeglądem")

st.markdown("---")
st.subheader("Why now?")
st.write(
    "LOTAMS wygrywa ceną, dostępnością slotu i bliskością dla linii CEE — "
    "ale tylko jeśli handlowiec wie **kiedy** zadzwonić. Każdy tydzień przewagi informacyjnej "
    "to potencjalnie podpisany kontrakt w hangarze w Warszawie."
)
