# Тестовый набор данных для НИР MVP

Этот каталог описывает официальный пилотный набор документов для проверки локального ETL-конвейера `NIR_MVP`.

## Структура

```text
data/
  sample_input/           # минимальный демонстрационный запуск
  real_input/             # основной пилотный набор для НИР
    pdf/                  # PDF-файлы
    docx/                 # DOCX-файлы
    html/                 # HTML-файлы
    bad_files/            # проблемные файлы для проверки устойчивости
    duplicates/           # дубликаты для проверки skipped_duplicate
  output/                 # результаты запусков
datasets/
  manifest.csv            # реестр тестовых файлов
  README_DATASET.md       # описание набора
```

## Текущее состояние набора

Текущий локальный набор является пилотным. Он содержит реальные учебные материалы и синтетические DOCX-примеры для проверки отдельных возможностей адаптера:

| Тип | Количество | Комментарий |
|---|---:|---|
| PDF | 18 | 16 уникальных корректных PDF, 1 плохой PDF и 1 PDF-дубликат |
| DOCX | 26 | реальные DOCX и 6 синтетических учебных DOCX |
| HTML | 22 | 21 уникальная HTML-страница и 1 HTML-дубликат |
| Проблемные файлы | 1 | входят в PDF: файл с расширением `.pdf`, который не является PDF |
| Дубликаты | 2 | входят в PDF/HTML: байтовый дубликат HTML и повтор PDF-файла |

Итого в текущем `data/real_input/` находится 66 поддерживаемых файлов: 63 успешно обработанных документа, 1 проблемный PDF и 2 дубликата для проверки `skipped_duplicate`. Целевой пилотный объём около 60 документов на текущем этапе достигнут. Масштабирование эксперимента до 100 и более документов запланировано на следующем этапе исследования для получения более устойчивых статистических оценок.

## Темы

В наборе представлены или имитируются темы:

- программирование;
- базы данных;
- машинное обучение;
- операционные системы;
- компьютерные сети и информационная безопасность;
- математика и дискретная математика.

## Где хранить архив

Если PDF/DOCX/HTML-файлы нельзя хранить в репозитории, набор можно упаковать в `nir_test_dataset.zip` и хранить одним из способов:

- Google Drive;
- Яндекс Диск;
- OneDrive;
- локальная папка на компьютере;
- GitHub Releases, если файлы публичные и небольшие.

В репозитории при этом остаются `datasets/manifest.csv`, скрипты подготовки набора и инструкция восстановления структуры.

## Подготовка перед запуском

1. Разархивировать `nir_test_dataset.zip` в корень проекта так, чтобы появилась структура `data/real_input/pdf`, `data/real_input/docx`, `data/real_input/html`, `data/real_input/bad_files`, `data/real_input/duplicates`.
2. Проверить или обновить `datasets/manifest.csv`.
3. При необходимости создать синтетические DOCX:

```bash
python scripts/create_synthetic_docx_samples.py --output data/real_input/docx --manifest datasets/manifest.csv
```

4. При необходимости собрать HTML-страницы NEERC wiki:

```bash
python scripts/collect_neerc_html.py --limit 20 --output data/real_input/html --manifest datasets/manifest.csv
```

Если автоматический сбор HTML недоступен из-за сети или ограничений сайта, страницы можно сохранить вручную через браузер в `data/real_input/html/` и добавить строки в `datasets/manifest.csv`.

## Запуск pipeline

```bash
python -m src.main \
  --input data/real_input \
  --output data/output/dataset_real.json \
  --metrics-output data/output/metrics_real.json \
  --log-output data/output/processing_log_real.csv \
  --errors-output data/output/errors_real.json \
  --pretty
```

Графики:

```bash
python -m src.generate_report_assets \
  --metrics data/output/metrics_real.json \
  --log data/output/processing_log_real.csv \
  --output reports/assets
```

## Ограничения

- Текущий набор превышает 60 файлов, но всё ещё меньше 100 документов и используется как пилотный.
- Часть DOCX сформирована синтетически для гарантированной проверки заголовков, таблиц и core properties.
- OCR пока не реализован, поэтому PDF без текстового слоя могут попасть в `errors_real.json`.
- Темы и сложность определяются эвристически.
