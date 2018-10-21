from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import amount
from beancount.core import flags
from beancount.core import data
from beancount.core import position

from dateutil.parser import parse

from titlecase import titlecase

import os
import re

import PyPDF2

REGEX = '(?P<date>(\d{2}\/){2}\d{4})\s*(?P<desc>\w+)\s*\${0,1}(?P<trad>([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{2})\s*\${0,1}(?P<roth>([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{2})\s*\${0,1}(?P<total>([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{2})\s*\${0,1}(?P<price>([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{4})\s*(?P<shares>([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{4})'


class Importer(importer.ImporterProtocol):
    def __init__(self, cash_account, invest_account):
        self.cash_account = cash_account
        self.invest_account = invest_account

    def identify(self, f):
        return re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}_tsp_statement.(pdf|PDF)',
                        os.path.basename(f.name))

    def file_account(self, f):
        return self.invest_account

    def extract(self, f):
        entries = []

        with open(f.name, 'rb') as pdf_file:

            read_pdf = PyPDF2.PdfFileReader(pdf_file)

            page = read_pdf.getPage(2)

            page_content = page.extractText()

            data_re = re.compile(REGEX)

            matches = [m.groupdict() for m in data_re.finditer(page_content)]

            for index, row in enumerate(matches):
                trans_date = parse(row['date']).date()

                trans_desc = titlecase(row['desc'].strip())
                trans_amt = row['total']
                shares = row['shares']
                price = row['price']
                total = row['total']

                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trans_date,
                    flag=flags.FLAG_OKAY,
                    payee=trans_desc,
                    narration="",
                    tags=set(),
                    links=set(),
                    postings=[]
                )

                txn.postings.append(
                    data.Posting(
                        self.invest_account,
                        amount.Amount(D(shares), 'TSPL2050'),
                        position.Cost(
                            D(price),
                            'USD',
                            None, None),
                        None,
                        None,
                        None))


                txn.postings.append(
                    data.Posting(
                        self.cash_account,
                        amount.Amount(D("-" + trans_amt), 'USD'),
                        None, None, None, None))

                entries.append(txn)

        return entries
