# README – Estymacja RD i parametrów λ dla JPEG

Ten zestaw skryptów służy do analizy jakości kompresji JPEG i estymacji parametrów λ, które pozwalają przewidywać optymalną kwantyzację. Skrypty umożliwiają:

* zbieranie danych RD (Rate-Distortion) z kodera,
* dopasowywanie modeli matematycznych do zależności D(R),
* obliczanie pochodnych i parametrów λ,
* agregowanie i dopasowywanie λ w funkcji Q,
* weryfikację dopasowań i generowanie wykresów.

---

## est_derivative.py

**Cel**
Analiza RD (Rate-Distortion) dla sekwencji wideo, dopasowując modele potęgowe do danych Luma i Chroma, oraz obliczenie pochodnych λ(R). Obsługuje wszystkie tabele kwantyzacji: default, flat i semiflat.

**Wejście**

* SQLite DB: `jpegRD.db` – tabela dla każdej sekwencji z kolumnami `q_level`, `quant_main_bits_y`, `quant_main_dist_y`, `quant_main_bits_cb`, `quant_main_dist_cb`, `quant_main_bits_cr`, `quant_main_dist_cr`
* Lista sekwencji zdefiniowana w skrypcie
* Zakres jakości Q: `Q_MIN`–`Q_MAX`
* Układy kwantyzacji: domyślny, flat, semiflat

**Wyjście**

* Wykresy RD (D vs R) dla Luma i Chroma: `plots/RD/Luma/` i `plots/RD/Chroma/`
* Wykresy λ(R) dla Luma i Chroma: `plots/Lambda/Luma/` i `plots/Lambda/Chroma/`
* CSV z parametrami dopasowania, współczynnikiem Pearsona i nazwą tabeli kwantyzacji: `fit_params.csv`
* Podsumowanie średnich wartości |r| dla każdej sekwencji i globalnie w konsoli

**Działanie**

1. Pobranie danych z bazy.
2. Dopasowanie modeli potęgowych: pojedyncza potęga dla Luma, podwójna dla Chroma.
3. Obliczenie pochodnej λ(R) na podstawie dopasowanych parametrów.
4. Generowanie wykresów RD i λ(R).
5. Obliczenie i podsumowanie współczynnika Pearsona.
6. Zapis parametrów do CSV dla wszystkich tabel kwantyzacji (default, flat, semiflat).

---

## derive_params_from_lambda.py

**Cel**
Agreguje parametry λ z poszczególnych sekwencji i tabel kwantyzacji oraz dopasowuje funkcję λ(Q) dla każdego kanału i układu kwantyzacji.

**Wejście**

* CSV z parametrami dopasowania: `fit_params.csv`
* SQLite DB: `jpegRD.db`

**Wyjście**

* Wykresy λ(Q) dla poszczególnych tabel QTL: `lambda_aggregate_by_qtl/`
* CSV z agregowanymi λ dla wszystkich QTL: `lambda_aggregate/*_agg.csv`
* Parametry dopasowania α, β dla modelu `λ(Q) = α*(101-Q)^β` w konsoli

**Działanie**

1. Wczytuje parametry λ z CSV i dane RD z bazy.
2. Agreguje λ dla wszystkich sekwencji i QTL (default, flat, semiflat).
3. Dopasowuje funkcję `λ(Q) = α*(101-Q)^β`.
4. Generuje wykresy λ(Q) i zapisuje CSV dla wszystkich tabel.

---

## test_lambda_Q.py

**Cel**
Testuje dopasowania λ(Q) z agregacji, wygładza dane i dopasowuje funkcje log-logowe dla Luma i Chroma. Tworzy wykresy porównujące dopasowanie z rzeczywistymi wartościami.

**Wejście**

* Pliki CSV z agregowanymi λ: `lambda_aggregate/*_agg.csv`

**Wyjście**

* Wykresy dopasowania λ(Q): `lambda_fit_plots/`
* CSV z wynikami dopasowania: `lambda_fit_results_by_qtl.csv`

**Działanie**

1. Wczytuje wszystkie pliki `_agg.csv` dla kanałów i tabel QTL.
2. Filtruje Q ≥ 15 i wygładza wartości λ.
3. Dopasowuje modele log-log: kwadratowy dla Luma, sześcian dla Chroma.
4. Oblicza R² dopasowania.
5. Generuje wykresy porównawcze i zapisuje wyniki do CSV.

---

## lambda_real_check.py

**Cel**
Weryfikuje dopasowania λ(Q) względem rzeczywistych wartości λ w bazie danych. Oblicza błędy względne i tworzy wykresy porównawcze.

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

## lambda_Q_plot.py

**Cel**
Tworzy ostateczny wykres λ(Q) dla Luma i Chroma (Q ≥ 15) na dwóch panelach, pokazując trend dla różnych tabel kwantyzacji.

**Wejście**

* Parametry dopasowania λ(Q): `lambda_fit_results_by_qtl.csv`

**Wyjście**

* Wykres PNG: `lambda_Q_plot_two_panels.png`

**Działanie**

1. Definiuje zakres Q od 15 do 100.
2. Wczytuje parametry dopasowania modeli log-log z CSV.
3. Oblicza λ(Q) dla Luma i Chroma dla każdego QTL.
4. Wygładza krzywe filtrem Savitzky-Golay.
5. Rysuje wykresy dwóch paneli z legendą i kolorami dla QTL.

---

## miara_bjontegaarda.py

**Cel**
Oblicza różnice jakości i bitrate między trybem bazowym (`LambdaMode=0`) a nowym trybem λ (`LambdaMode=1`) dla różnych tabel kwantyzacji i grup wartości Q.

**Wejście**

* Baza SQLite: `lambda_compare.db`
  Każda tabela sekwencji zawiera kolumny:
  `Q, LambdaMode, QuantTabLayout, Bitrate_kib, PSNR_Y, PSNR_Cb, PSNR_Cr, EncodeTime_ms, DecodeTime_ms, TotalTime_ms`
* Zdefiniowane grupy Q w skrypcie:

  * **Q_L**: 20–35
  * **Q_M**: 50–65
  * **Q_H**: 80–95
* Układy kwantyzacji: Default, Flat, SemiFlat

**Wyjście**

* Tabele porównawcze w konsoli i CSV: `wykresy_bj/<group>_<qtl>.csv`
* Dodatkowy wiersz ze średnimi wartościami Δ dla całej grupy

**Działanie**

1. Łączy się z bazą i pobiera dane dla każdej sekwencji, layoutu i trybu λ.
2. Filtruje punkty odpowiadające zadanym grupom Q.
3. Oblicza metryki Bjøntegaarda: ΔPSNR, ΔBitrate i zmiany czasów kodowania/odkodowania.
4. Zapisuje wyniki do CSV i wyświetla w konsoli.

---

## Uwagi ogólne

* Wymagane biblioteki: `numpy`, `pandas`, `matplotlib`, `scipy`, `tqdm`
* Wszystkie wykresy i CSV są zapisywane w podfolderach skryptu
* Kolejność uruchamiania skryptów:

  1. est_derivative.py
  2. derive_params_from_lambda.py
  3. test_lambda_Q.py
  4. lambda_real_check.py
  5. lambda_Q_plot.py
  6. miara_bjontegaarda.py
