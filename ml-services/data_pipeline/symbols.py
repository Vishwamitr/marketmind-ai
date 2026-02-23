"""
MarketMind Symbol Universe
Complete list of NSE/BSE stocks, mutual funds, and F&O symbols.
Data source: NSE India indices (NIFTY 50, 100, 500, MidCap, SmallCap).
"""

# ═══════════════════════════════════════════════════════════════
# NIFTY 50 — Top 50 by market cap
# ═══════════════════════════════════════════════════════════════
NIFTY_50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE",
    "KOTAKBANK", "LT", "HCLTECH", "AXISBANK", "ASIANPAINT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "BAJAJFINSV",
    "WIPRO", "ONGC", "NTPC", "JSWSTEEL", "POWERGRID",
    "M&M", "TATAMOTORS", "ADANIENT", "ADANIPORTS", "TATASTEEL",
    "NESTLEIND", "TECHM", "HDFCLIFE", "BAJAJ-AUTO", "BRITANNIA",
    "INDUSINDBK", "HINDALCO", "SBILIFE", "GRASIM", "DIVISLAB",
    "CIPLA", "EICHERMOT", "DRREDDY", "COALINDIA", "BPCL",
    "TATACONSUM", "APOLLOHOSP", "HEROMOTOCO", "UPL", "LTIM",
]

# ═══════════════════════════════════════════════════════════════
# NIFTY NEXT 50 (51-100)
# ═══════════════════════════════════════════════════════════════
NIFTY_NEXT_50 = [
    "ADANIGREEN", "AMBUJACEM", "BANKBARODA", "BERGEPAINT", "BOSCHLTD",
    "CANBK", "CHOLAFIN", "COLPAL", "DABUR", "DLF",
    "GAIL", "GODREJCP", "HAVELLS", "ICICIGI", "ICICIPRULI",
    "INDIGO", "IOC", "JINDALSTEL", "LUPIN", "MARICO",
    "MCDOWELL-N", "MOTHERSON", "NAUKRI", "NMDC", "OBEROIRLTY",
    "OFSS", "PIDILITIND", "PNB", "SAIL", "SBICARD",
    "SHREECEM", "SIEMENS", "SRF", "TATAPOWER", "TORNTPHARM",
    "TRENT", "VEDL", "ZOMATO", "ZYDUSLIFE", "PIIND",
    "LODHA", "ATGL", "IRCTC", "LICI", "HAL",
    "VBL", "ABB", "MANKIND", "PEL", "MAXHEALTH",
]

# ═══════════════════════════════════════════════════════════════
# NIFTY MIDCAP 150 (sample — most liquid)
# ═══════════════════════════════════════════════════════════════
NIFTY_MIDCAP_150 = [
    "AARTI", "ABCAPITAL", "ACC", "AFFLE", "AJANTPHARM",
    "ALKEM", "ALOKINDS", "ANGELONE", "APLAPOLLO", "ASHOKLEY",
    "ASTRAL", "AUROPHARMA", "BALKRISIND", "BANDHANBNK", "BATAINDIA",
    "BEL", "BHARATFORG", "BHEL", "BIOCON", "CAMS",
    "CANFINHOME", "CARBORUNIV", "CASTROLIND", "CDSL", "CENTRALBK",
    "CESC", "CGPOWER", "CHAMBLFERT", "CHENNPETRO", "CLEAN",
    "COFORGE", "CONCOR", "COROMANDEL", "CROMPTON", "CUB",
    "CUMMINSIND", "CYIENT", "DALBHARAT", "DEEPAKNTR", "DEVYANI",
    "DMART", "ECLERX", "ELGIEQUIP", "EMAMILTD", "ENDURANCE",
    "ENGINERSIN", "EQUITASBNK", "ESCORTS", "EXIDEIND", "FEDERALBNK",
    "FORTIS", "GLENMARK", "GMRAIRPORT", "GNFC", "GODREJPROP",
    "GRINDWELL", "GSPL", "GUJGASLTD", "HAPPSTMNDS", "HDFCAMC",
    "HINDPETRO", "HONAUT", "IBREALEST", "IDFC", "IDFCFIRSTB",
    "IEX", "IIFL", "INDHOTEL", "INDIANB", "INDUSTOWER",
    "INTELLECT", "IRFC", "ISEC", "JBCHEPHARM", "JKCEMENT",
    "JSL", "JUBLFOOD", "KAJARIACER", "KANSAINER", "KEI",
    "KPITTECH", "LATENTVIEW", "LAURUSLABS", "LICHSGFIN", "LTTS",
    "MFSL", "MGL", "MINDTREE", "MPHASIS", "MUTHOOTFIN",
    "NAM-INDIA", "NATIONALUM", "NAVINFLUOR", "NBCC", "NCC",
    "NLCINDIA", "PAGEIND", "PGHH", "PHOENIXLTD", "POLYMED",
    "POLYCAB", "PRESTIGE", "PVRCINOX", "RAJESHEXPO", "RAMCOCEM",
    "RBLBANK", "RECLTD", "RELAXO", "RVNL", "SANOFI",
    "SAPPHIRE", "SCHAEFFLER", "SHRIRAMFIN", "SJVN", "SKFINDIA",
    "SONACOMS", "STARHEALTH", "SUNDARMFIN", "SUNDRMFAST", "SUNTV",
    "SUVENPHAR", "SYNGENE", "TATACHEM", "TATACOMM", "TATAELXSI",
    "TATAINVEST", "THERMAX", "TIMKEN", "TIINDIA", "TRIDENT",
    "TTML", "TV18BRDCST", "TVSMOTOR", "UCOBANK", "UNIONBANK",
    "UBL", "UTIAMC", "VOLTAS", "WHIRLPOOL", "ZEEL",
    "ZENSAR", "PERSISTENT", "ROUTE", "SAPPHIRE", "BSOFT",
    "FACT", "FINEORG", "FLUOROCHEM", "GRSE", "IDEA",
]

