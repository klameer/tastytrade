"""
Comprehensive Watchlist for Options Scanner
Covers indices, sectors, and high-liquidity stocks
"""

WATCHLIST = {
    # Major Indices & ETFs
    'indices': [
        'SPY',    # S&P 500
        'QQQ',    # Nasdaq 100
        'IWM',    # Russell 2000
        'DIA',    # Dow Jones
        'SPX',    # S&P 500 Index Options
    ],
    
    # Technology
    'technology': [
        'AAPL',   # Apple
        'MSFT',   # Microsoft
        'GOOGL',  # Google
        'AMZN',   # Amazon
        'META',   # Meta
        'NVDA',   # Nvidia
        'TSLA',   # Tesla
        'AMD',    # AMD
        'INTC',   # Intel
        'CRM',    # Salesforce
        'ORCL',   # Oracle
        'ADBE',   # Adobe
        'NFLX',   # Netflix
        'AVGO',   # Broadcom
        'QCOM',   # Qualcomm
    ],
    
    # Financial
    'financial': [
        'JPM',    # JPMorgan
        'BAC',    # Bank of America
        'WFC',    # Wells Fargo
        'GS',     # Goldman Sachs
        'MS',     # Morgan Stanley
        'C',      # Citigroup
        'BLK',    # BlackRock
        'AXP',    # American Express
        'V',      # Visa
        'MA',     # Mastercard
        'PYPL',   # PayPal
    ],
    
    # Healthcare
    'healthcare': [
        'UNH',    # UnitedHealth
        'JNJ',    # Johnson & Johnson
        'PFE',    # Pfizer
        'ABBV',   # AbbVie
        'TMO',    # Thermo Fisher
        'MRK',    # Merck
        'LLY',    # Eli Lilly
        'ABT',    # Abbott
    ],
    
    # Consumer
    'consumer': [
        'WMT',    # Walmart
        'HD',     # Home Depot
        'DIS',    # Disney
        'NKE',    # Nike
        'MCD',    # McDonald's
        'SBUX',   # Starbucks
        'TGT',    # Target
        'COST',   # Costco
        'LOW',    # Lowe's
    ],
    
    # Energy
    'energy': [
        'XOM',    # Exxon Mobil
        'CVX',    # Chevron
        'COP',    # ConocoPhillips
        'SLB',    # Schlumberger
        'OXY',    # Occidental
        'XLE',    # Energy Sector ETF
    ],
    
    # Communications
    'communications': [
        'T',      # AT&T
        'VZ',     # Verizon
        'CMCSA',  # Comcast
        'TMUS',   # T-Mobile
    ],
    
    # Industrials
    'industrials': [
        'BA',     # Boeing
        'CAT',    # Caterpillar
        'GE',     # General Electric
        'UPS',    # UPS
        'FDX',    # FedEx
        'HON',    # Honeywell
    ],
    
    # Popular Trading Names
    'meme_and_trading': [
        'GME',    # GameStop
        'AMC',    # AMC Entertainment
        'PLTR',   # Palantir
        'SOFI',   # SoFi
        'RIVN',   # Rivian
        'LCID',   # Lucid
        'F',      # Ford
        'GM',     # General Motors
    ],
    
    # Commodity & Materials
    'commodities': [
        'GLD',    # Gold ETF
        'SLV',    # Silver ETF
        'USO',    # Oil ETF
        'FCX',    # Freeport-McMoRan
    ],
    
    # Volatile/High IV Stocks (good for premium selling)
    'high_volatility': [
        'COIN',   # Coinbase
        'SQ',     # Block (Square)
        'ROKU',   # Roku
        'ZM',     # Zoom
        'SNAP',   # Snap
        'UBER',   # Uber
        'LYFT',   # Lyft
        'PINS',   # Pinterest
    ],
}


def get_full_watchlist():
    """Get flat list of all unique symbols."""
    symbols = set()
    for category, tickers in WATCHLIST.items():
        symbols.update(tickers)
    return sorted(list(symbols))


def get_watchlist_by_category(category):
    """Get symbols for a specific category."""
    return WATCHLIST.get(category, [])


def get_all_categories():
    """Get all available categories."""
    return list(WATCHLIST.keys())


if __name__ == "__main__":
    full_list = get_full_watchlist()
    print(f"Total unique symbols: {len(full_list)}")
    print("\nCategories:")
    for cat in get_all_categories():
        print(f"  {cat}: {len(WATCHLIST[cat])} symbols")
    
    print(f"\nFull Watchlist:\n{', '.join(full_list)}")
