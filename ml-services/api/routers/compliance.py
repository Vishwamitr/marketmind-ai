from fastapi import APIRouter

router = APIRouter()

DISCLAIMER_TEXT = """
MarketMind AI is an educational tool powered by Artificial Intelligence. 
It does NOT provide investment advice, recommendations, or financial analysis services.
All predictions and data are for informational purposes only. 
Investments in securities market are subject to market risks. Read all the related documents carefully before investing.
Registration granted by SEBI, membership of BASL (in case of IAs) and certification from NISM in no way guarantee performance of the intermediary or provide any assurance of returns to investors.
"""

RISK_DISCLOSURE = """
Risk Disclosure Document on Derivatives:
9 out of 10 individual traders in equity Future and Options Segment, incurred net losses.
On an average, loss makers registered net trading loss close to ₹ 50,000.
Over and above the net trading losses incurred, loss makers expended an additional 28% of net trading losses as transaction costs.
Those making net trading profits, incurred between 15% to 50% of such profits as transaction cost.
"""

@router.get("/compliance/disclaimer")
def get_disclaimer():
    return {"disclaimer": DISCLAIMER_TEXT.strip()}

@router.get("/compliance/risk")
def get_risk_disclosure():
    return {"risk_disclosure": RISK_DISCLOSURE.strip()}