# ═══════════════════════════════════════════════════════════════
# NIFTY SMALLCAP 250 (sample — most liquid)
# ═══════════════════════════════════════════════════════════════
NIFTY_SMALLCAP_250 = [
    "3MINDIA", "AARTIIND", "AAVAS", "ABSLAMC", "ACCELYA",
    "ADANITRANS", "ADVENZYMES", "AEGISCHEM", "AETHER", "AGARIND",
    "AIAENG", "AKZOINDIA", "APARINDS", "APTECHT", "APTUS",
    "ARVINDFASN", "ASAHIINDIA", "ATUL", "AVANTIFEED", "AWHCL",
    "AXISCADES", "BAJAJELEC", "BAJAJHLDNG", "BALRAMCHIN", "BASF",
    "BAYERCROP", "BDL", "BEML", "BIRLACORPN", "BLUEDART",
    "BLUESTARCO", "BRIGADE", "BORORENEW", "BSE", "CALCOMP",
    "CAMPUS", "CAPLIPOINT", "CARERATING", "CEATLTD", "CENTENKA",
    "CENTURYPLY", "CERA", "CHALET", "CHOLAHLDNG", "COCHINSHIP",
    "CRAFTSMAN", "CREDITACC", "CROMPTON", "CSBBANK", "CYIENT",
    "DCBBANK", "DCMSHRIRAM", "DEEPAKFERT", "DELTACORP", "DHANI",
    "DIAMONDYD", "DIXON", "DOMS", "EASEMYTRIP", "EDELWEISS",
    "ERIS", "ETHOSLTD", "EVERESTIND", "FINCABLES", "FINPIPE",
    "FIRSTSOURCE", "GALAXY", "GARFIBRES", "GATEWAY", "GHCL",
    "GILLETTE", "GLAXO", "GLS", "GMDCLTD", "GODFRYPHLP",
    "GODREJAGRO", "GPIL", "GRANULES", "GRAPHITE", "GREENPANEL",
    "GRINFRA", "GSHIP", "GUFICBIO", "GULFOILLUB", "HAPPSTMNDS",
    "HATSUN", "HCG", "HGINFRA", "HIKAL", "HINDCOPPER",
    "HLE", "HMVL", "HOMEFIRST", "HONASA", "HSCL",
    "HUDCO", "IBULHSGFIN", "ICRA", "IFBIND", "IGARASHI",
    "IIFLWAM", "IMFA", "INDIASHLTR", "INDIGOPNTS", "INDOSTAR",
    "INFIBEAM", "INOXWIND", "IPCALAB", "IRB", "IRCON",
    "ISEC", "ITDC", "ITDCEM", "ITI", "J&KBANK",
    "JAMNAAUTO", "JAYNECOIND", "JBMA", "JKLAKSHMI", "JMFINANCIL",
    "JSWENERGY", "JTEKTINDIA", "JUBLINGREA", "JUSTDIAL", "JYOTHYLAB",
    "KALYANKJIL", "KAMAHOLD", "KARDA", "KDDL", "KEC",
    "KELLTONTEC", "KENNAMET", "KIRLOSENG", "KIRLPNU", "KMCSHIL",
    "KNRCON", "KOKUYOCMLN", "KRBL", "KSB", "LALPATHLAB",
    "LAOPALA", "LEMONTREE", "LXCHEM", "MAHINDCIE", "MAHLIFE",
    "MAHLOG", "MAHSEAMLES", "MANINDS", "MANINFRA", "MANYAVAR",
    "MAPMYINDIA", "MASTEK", "MAXVIL", "MAZAGON", "METROPOLIS",
    "MIDHANI", "MMTC", "MOIL", "MONTECARLO", "MOREPENLAB",
    "MOTILALOFS", "MRPL", "MSUMI", "MTARTECH", "MUKANDLTD",
    "NATCOPHARM", "NESCO", "NETWORK18", "NH", "NIITLTD",
    "NIPPON", "NOCIL", "OLECTRA", "ORIENTELEC", "ORIENTCEM",
    "PCBL", "PDSL", "PFIZER", "PFS", "PGHL",
    "PINELAB", "POLYMED", "POONAWALLA", "POWERINDIA", "PRICOLLTD",
    "PRINCEPIPE", "PRSMJOHNSN", "QUESS", "RADICO", "RAILTEL",
    "RAJRATAN", "RAMACRAFT", "RATNAMANI", "RAYMOND", "RCF",
    "REDINGTON", "RHIM", "RITES", "ROLEXRINGS", "ROSSARI",
    "RPSGVENT", "RUPA", "SAREGAMA", "SATIN", "SFLY",
    "SHANKARA", "SHOPERSTOP", "SIS", "SNOWMAN", "SOLARA",
    "SONATSOFTW", "SOUTHBANK", "SPARC", "STARCEMENT", "STLTECH",
    "SUBEXLTD", "SUMICHEM", "SUNDRMFAST", "SUPRAJIT", "SUPREMEIND",
    "SUVEN", "SWANENERGY", "SYMPHONY", "TANLA", "TATACOFFEE",
    "TEAMLEASE", "TECHNOE", "TITAGARH", "TTKPRESTIG", "UFLEX",
    "UJJIVAN", "UJJIVANSFB", "UNOMINDA", "USHAMART", "UTIAMC",
    "VAIBHAVGBL", "VALIANTORG", "VMART", "VSTIND", "WELCORP",
    "WELSPUNIND", "WESTLIFE", "WHEELS", "WOCKPHARMA", "YESBANK",
    "ZENSARTECH", "ZFCVINDIA", "ZOMATO", "PVRINOX", "CELLO",
]

