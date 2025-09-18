# README – Estymacja RD i parametrów λ dla JPEG

Ten zestaw skryptów służy do analizy jakości kompresji JPEG i estymacji parametrów λ, które pozwalają przewidywać optymalną kwantyzację. Skrypty pozwalają:

* zbierać dane RD (Rate-Distortion) z kodera,
* dopasowywać modele matematyczne do zależności D(R),
* obliczać pochodne i parametry λ,
* agregować i dopasowywać λ w funkcji Q,
* weryfikować dopasowania i generować wykresy.

---

## est\_derivative.py

**Cel**
Skrypt wykonuje analizę RD (Rate-Distortion) dla sekwencji wideo, dopasowując modele potęgowe do danych Luma i Chroma, a następnie oblicza odpowiadające pochodne λ(R). Łączy funkcjonalność estymacji liniowej i obliczania pochodnej w jednym przepływie pracy.

**Wejście**

* SQLite DB: `jpegRD.db` – tabela dla każdej sekwencji z kolumnami `q_level`, `quant_main_bits_y`, `quant_main_dist_y`, `quant_main_bits_cb`, `quant_main_dist_cb`, `quant_main_bits_cr`, `quant_main_dist_cr`.
* Lista sekwencji zdefiniowana w skrypcie.
* Zakres jakości Q: `Q_MIN`–`Q_MAX`.
* Układy kwantyzacji: domyślny, flat, semiflat.

**Wyjście**

* Wykresy RD (D vs R) dla Luma i Chroma: `plots/RD/Luma/` i `plots/RD/Chroma/`
* Wykresy λ(R) dla Luma i Chroma: `plots/Lambda/Luma/` i `plots/Lambda/Chroma/`
* CSV z parametrami dopasowania i współczynnikiem korelacji Pearsona: `fit_params.csv`
* Podsumowanie średnich wartości |r| dla każdej sekwencji i globalnie w konsoli.

**Działanie**

1. **Pobieranie danych z bazy:**
   Skrypt łączy się z `jpegRD.db` i pobiera sumaryczne liczby bitów i odkształcenia dla wszystkich Q dla każdej sekwencji i układu kwantyzacji.

2. **Dopasowanie modeli potęgowych:**

   * Luma: model pojedynczej potęgi $D = a R^b$
   * Chroma (Cb+Cr): model podwójnej potęgi $D = c_1 R^{b_1} + c_2 R^{b_2}$
     Normalizacja danych zapewnia stabilność dopasowania, a funkcje `norm_to_raw_single` i `norm_to_raw_double` przeliczają parametry znormalizowane na oryginalną skalę.

3. **Obliczanie pochodnej λ(R):**
   Na podstawie dopasowanych parametrów obliczana jest pochodna λ(R), czyli szybkość zmiany D względem R.
   Funkcje: `lambda_from_single` i `lambda_from_double`.

4. **Generowanie wykresów:**

   * RD: rozrzut danych i linia dopasowania D(R)
   * λ(R): wykres pochodnej λ w funkcji R
     Wykresy zapisywane są w katalogach `plots/RD/` i `plots/Lambda/`.

5. **Podsumowanie Pearsona:**
   Skrypt oblicza współczynnik korelacji Pearsona między D obserwowanym a dopasowanym dla każdej sekwencji i kanału oraz wyświetla średnie wartości globalne.

**Cel dopasowania funkcji i obliczania λ(R)**
Umożliwia spójną estymację zależności D(R) i pochodnej λ(R) dla wszystkich sekwencji i układów kwantyzacji, co ułatwia dalszą analizę, agregację parametrów i generowanie wykresów porównawczych.


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
