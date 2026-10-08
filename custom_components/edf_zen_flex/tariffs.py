"""Import explicite de la grille publique EDF, sans écrasement silencieux du contrat."""
import asyncio
from datetime import date
from html import unescape
from html.parser import HTMLParser
import re
import unicodedata
from .model import REFERENCE_SOURCE, TARIFF_KEYS

MONTHS = {name: i for i, name in enumerate(('janvier','fevrier','mars','avril','mai','juin','juillet','aout','septembre','octobre','novembre','decembre'),1)}

def normal(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c)).split())

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headers, self.rows, self.row = [], [], []
        self.cell = None
        self.tag = None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr':self.row = []
        if tag in ('td','th'):self.cell, self.tag = [], tag
        if tag == 'br' and self.cell is not None:self.cell.append(' ')
    def handle_data(self, data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('td','th') and self.cell is not None:
            value = normal(''.join(self.cell))
            if self.tag == 'th':self.headers.append(value)
            else:self.row.append(value)
            self.cell, self.tag = None, None
        if tag == 'tr' and self.row:self.rows.append(self.row)


def parse_published_tariffs(html):
    tables = list(re.finditer(r'<table\b[^>]*class=["\'][^"\']*\bedf-gp-zenweflex__table\b[^"\']*["\'][^>]*>.*?</table>', html, re.I|re.S))
    if len(tables) != 1:
        raise ValueError('Grille publique EDF absente ou ambiguë')
    table = tables[0]
    parser = TableParser();parser.feed(table.group())
    expected = ['heures creuses jour eco','heures pleines jour eco','heures creuses jour sobriete','heures pleines jour sobriete']
    if 'option flex (ttc)' not in parser.headers or parser.headers[-4:] != expected:
        raise ValueError('Colonnes de la grille EDF non reconnues')
    rows = [row for row in parser.rows if len(row)==6 and row[0]=='6']
    if len(rows)!=1:raise ValueError('Ligne tarifaire EDF non reconnue')
    numbers = rows[0][2:]
    if not all(re.fullmatch(r'\d+[,.]\d{3,6}', text) for text in numbers):
        raise ValueError('Prix EDF non reconnus')
    rates = {key:float(text.replace(',','.')) for key,text in zip(TARIFF_KEYS,numbers)}
    if not all(0 < price <= 10 for price in rates.values()):raise ValueError('Prix EDF hors limites')
    following = normal(unescape(re.sub('<[^>]+>', ' ', html[table.end():table.end()+3000])))
    dates = re.findall(r'prix applicable a compter du (\d{1,2}) ([a-z]+) (\d{4}) pour toute nouvelle souscription', following)
    if len(dates)!=1 or dates[0][1] not in MONTHS:
        raise ValueError('Date d’application EDF non reconnue')
    day,month,year=dates[0]
    effective=date(int(year),MONTHS[month],int(day)).isoformat()
    return {**rates,'tariff_date':effective,'tariff_source':REFERENCE_SOURCE,'tariffs_confirmed':False}

async def fetch_published_tariffs(session):
    async with asyncio.timeout(20):
        async with session.get(REFERENCE_SOURCE) as response:
            response.raise_for_status()
            html=await response.text()
            if len(html)>2_000_000:raise ValueError('Réponse EDF trop volumineuse')
            return parse_published_tariffs(html)