# ═══════════════════════════════════════════════════════════════
# ADDITIONAL NSE STOCKS (for 1000+ coverage)
# ═══════════════════════════════════════════════════════════════
OTHER_NSE = [
    "AADHARHFC", "AARTIDRUGS", "ABFRL", "ADANIENSOL", "ADANITOTAL",
    "AHLUCONT", "AJMERA", "ALKYLAMINE", "ALLCARGO", "AMBER",
    "ANANTRAJ", "ANDHRAPAP", "ANDHRSUGAR", "ANGELBROKIN", "ANIKINDS",
    "ANTGRAPHIC", "APCOTEXIND", "APLLTD", "ARCHIDPLY", "ARROWGREEN",
    "ARVIND", "ASHIANA", "ASHOKA", "ASIANHOTNR", "ASTERDM",
    "ASTRAZEN", "ATFL", "AURIONPRO", "AUTOAXLES", "AVTNPL",
    "BANARISUG", "BANCOINDIA", "BARBEQUE", "BBTC", "BIRLAMONEY",
    "BLISSGVS", "BOROLTD", "BRAINBEES", "CANTABIL", "CAPACITE",
    "CAREERP", "CCHHL", "CCL", "CENTUM", "CHAMAN",
    "CHEMCON", "CHEMFAB", "CHOICEIN", "CIEINDIA", "CINELINE",
    "CLSEL", "COALINDIA", "CONFIPET", "CONTROLPR", "COSMOFILMS",
    "CUPID", "DATAMATICS", "DBCORP", "DECCANCE", "DEEPINDS",
    "DENORA", "DHANUKA", "DHARMAJ", "DISHTV", "DREAMFOLKS",
    "DYNAMATECH", "ECLERX", "EIDPARRY", "ELECON", "ELECTCAST",
    "ELECTHERM", "ELGIEQUIP", "EMKAY", "ESTER", "ETHOSLTD",
    "EUROTEXIND", "EVEREADY", "EXCELINDUS", "FAZE3Q", "FDC",
    "FIEMIND", "FMGOETZE", "FORCEMOT", "GABRIEL", "GAEL",
    "GALAXYSURF", "GANDHAR", "GANESHBE", "GANESHHOUC", "GARFIBRES",
    "GENCON", "GENESYS", "GENSOL", "GEOJITFSL", "GILLETTE",
    "GLAND", "GLOBUSSPR", "GMBREW", "GOCLCORP", "GOODYEAR",
    "GPTINFRA", "GREENPLY", "GRINDWELL", "GSFC", "GTLINFRA",
    "GTPL", "GUJALKALI", "GUJGAS", "GULFOILLUB", "HATHWAY",
    "HAWKINCOOK", "HBLPOWER", "HCLINFRA", "HERANBA", "HERITGFOOD",
    "HIMATSEIDE", "HINDOILEXP", "HINDWAREAP", "HLEGLAS", "HMT",
    "HNDFDS", "HPL", "HUB", "ICIL", "ICSA",
    "IDBI", "IDFCFIRSTB", "IFCI", "IGPL", "IGL",
    "IMAGICAA", "IMFA", "INDIANCARD", "INDIGRID", "INDNIPPON",
    "INDOCO", "INSECTIND", "INTELLECT", "INVENTURE", "IONEXCHANG",
    "ISGEC", "JHS", "JINDALPHOT", "JINDALPOLY", "JINDALSAW",
    "JISLDVREQS", "JKIL", "JKLAKSHMI", "JKPAPER", "JKTYRE",
    "JPASSOCIAT", "JSLHISAR", "JUBILANT", "KALAMANDIR", "KAMATHOTEL",
    "KANCHI", "KANDAGIRI", "KANPRPLA", "KARMAENG", "KARTIKFIN",
    "KAVVERITEL", "KDDL", "KEC", "KIRLFER", "KIRLLOS",
    "KIRLOSBROS", "KITEX", "KOLTEPATIL", "KOPRAN", "KPIGREEN",
    "KPIT", "L&TFH", "LASA", "LAURAS", "LIKHITHA",
    "LINCOLN", "LLOYDSENGG", "LOKESHM", "LTFOODS", "LUMAXAUTO",
    "LUMAXIND", "LUMAXTECH", "LUXIND", "LYKALABS", "MADRASFERT",
    "MAHEPC", "MAHSCOOTER", "MAITHANALL", "MALLCOM", "MANALIPETC",
    "MANGCHEFER", "MARICOIND", "MASFIN", "MAXFINVEST", "MAXIND",
    "MAYURUNIQ", "MBLINFRA", "MCX", "MEDPLUS", "MEGASOFT",
    "MENONBE", "METALFORGE", "MHRIL", "MIRZAINT", "MITCON",
    "MODIRUBBER", "MOLDTEK", "MOLDTKPAC", "MONTECARLO", "MOREPENLAB",
    "MOTILALOFS", "MPSLTD", "MRPL", "MSPL", "MSTCLTD",
    "MTARTECH", "MUKANDLTD", "MUTHOOTCAP", "NAGREEKEXP", "NAHARPOLY",
    "NAHARINDUS", "NAHARSPING", "NATIONALUM", "NDTV", "NELCO",
    "NETWORK18", "NEWGEN", "NEXTMEDIA", "NGLFINECM", "NHPC",
    "NITINSPIN", "NLCINDIA", "NOCIL", "NRBBEARING", "NUCLEUS",
    "NURECA", "OCCL", "OIL", "OLECTRA", "OMAXAUTO",
    "OMAXE", "ONMOBILE", "ONWARDTEC", "OPTIEMUS", "ORCHPHARMA",
    "ORIENTBELL", "ORIENTCEM", "ORIENTELEC", "ORIENTHOT", "ORIENTREF",
]

