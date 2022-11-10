# Scrapper de supermercados

> Proyecto de GPTI

Web scrapper de supermercados para obtener información de productos y precios.

## Requerimientos

- Python >= 3.8 (idealmente 3.10)
- Poetry

## Instalación

```bash
poetry install
```

## Ejecución

```bash
poetry run scrapy crawl jumbo -L INFO -O jumbo.json
poetry run scrapy crawl lider -L INFO -O lider.json
```
