# MortalityENW

Preprocessing for a data viz exercise with mortality data from England and Wales

## Data sources

* [Deaths registered in England and Wales – 21st century mortality](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets/the21stcenturymortalityfilesdeathsdataset)
* [The 20th Century Mortality Files, 1901 to 2000](https://webarchive.nationalarchives.gov.uk/20160111174808/http://www.ons.gov.uk/ons/publications/re-reference-tables.html?edition=tcm%3A77-215593)

Data files are expected (unzip'd) in `../rawdata`, relative to this file.

## Process

All code is in `process.py`.

* Load data tables for every 5th data year, 1915 to 2000
* Map ICD codes to categories (communicable, injuries, ...) according to the [Appendix](https://link.springer.com/content/pdf/bbm%3A978-3-319-14403-0%2F1.pdf) of ["The Transitions of Aging" by Suchit Arora](http://dx.doi.org/10.1007/978-3-319-14403-0), with the ICD-10 mapping defined by myself. Translation tables are hardcoded in `process.py`. NOTE: they are slightly simplified in the code, e.g. disregarding excluded ICD sub-codes from groups. Also, the table in the book has some sever typos in the group codes, overlaps between groups... !
* Keep top N ICD codes per data year, aggregate others to 'Other communicable diseases', 'Other injuries', ...
* Attach ICD descriptions to retained codes
* Dump everything into a CSV file in `../outdata/`, relative to this file