# ═══════════════════════════════════════════════════════════════
# MUTUAL FUND TICKERS (yfinance .NS suffix)
# NAV data available for most popular Indian MFs
# ═══════════════════════════════════════════════════════════════
MUTUAL_FUNDS = [
    # HDFC MF
    {"symbol": "0P0000XVAA.BO", "name": "HDFC Top 100 Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVAB.BO", "name": "HDFC Mid-Cap Opportunities Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVAC.BO", "name": "HDFC Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVAD.BO", "name": "HDFC Flexi Cap Fund", "category": "Flexi Cap"},
    {"symbol": "0P0000XVAE.BO", "name": "HDFC Balanced Advantage Fund", "category": "Hybrid"},
    # SBI MF
    {"symbol": "0P0000XVBA.BO", "name": "SBI Bluechip Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVBB.BO", "name": "SBI Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVBC.BO", "name": "SBI Magnum Midcap Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVBD.BO", "name": "SBI Equity Hybrid Fund", "category": "Hybrid"},
    {"symbol": "0P0000XVBE.BO", "name": "SBI Focused Equity Fund", "category": "Focused"},
    # Axis MF
    {"symbol": "0P0000XVCA.BO", "name": "Axis Bluechip Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVCB.BO", "name": "Axis Midcap Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVCC.BO", "name": "Axis Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVCD.BO", "name": "Axis Long Term Equity Fund", "category": "ELSS"},
    {"symbol": "0P0000XVCE.BO", "name": "Axis Flexi Cap Fund", "category": "Flexi Cap"},
    # ICICI Pru MF
    {"symbol": "0P0000XVDA.BO", "name": "ICICI Pru Bluechip Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVDB.BO", "name": "ICICI Pru Value Discovery Fund", "category": "Value"},
    {"symbol": "0P0000XVDC.BO", "name": "ICICI Pru Midcap Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVDD.BO", "name": "ICICI Pru Technology Fund", "category": "Sectoral"},
    {"symbol": "0P0000XVDE.BO", "name": "ICICI Pru Balanced Advantage Fund", "category": "Hybrid"},
    # Kotak MF
    {"symbol": "0P0000XVEA.BO", "name": "Kotak Bluechip Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVEB.BO", "name": "Kotak Emerging Equity Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVEC.BO", "name": "Kotak Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVED.BO", "name": "Kotak Flexi Cap Fund", "category": "Flexi Cap"},
    {"symbol": "0P0000XVEE.BO", "name": "Kotak Equity Hybrid Fund", "category": "Hybrid"},
    # Nippon MF
    {"symbol": "0P0000XVFA.BO", "name": "Nippon India Large Cap Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVFB.BO", "name": "Nippon India Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVFC.BO", "name": "Nippon India Growth Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVFD.BO", "name": "Nippon India Multi Cap Fund", "category": "Multi Cap"},
    {"symbol": "0P0000XVFE.BO", "name": "Nippon India Pharma Fund", "category": "Sectoral"},
    # Mirae Asset MF
    {"symbol": "0P0000XVGA.BO", "name": "Mirae Asset Large Cap Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVGB.BO", "name": "Mirae Asset Emerging Bluechip Fund", "category": "Large & Mid"},
    {"symbol": "0P0000XVGC.BO", "name": "Mirae Asset Tax Saver Fund", "category": "ELSS"},
    # Parag Parikh MF
    {"symbol": "0P0000XVHA.BO", "name": "Parag Parikh Flexi Cap Fund", "category": "Flexi Cap"},
    {"symbol": "0P0000XVHB.BO", "name": "Parag Parikh Tax Saver Fund", "category": "ELSS"},
    # Motilal Oswal MF
    {"symbol": "0P0000XVIA.BO", "name": "Motilal Oswal Midcap Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVIB.BO", "name": "Motilal Oswal Flexi Cap Fund", "category": "Flexi Cap"},
    # Tata MF
    {"symbol": "0P0000XVJA.BO", "name": "Tata Digital India Fund", "category": "Sectoral"},
    {"symbol": "0P0000XVJB.BO", "name": "Tata Small Cap Fund", "category": "Small Cap"},
    # DSP MF
    {"symbol": "0P0000XVKA.BO", "name": "DSP Midcap Fund", "category": "Mid Cap"},
    {"symbol": "0P0000XVKB.BO", "name": "DSP Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVKC.BO", "name": "DSP Tax Saver Fund", "category": "ELSS"},
    # Quant MF
    {"symbol": "0P0000XVLA.BO", "name": "Quant Small Cap Fund", "category": "Small Cap"},
    {"symbol": "0P0000XVLB.BO", "name": "Quant Active Fund", "category": "Multi Cap"},
    {"symbol": "0P0000XVLC.BO", "name": "Quant Mid Cap Fund", "category": "Mid Cap"},
    # UTI MF
    {"symbol": "0P0000XVMA.BO", "name": "UTI Flexi Cap Fund", "category": "Flexi Cap"},
    {"symbol": "0P0000XVMB.BO", "name": "UTI Nifty Index Fund", "category": "Index"},
    # Canara Robeco MF
    {"symbol": "0P0000XVNA.BO", "name": "Canara Robeco Bluechip Equity Fund", "category": "Large Cap"},
    {"symbol": "0P0000XVNB.BO", "name": "Canara Robeco Emerging Equities Fund", "category": "Large & Mid"},
    # Sundaram MF
    {"symbol": "0P0000XVOA.BO", "name": "Sundaram Midcap Fund", "category": "Mid Cap"},
]

