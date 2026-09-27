"""Extraire les abonnements trimestriels publiés par Basic-Fit, sans interpolation."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

SOURCES = [
    (2021, 26, 'annual-2021.pdf', 'https://corporate.basic-fit.com/docs/Basic-Fit%20Annual%20Report%202021%20WEB?a=6UWq4tddgh8ofCiyWyeA8G'),
    (2022, 23, 'annual-2022.pdf', 'https://corporate.basic-fit.com/docs/Basic-Fit_Annual_Report_2022_Pdf.pdf?a=59eFPFFX7yWrajhSZAdWuA'),
    (2024, 22, 'annual-2024.pdf', 'https://corporate.basic-fit.com/docs/Basic-Fit%20Annual_Report_2024_Webversion.pdf?a=6YiUByKgbZ06bBQ3VnLkRj'),
    (2025, None, 'annual-2025-review.html', 'https://annualreport.basic-fit.com/2025/mbr/business-and-financial-review/'),
]
LABELS = ('First', 'Second', 'Third', 'Fourth')


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        if tag in ('td', 'th') and self.row is not None: self.cell = ''

    def handle_data(self, data):
        if self.cell is not None: self.cell += data

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(self.cell.strip()); self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row); self.row = None


def extraire_table(text, html=False):
    if html:
        parser = TableRows(); parser.feed(text)
        pairs = []
        for label in LABELS:
            matches = [r for r in parser.rows if r and r[0].startswith(label+' quarter')]
            if len(matches) != 1 or len(matches[0]) < 3:
                raise ValueError('Table HTML ambiguë ou absente : ' + label)
            pairs.append(matches[0][1:3])
    else:
        pairs = []
        for label in LABELS:
            matches = re.findall(label+r'\s+quarter\s+(\d+\.\d+)\s+(\d+\.\d+)', text)
            if len(matches) != 1:
                raise ValueError('Table PDF ambiguë ou absente : ' + label)
            pairs.append(matches[0])
    return [[int(Decimal(x)*1000000) for x in pair] for pair in pairs]


def collecter(cache, sortie, hors_ligne=False):
    from pypdf import PdfReader
    cache, sortie = Path(cache), Path(sortie)
    if sortie.exists():
        raise ValueError('Choisir un nouveau dossier : le jeu précédent reste figé')
    cache.mkdir(parents=True, exist_ok=True)
    values, sources = {}, []
    extracted = datetime.now(timezone.utc).isoformat()
    for year, page, filename, url in SOURCES:
        path = cache/filename
        if not path.exists():
            if hors_ligne: raise ValueError('Source absente du cache : '+filename)
            with urllib.request.urlopen(url, timeout=60) as response:
                blob = response.read()
            path.write_bytes(blob)
        blob = path.read_bytes()
        text = (PdfReader(path).pages[page-1].extract_text() if page
                else blob.decode('utf-8'))
        table = extraire_table(text, html=page is None)
        source_id = f'basicfit-rapport-{year}'
        sources.append(dict(id=source_id, url=url, page_pdf=page,
                            section='Membership development',
                            sha256=hashlib.sha256(blob).hexdigest(), cache=filename))
        for quarter, pair in enumerate(table, 1):
            for offset, value in enumerate(pair):
                period = f'{year-offset}-Q{quarter}'
                if period in values and values[period]['abonnements'] != value:
                    raise ValueError('Comparatifs contradictoires pour '+period)
                values[period] = dict(trimestre=period, abonnements=value, source_id=source_id,
                                      precision_publication_abonnements=10000)
    periods = sorted(values)
    expected = [f'{year}-Q{quarter}' for year in range(2020, 2026) for quarter in range(1, 5)]
    if periods != expected:
        raise ValueError('Couverture attendue : 24 trimestres de 2020 à 2025')
    sortie.mkdir(parents=True)
    csv_path = sortie/'abonnements_trimestriels.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[periods[0]]))
        writer.writeheader(); writer.writerows(values[p] for p in periods)
    manifest = dict(entreprise='Basic-Fit', relation_jiyufit='concurrent indirect fitness',
                    extraction_utc=extracted, frequence='trimestrielle',
                    mesure='abonnements en fin de trimestre, arrondis à 0.01 million',
                    perimetre='réseau Basic-Fit, ensemble des pays ; Clever Fit exclu en 2025',
                    statut='observations_publiees_par_entreprise',
                    interpolation=False, source_csv_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                    sources=sources,
                    limites=['Pas une part de marché ni un nombre de clients uniques actifs.',
                             'Chocs COVID 2020-2021 et reprise ; expansion géographique et acquisitions.',
                             'Test rétrospectif avec rapports publiés après les périodes, pas backtest de millésimes temps réel.',
                             'Une entreprise unique ne permet pas de tester la capture concurrentielle de Tullock.'])
    (sortie/'provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return csv_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('artifacts/sources/basicfit'))
    parser.add_argument('--sortie', type=Path, required=True)
    parser.add_argument('--hors-ligne', action='store_true')
    args = parser.parse_args()
    try:
        path = collecter(args.cache, args.sortie, args.hors_ligne)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f'24 observations trimestrielles publiées : {path}')


if __name__ == '__main__':
    main()
