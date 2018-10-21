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


FUND_D = {
     "L Income Fund" : "LInc",
     "L 2020 Fund" : "L2020",
     "L 2030 Fund" : "L2030",
     "L 2040 Fund" : "L2040",
     "L 2050 Fund" : "L2050",
     "Common Stock Index Investment (C) Fund" : "CFund",
     "Small Capitalization Stock Index Investment (S) Fund" : "SFund",
     "International Stock Index Investment (I) Fund" : "IFund",
     "Government Securities Investment (G) Fund" : "GFund", #Maybe?
     "Fixed Income Index Investment (F) Fund" : "FFund", #Maybe?
}

#TODO: Make this generate from the dictionary above.
FUND_RE = '(?P<fund>L 2020|L 2050|International Stock Index Investment \(I\)|L 2040|Small Capitalization Stock Index Investment \(S\)|L 2030|Fixed Income Index Investment \(F\)|Government Securities Investment \(G\)|L Income|Common Stock Index Investment \(C\))(?P<data>.+?)(Ending Balance|Continued on next page)'

TRXN_RE = '(?P<date>(\d{2}\/){2}\d{4})\s*(?P<desc>[\w\s]+?)\s*\${0,1}(?P<trad>(Œ|-){0,1}\s*([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{2})\s*\${0,1}(?P<roth>(Œ|-){0,1}\s*([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{2})\s*\${0,1}(?P<total>(Œ|-){0,1}\s*([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{2})\s*\${0,1}(?P<price>(Œ|-){0,1}\s*([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{4})\s*(?P<shares>(Œ|-){0,1}\s*([0-9]{0,3},)*[0-9]{0,3}\.[0-9]{4})'


class Importer(importer.ImporterProtocol):
    def __init__(self, cash_account, tsp_root):
        self.cash_account = cash_account
        self.tsp_root = tsp_root

    def identify(self, f):
        return re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}_tsp_statement.(pdf|PDF)',
                        os.path.basename(f.name))

    def file_account(self, f):
        return self.tsp_root

    def extract(self, f):
        entries = []

        with open(f.name, 'rb') as pdf_file:

            read_pdf = PyPDF2.PdfFileReader(pdf_file)

            all_text = "".join(
                read_pdf.getPage(curr_page).extractText()
                for curr_page in range(read_pdf.numPages)
            )

            data_re = re.compile(TRXN_RE)
            fund_re = re.compile(FUND_RE)

            fund_match = [m.groupdict() for m in fund_re.finditer(all_text)]

            for index, row in enumerate(fund_match):
                fund_text = row['fund'].strip()
                text = row['data'].strip()

                fund = FUND_D[fund_text + " Fund"]

                matches = [m.groupdict() for m in data_re.finditer(text)]

                for index, row in enumerate(matches):

                    trans_date = parse(row['date']).date()

                    trans_desc = titlecase(row['desc'].strip())
                    trans_amt = row['total'].replace("Œ", '-')
                    shares = row['shares'].replace("Œ", '-')
                    price = row['price'].replace("Œ", '-')
                    total = row['total'].replace("Œ", '-')

                    meta = data.new_metadata(f.name, index)

                    # Trans_amt in TSP statement is relative to dollars in fund
                    # Changes sign when relative to "Cash" account in TSP
                    if "-" in trans_amt:
                        trans_amt = trans_amt.replace("-", "")
                    else:
                        trans_amt = "-" + trans_amt

                    # Clean up the description to standardize naming.
                    # After fixed above, negative on amnt means purchase.
                    if ("contribution" in trans_desc.lower() and
                        "-" in trans_amt):
                        trans_desc = fund.title() + " purchase"

                    txn = data.Transaction(
                        meta=meta,
                        date=trans_date,
                        flag=flags.FLAG_OKAY,
                        payee="Thrift Savings Plan",
                        narration=trans_desc,
                        tags=set(),
                        links=set(),
                        postings=[]
                    )

                    txn.postings.append(
                        data.Posting(
                            self.tsp_root + ":" + fund,
                            amount.Amount(D(shares), ("TSP" + fund).upper()),
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
                            amount.Amount(D(trans_amt), 'USD'),
                            None, None, None, None))

                    entries.append(txn)

        return entries