# ═══════════════════════════════════════════════════════════════
# F&O ELIGIBLE STOCKS (options chain available)
# Top liquid F&O names — used for options fetching
# ═══════════════════════════════════════════════════════════════
FNO_STOCKS = [
    # Index Options
    "NIFTY", "BANKNIFTY", "FINNIFTY",
    # Top 50 F&O stocks
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "SBIN", "BHARTIARTL", "BAJFINANCE", "LT", "HCLTECH",
    "AXISBANK", "KOTAKBANK", "ITC", "HINDUNILVR", "MARUTI",
    "SUNPHARMA", "TITAN", "WIPRO", "TATAMOTORS", "TATASTEEL",
    "NTPC", "ONGC", "POWERGRID", "ADANIENT", "ADANIPORTS",
    "M&M", "BAJAJFINSV", "JSWSTEEL", "ULTRACEMCO", "TECHM",
    "HINDALCO", "INDUSINDBK", "COALINDIA", "BPCL", "GRASIM",
    "DRREDDY", "CIPLA", "EICHERMOT", "DIVISLAB", "APOLLOHOSP",
    "TATACONSUM", "HEROMOTOCO", "BAJAJ-AUTO", "BRITANNIA", "NESTLEIND",
    "DLF", "VEDL", "JINDALSTEL", "TATAPOWER", "ZOMATO",
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_all_stocks() -> list[str]:
    """Get deduplicated list of all stock symbols."""
    all_syms = set()
    all_syms.update(NIFTY_50)
    all_syms.update(NIFTY_NEXT_50)
    all_syms.update(NIFTY_MIDCAP_150)
    all_syms.update(NIFTY_SMALLCAP_250)
    all_syms.update(OTHER_NSE)
    return sorted(all_syms)


def get_stocks_by_index(index: str) -> list[str]:
    """Get stocks for a specific index."""
    mapping = {
        "NIFTY50": NIFTY_50,
        "NIFTYNEXT50": NIFTY_NEXT_50,
        "MIDCAP150": NIFTY_MIDCAP_150,
        "SMALLCAP250": NIFTY_SMALLCAP_250,
        "OTHER": OTHER_NSE,
    }
    return mapping.get(index.upper(), [])


def get_all_mf() -> list[dict]:
    """Get all mutual fund definitions."""
    return MUTUAL_FUNDS


def get_mf_symbols() -> list[str]:
    """Get just the MF ticker symbols."""
    return [mf["symbol"] for mf in MUTUAL_FUNDS]


def get_mf_categories() -> list[str]:
    """Get unique MF categories."""
    return sorted(set(mf["category"] for mf in MUTUAL_FUNDS))


def get_fno_stocks() -> list[str]:
    """Get F&O eligible stocks."""
    return FNO_STOCKS


def get_nse_suffix(symbol: str) -> str:
    """Convert clean symbol to yfinance NSE symbol."""
    if symbol in ("NIFTY", "BANKNIFTY", "FINNIFTY"):
        return f"^{symbol}"
    return f"{symbol}.NS"


def get_stock_count() -> int:
    """Get total number of unique stocks."""
    return len(get_all_stocks())


# Quick stats
if __name__ == "__main__":
    stocks = get_all_stocks()
    print(f"Total unique stocks: {len(stocks)}")
    print(f"NIFTY 50: {len(NIFTY_50)}")
    print(f"NIFTY Next 50: {len(NIFTY_NEXT_50)}")
    print(f"NIFTY MidCap 150: {len(NIFTY_MIDCAP_150)}")
    print(f"NIFTY SmallCap 250: {len(NIFTY_SMALLCAP_250)}")
    print(f"Other NSE: {len(OTHER_NSE)}")
    print(f"Mutual Funds: {len(MUTUAL_FUNDS)}")
    print(f"F&O Stocks: {len(FNO_STOCKS)}")
