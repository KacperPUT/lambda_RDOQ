# README – Estymacja RD i parametrów λ dla JPEG

Ten zestaw skryptów służy do analizy jakości kompresji JPEG i estymacji parametrów λ. Parametry te pozwalają przewidywać optymalne wartości kwantyzacji. Cały proces obejmuje zebranie danych z kodera, dopasowanie modeli matematycznych, analizę dokładności oraz obliczenie metryk porównawczych.

---

## 00_init_database.py

**Cel**
Tworzy pustą bazę danych `jpegRD.db`, w której każda sekwencja wideo dostaje osobną tabelę.

**Działanie**

* Definiuje strukturę tabel (bity i zniekształcenia dla kanałów Y, Cb, Cr).
* Przygotowuje bazę pod dalsze zbieranie danych RD.

---

## 00b_init_lambda_compare_db.py

**Cel**
Tworzy drugą bazę danych `lambda_compare.db`, przeznaczoną do testów porównawczych.

**Działanie**

* Definiuje tabelę dla każdej sekwencji.
* Dodaje kolumny: `Q`, `LambdaMode`, `QuantTabLayout`, bitrate, PSNR-y, czasy enkodowania i dekodowania.
* Dzięki temu można bezpośrednio porównać tryb klasyczny i tryb sterowany parametrem λ.

---

## 01_collect_rd_data.py

**Cel**
Zbiera dane RD (Rate–Distortion) z kodera JPEG i zapisuje je do `jpegRD.db`.

**Działanie**

* Uruchamia koder JPEG na zadanych sekwencjach i wartościach Q.
* Zapisuje: liczbę bitów, wartości błędów (MSE/distortion), Q, itp.
* Obsługuje różne warianty tabel kwantyzacji: default, flat, semiflat.

---

## 02_collect_lambda_compare.py

**Cel**
Zbiera dane porównawcze (LambdaMode=0 vs LambdaMode=1) i zapisuje do `lambda_compare.db`.

**Działanie**

* Uruchamia koder w dwóch trybach.
* Zapisuje bitrate, PSNR-y oraz czasy enkodowania i dekodowania.
* Dane te służą później do obliczeń metryki Bjøntegaarda.

---

## 10_fit_rd_lambda.py

**Cel**
Analizuje dane RD i dopasowuje modele matematyczne do zależności D(R). Następnie oblicza pochodne, czyli λ(R).

**Działanie**

* Pobiera dane z `jpegRD.db`.
* Dla Luma (Y) dopasowuje funkcję potęgową `D(R) = c·R^b`.
* Dla Chroma (Cb+Cr) dopasowuje sumę dwóch potęg.
* Oblicza pochodne λ(R).
* Generuje wykresy RD i λ(R).
* Zapisuje parametry dopasowania do `fit_params.csv` razem z korelacją Pearsona.

---

## 11_aggregate_lambda.py

**Cel**
Agreguje wartości λ(R) pochodzące z różnych sekwencji i uśrednia je w funkcji Q.

**Działanie**

* Wczytuje parametry z `fit_params.csv`.
* Dla każdej sekwencji i Q oblicza λ.
* Grupuje wyniki i oblicza medianę i odchylenie standardowe.
* Zapisuje pliki CSV `lambda_aggregate/*_agg.csv`.
* Tworzy wykresy λ(Q) w folderze `lambda_aggregate_by_qtl/`.

---

## 12_fit_lambda_q.py

**Cel**
Dopasowuje globalne modele λ(Q) na podstawie agregowanych danych.

**Działanie**

* Wczytuje dane z `lambda_aggregate/*_agg.csv`.
* Filtruje Q ≥ 15 i wygładza dane filtrem Savitzky-Golay.
* Dopasowuje:

  * log-log kwadratowy dla Luma,
  * log-log sześcienny dla Chroma.
* Oblicza współczynnik dopasowania R².
* Zapisuje parametry modeli do `lambda_fit_results_by_qtl.csv`.
* Generuje wykresy w `lambda_fit_plots/`.

---

## 13_validate_lambda.py

**Cel**
Sprawdza, jak dobrze dopasowane modele λ(Q) odwzorowują rzeczywiste wartości λ zapisane w bazie.

**Działanie**

* Pobiera dane z `jpegRD.db`.
* Wczytuje dopasowane parametry z `lambda_fit_results_by_qtl.csv`.
* Porównuje λ_real z λ_pred dla każdej sekwencji i Q.
* Oblicza średni i maksymalny błąd względny.
* Tworzy wykresy porównawcze (`lambda_validation_plots/`).
* Zapisuje szczegółowe wyniki (`lambda_validation_summary.csv`) i średnie błędy (`lambda_validation_summary_mean.csv`).

---

## 14_plot_lambda_q.py

**Cel**
Tworzy końcowy wykres λ(Q) dla kanałów Luma i Chroma, pokazując różne układy tabel kwantyzacji.

**Działanie**

* Wczytuje parametry modeli z `lambda_fit_results_by_qtl.csv`.
* Oblicza λ(Q) dla Q od 20 do 100.
* Rysuje dwa panele: osobno dla Luma i Chroma.
* Kolory i style linii odpowiadają QTL (default, flat, semiflat).
* Zapisuje wynik do `lambda_Q_plot_two_panels.png`.

---

## 15_bjontegaard_metric.py

**Cel**
Porównuje tryb klasyczny (`LambdaMode=0`) i tryb sterowany λ (`LambdaMode=1`) za pomocą metryk Bjøntegaarda.

**Działanie**

* Pobiera dane z `lambda_compare.db`.
* Grupuje wyniki według Q:

  * Q_L (20–35),
  * Q_M (50–65),
  * Q_H (80–95).
* Oblicza:

  * ΔBitrate-Y, ΔBitrate-YCbCr [%],
  * ΔPSNR-Y, ΔPSNR-YCbCr [dB],
  * średnie zmiany czasów enkodowania i dekodowania [%].
* Wyniki zapisuje w `wykresy_bj/<group>_<qtl>.csv`.
* Dodatkowo wypisuje podsumowania w konsoli.

---

## Uwagi ogólne

* Wymagane biblioteki: `numpy`, `pandas`, `matplotlib`, `scipy`, `tqdm`.
* Wszystkie wyniki (CSV i wykresy) zapisywane są w automatycznie tworzonych podfolderach.
* Rekomendowana kolejność uruchamiania:

  1. 00_init_database.py
  2. 00b_init_lambda_compare_db.py
  3. 01_collect_rd_data.py
  4. 02_collect_lambda_compare.py
  5. 10_fit_rd_lambda.py
  6. 11_aggregate_lambda.py
  7. 12_fit_lambda_q.py
  8. 13_validate_lambda.py
  9. 14_plot_lambda_q.py
  10. 15_bjontegaard_metric.py
