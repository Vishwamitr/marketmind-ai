import logging
from analysis.regime_detector import RegimeDetector

logging.basicConfig(level=logging.INFO)

def verify():
    detector = RegimeDetector(symbol='INFY')
    
    # Test Latest
    print("--- Latest Regime ---")
    regime, metrics = detector.detect_regime()
    print(f"Regime: {regime.value}")
    print(f"Metrics: {metrics}")
    
    # We could test specific dates if we knew them, but latest is good for integration check.

if __name__ == "__main__":
    verify()
