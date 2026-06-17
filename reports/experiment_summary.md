# Экспериментальная часть

## Цель эксперимента

Проверить работоспособность разработанного MVP ETL-конвейера на учебных материалах разных форматов и оценить возможность автоматического извлечения текста, обогащения метаданных, валидации и сохранения структурированного JSON-датасета.

## Тестовый набор данных

Текущий тестовый набор является пилотным и размещён в `data/real_input/`. Он используется для первичной проверки MVP на всех поддерживаемых форматах: PDF, DOCX и HTML.

Фактический состав текущего набора:

| Категория | Количество | Комментарий |
|---|---:|---|
| PDF | 18 | 16 уникальных корректных PDF, 1 плохой PDF и 1 PDF-дубликат |
| DOCX | 26 | реальные DOCX и 6 синтетических учебных DOCX |
| HTML | 22 | 21 уникальная HTML-страница и 1 HTML-дубликат |
| Проблемные файлы | 1 | входят в PDF: файл с расширением `.pdf`, который не является PDF |
| Дубликаты | 2 | входят в PDF/HTML: копия HTML-файла и повтор PDF-файла |

В терминах pipeline найдено 66 поддерживаемых файлов: 18 PDF с учётом плохого PDF и PDF-дубликата, 26 DOCX и 22 HTML с учётом HTML-дубликата.

Целевой пилотный объём около 60 документов на текущем этапе достигнут и немного превышен. Расширение набора до 100+ документов запланировано на следующем этапе исследования для получения более устойчивых статистических оценок.

Для проверки корректности DOCX-адаптера часть документов была сформирована как синтетические учебные примеры, содержащие типовые элементы учебных материалов: заголовки, параграфы, таблицы, автора и ключевые термины.

## Методика тестирования

1. Подготовить структуру `data/real_input/pdf`, `data/real_input/docx`, `data/real_input/html`, `data/real_input/bad_files`, `data/real_input/duplicates`.
2. При необходимости собрать HTML-страницы NEERC wiki:

```bash
python scripts/collect_neerc_html.py --limit 20 --output data/real_input/html --manifest datasets/manifest.csv
```

3. При необходимости создать синтетические DOCX:

```bash
python scripts/create_synthetic_docx_samples.py --output data/real_input/docx --manifest datasets/manifest.csv
```

4. Запустить pipeline:

```bash
python -m src.main \
  --input data/real_input \
  --output data/output/dataset_real.json \
  --metrics-output data/output/metrics_real.json \
  --log-output data/output/processing_log_real.csv \
  --errors-output data/output/errors_real.json \
  --pretty
```

5. Сгенерировать графики:

```bash
python -m src.generate_report_assets \
  --metrics data/output/metrics_real.json \
  --log data/output/processing_log_real.csv \
  --output reports/assets
```

6. Проверить `dataset_real.json`, `metrics_real.json`, `processing_log_real.csv`, `errors_real.json`.
7. Проверить устойчивость обработки на плохом PDF и дубликате.
8. Запустить тесты:

```bash
pytest tests/
```

## Метрики оценки

В эксперименте используются следующие группы метрик:

- скорость обработки: `processing_time_sec`, `average_processing_time_sec`, `files_per_second`;
- устойчивость: `processed_files`, `failed_files`, `success_rate`, `error_count_by_format`;
- дубликаты: `skipped_duplicates`, `duplicate_of`, `ingest_status`;
- качество заполнения метаданных: `metadata_completeness_common`, `metadata_completeness_format_specific`, `metadata_completeness_total`;
- форматная аналитика: `success_rate_by_format`, `average_processing_time_by_format`, `file_format_distribution`.

Полнота метаданных считается с учётом применимости полей:

- `metadata_completeness_common` — универсальные поля `title`, `author`, `language`, `topic`, `difficulty`, `keywords`, `word_count`, `char_count`;
- `metadata_completeness_format_specific` — поля, зависящие от формата: `page_count` для PDF, `headings` для HTML/DOCX, `embedded_metadata`;
- `metadata_completeness_total` — среднее значение common и format-specific.

## Результаты

Фактические результаты последнего запуска:

| Метрика | Значение |
|---|---:|
| total_files | 66 |
| processed_files | 63 |
| failed_files | 1 |
| skipped_duplicates | 2 |
| success_rate | 0.9844 |
| average_processing_time_sec | 0.309635 |
| total_processing_time_sec | 19.882103 |
| files_per_second | 3.218975 |
| average_words_per_document | 816.396825 |
| metadata_completeness_common | 0.888672 |
| metadata_completeness_format_specific | 0.921875 |
| metadata_completeness_total | 0.905273 |

Результаты по форматам:

| Формат | Количество файлов | Success rate | Среднее время обработки, сек | Количество ошибок |
|---|---:|---:|---:|---:|
| DOCX | 26 | 1.0 | 0.122099 | 0 |
| HTML | 22 | 1.0 | 0.054436 | 0 |
| PDF | 18 | 0.9412 | 0.911700 | 1 |

PDF-группа включает один специально добавленный плохой файл. Поэтому значение `success_rate_by_format.pdf = 0.9412` отражает успешную обработку большинства PDF и отдельную проверку устойчивости, а не отказ обработки корректных PDF.

## Анализ результатов

Пилотный запуск подтвердил, что MVP выполняет полный путь `Input -> Ingest -> Extract -> Transform -> Validate -> Load -> Output` для документов разных форматов. Успешно созданы `dataset_real.json`, `metrics_real.json`, `processing_log_real.csv`, `errors_real.json` и PNG-графики.

Для PDF используется `pdfplumber`, а при пустом результате или ошибке выполняется fallback на `PyPDF2`. В расширенном наборе успешно обработаны 17 PDF-файлов с текстовым слоем; `page_count` определён для большинства корректных PDF, embedded metadata заполнены частично. Плохой PDF не остановил pipeline: ошибка сохранена в `errors_real.json`, а остальные документы обработаны.

Для DOCX используется `python-docx`. Расширенный DOCX-поднабор подтвердил извлечение параграфов, таблиц, заголовков и core properties. Ограничение состоит в том, что часть документов синтетическая; это честно фиксируется как часть пилотной проверки.

Для HTML используется BeautifulSoup. Проверена обработка сохранённой страницы и страниц NEERC wiki; извлекаются title, h1/h2/h3 и meta-теги, технические `script/style/nav/footer` удаляются.

Дубликаты проверяются по SHA256. В последнем запуске `Лекция №7 new new.pdf` и `boolean_function_duplicate.html` получили статус `skipped_duplicate`, а в `processing_log_real.csv` поле `duplicate_of` указывает на исходный документ.

Наиболее слабое универсальное поле — `author`: многие реальные учебные материалы не содержат автора в embedded metadata или тексте. Это снижает `metadata_completeness_common`, но является свойством исходных данных, а не ошибкой сохранения результата.

## Связь с критериями аналитического обзора

- Скорость обработки подтверждена метриками времени и `files_per_second`.
- Устойчивость подтверждена обработкой плохого PDF без падения всего pipeline.
- Качество извлечения метаданных оценивается через common и format-specific completeness.
- Масштабируемость пока подтверждается модульной архитектурой, manifest и структурой dataset; промышленное масштабирование на Airflow/Spark остаётся дальнейшим развитием.
- Затраты на внедрение снижены за счёт локального запуска и open-source библиотек.

## Выводы

Проведённая пилотная проверка подтверждает работоспособность разработанного MVP на расширенном наборе документов разных форматов и демонстрирует возможность автоматического формирования структурированного JSON-датасета. При этом для получения статистически устойчивой оценки качества извлечения метаданных требуется дальнейшее расширение тестового набора и проведение масштабного эксперимента на 100+ документах.

Корректная формулировка результата для отчёта: в рамках текущего этапа НИР выполнена пилотная экспериментальная проверка локального ETL-конвейера на расширенном наборе из 66 поддерживаемых PDF/DOCX/HTML-файлов. Конвейер подтвердил работоспособность основных этапов, включая обработку ошибок и дубликатов. Масштабирование эксперимента до 100+ документов запланировано на следующем этапе исследования.
