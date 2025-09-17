# README – Estymacja RD i parametrów λ dla JPEG

Ten zestaw skryptów służy do analizy jakości kompresji JPEG i estymacji parametrów λ, które pozwalają przewidywać optymalną kwantyzację. Skrypty pozwalają:

* zbierać dane RD (Rate-Distortion) z kodera,
* dopasowywać modele matematyczne do zależności D(R),
* obliczać pochodne i parametry λ,
* agregować i dopasowywać λ w funkcji Q,
* weryfikować dopasowania i generować wykresy.

---

## 1. estymacja\_liniowa.py

**Cel**
Dopasowuje modele jednoskładnikowe (Luma) i dwuskładnikowe (Chroma) do danych RD z bazy `jpegRD.db` i oblicza współczynnik korelacji Pearsona |r|.

**Wejście**

* SQLite DB: `jpegRD.db`
* Tabele z kolumnami `q_level`, `quant_main_bits_*`, `quant_main_dist_*`

**Wyjście**

* Wykresy dopasowania RD dla Luma i Chroma (`plots_final/Luma` i `plots_final/Chroma`)
* Średnie wartości |r| dla każdego layoutu kwantyzacji w konsoli

**Działanie**

1. Pobiera dane z bazy dla sekwencji i layoutów tabel kwantyzacji (`default`, `flat`, `semiflat`).
2. Filtruje zakres Q od 4 do 100.
3. Dopasowuje model `D = a*R^b` dla Luma i `D = a1*R^b1 + a2*R^b2` dla Chroma.
4. Oblicza współczynnik Pearsona |r| między rzeczywistymi i przewidzianymi wartościami.
5. Generuje wykresy dla każdej sekwencji i layoutu.

**Funkcje użyte w pliku**

* Dopasowanie modelu RD metodą najmniejszych kwadratów
* Obliczenie współczynnika korelacji Pearsona

---

## 2. pochodna\_liniowa.py

**Cel**
Na podstawie dopasowanych modeli RD oblicza λ(R) jako pochodną funkcji D(R) i zapisuje wyniki do CSV. Tworzy również wykresy RD i λ.

**Wejście**

* SQLite DB: `jpegRD.db`
* Wymaga danych z estymacja\_liniowa.py

**Wyjście**

* CSV z parametrami dopasowania: `fit_params.csv`
* Wykresy RD: `plots/RD/Luma` i `plots/RD/Chroma`
* Wykresy λ(R): `plots/Lambda/Luma` i `plots/Lambda/Chroma`

**Działanie**

1. Wczytuje dane RD z bazy i filtruje je według Q.
2. Dopasowuje modele (jednoskładnikowy dla Luma, dwuskładnikowy dla Chroma).
3. Oblicza λ(R) jako pochodną D(R).
4. Generuje wykresy D(R) i λ(R) dla każdej sekwencji i layoutu.
5. Zapisuje parametry dopasowania i korelacje Pearsona w CSV.

**Funkcje użyte w pliku**

* Obliczanie pochodnej funkcji D(R)
* Tworzenie wykresów RD i λ

---

## 3. derive\_params\_from\_lambda.py

**Cel**
Agreguje parametry λ obliczone z poszczególnych sekwencji i tabel kwantyzacji, dopasowuje funkcję λ(Q) dla każdego kanału i layoutu.

**Wejście**

* CSV z dopasowanymi parametrami `fit_params.csv`
* SQLite DB: `jpegRD.db`

**Wyjście**

* Wykresy λ(Q) dla poszczególnych tabel QTL: `lambda_aggregate_by_qtl/`
* Parametry dopasowania α, β dla modelu `λ(Q) = α*(101-Q)^β` w konsoli

**Działanie**

1. Wczytuje parametry λ z CSV i dane RD z bazy.
2. Agreguje λ dla wszystkich sekwencji i QTL.
3. Dopasowuje funkcję `λ(Q) = α*(101-Q)^β` dla spójnej reprezentacji λ w zależności od Q.
4. Generuje wykresy λ(Q) i zapisuje parametry dopasowania.

**Cel dopasowania funkcji**
Umożliwia spójną reprezentację λ w zależności od Q dla wszystkich sekwencji i tabel, co ułatwia analizę, porównanie wyników i generowanie wykresów trendów.

---

## 4. test\_lambda\_Q.py

**Cel**
Testuje dopasowania λ(Q) z agregacji, wygładza dane i dopasowuje funkcje log-logowe dla Luma i Chroma. Tworzy wykresy porównujące dopasowanie z rzeczywistymi wartościami.

**Wejście**
Pliki CSV z agregowanymi λ: `lambda_aggregate/*_agg.csv`

**Wyjście**

* Wykresy dopasowania λ(Q): `lambda_fit_plots/`
* CSV z wynikami dopasowania: `lambda_fit_results_by_qtl.csv`

**Działanie**

1. Wczytuje pliki `_agg.csv` dla wszystkich kanałów i tabel.
2. Filtruje Q ≥ 15 i wygładza wartości λ.
3. Dopasowuje modele log-log: kwadratowy dla Luma, sześcian dla Chroma.
4. Oblicza R² dla dopasowania.
5. Generuje wykresy porównujące średnie λ z dopasowaną funkcją.

---

## 5. lambda\_real\_check.py

**Cel**
Weryfikuje dopasowania λ(Q) względem rzeczywistych wartości λ zapisanych w bazie danych. Oblicza błędy względne i tworzy wykresy porównawcze.

**Wejście**

* SQLite DB: `jpegRD.db`
* Parametry dopasowania: `lambda_fit_results_by_qtl.csv`

**Wyjście**

* Wykresy porównawcze λ\_real vs λ\_pred: `lambda_validation_plots/`
* CSV szczegółowe: `lambda_validation_summary.csv`
* CSV ze średnimi błędami względnymi: `lambda_validation_summary_mean.csv`

**Działanie**

1. Iteruje przez wszystkie sekwencje i tabele QTL.
2. Pobiera rzeczywiste λ z bazy i przewidywane λ z dopasowanego modelu.
3. Oblicza średni i maksymalny błąd względny dla każdej sekwencji, kanału i QTL.
4. Generuje wykresy porównawcze i zapisuje podsumowanie błędów.

---

## 6. lambda\_Q\_plot.py

**Cel**
Tworzy ostateczny wykres λ(Q) dla Luma i Chroma (Q ≥ 15) na dwóch panelach, pokazując trend dla różnych tabel kwantyzacji (QTL).

**Wejście**
Parametry dopasowania λ(Q): `lambda_fit_results_by_qtl.csv`

**Wyjście**
Wykres PNG: `lambda_Q_plot_two_panels.png`

**Działanie**

1. Definiuje zakres Q od 15 do 100.
2. Wczytuje parametry dopasowania modeli log-log z CSV.
3. Oblicza λ(Q) dla Luma i Chroma dla każdego QTL.
4. Wygładza krzywe filtrem Savitzky-Golay.
5. Rysuje wykresy dwóch paneli z legendą i kolorami dla QTL.

---

## Uwagi ogólne

* Wymagane biblioteki: `numpy`, `pandas`, `matplotlib`, `scipy`, `tqdm`
* Wszystkie wykresy i CSV są zapisywane w podfolderach skryptu.
* Kolejność uruchamiania skryptów:

  1. estymacja\_liniowa.py
  2. pochodna\_liniowa.py
  3. derive\_params\_from\_lambda.py
  4. test\_lambda\_Q.py
  5. lambda\_real\_check.py
  6. lambda\_Q\_plot.py