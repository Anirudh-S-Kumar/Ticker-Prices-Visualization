import yahooquery as yq
import re

"""Documentation for yahooquery history - https://yahooquery.dpguthrie.com/guide/ticker/historical/#history"""


class extendTicker(yq.Ticker):

    def __init__(self, query, **kwargs) -> None:
        """tickers will be found by search instead"""
        search_query = yq.search(query, first_quote=True)
        self.symbol = search_query["symbol"]
        self.name = search_query["shortname"]
        super().__init__(self.symbol, **kwargs)

    def get_info(self):
        """Return the company name, quote type, company summary, and logo for a given ticker if present"""
        ass = self.asset_profile[self.symbol]
        self.type = self.quote_type[self.symbol]["quoteType"].title()
        try:
            self.summary = ass["longBusinessSummary"]
        except KeyError:
            # print("Error 1")
            self.summary = ass["description"]
        except:
            self.summary = None

        try:
            website = ass['website'][12:]
            self.logo = f"https://logo.clearbit.com/{website}"
        except KeyError:
            # print("Error 2")
            pattern = re.compile(r'https?://(www\.)?(\w+)(\.\w+)')
            matched_url = re.search(pattern, self.summary).group(0)
            website = pattern.sub(r'\2\3', matched_url)
            self.logo = f"https://logo.clearbit.com/{website}"
        except:
            self.logo = None

        temp = (self.name, self.type, self.summary, self.logo)
        return temp

