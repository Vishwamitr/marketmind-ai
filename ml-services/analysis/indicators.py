import pandas as pd
import pandas_ta as ta
import logging
from utils.config import Config

# Configure logger
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    """
    Calculates technical indicators for stock data.
    """

    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all configured indicators.
        
        Args:
            data (pd.DataFrame): Dataframe with OHLCV columns (Open, High, Low, Close, Volume).
        
        Returns:
            pd.DataFrame: Dataframe with added indicator columns.
        """
        if data.empty:
            logger.warning("Empty data provided for analysis.")
            return data

        # Ensure correct types
        data = data.copy() # Avoid SettingWithCopyWarning
        data['Close'] = data['Close'].astype(float)
        data['High'] = data['High'].astype(float)
        data['Low'] = data['Low'].astype(float)

        try:
            # Momentum
            self.calculate_rsi(data)
            data = self.calculate_macd(data)
            
            # Volatility
            data = self.calculate_bollinger(data)
            self.calculate_atr(data)
            
            # Trend
            self.calculate_moving_averages(data)
            data = self.calculate_adx(data)
            
            logger.debug(f"Calculated indicators: {data.columns.tolist()}")
            return data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return data

    def calculate_rsi(self, data: pd.DataFrame, length: int = 14):
        """Relative Strength Index"""
        data[f'RSI_{length}'] = ta.rsi(data['Close'], length=length)

    def calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Moving Average Convergence Divergence"""
        macd = ta.macd(data['Close'], fast=fast, slow=slow, signal=signal)
        if macd is not None:
            data = pd.concat([data, macd], axis=1)
        return data

    def calculate_bollinger(self, data: pd.DataFrame, length: int = 20, std: float = 2.0) -> pd.DataFrame:
        """Bollinger Bands"""
        bb = ta.bbands(data['Close'], length=length, std=std)
        if bb is not None:
            data = pd.concat([data, bb], axis=1)
        return data

    def calculate_moving_averages(self, data: pd.DataFrame):
        """SMA and EMA"""
        data['SMA_20'] = ta.sma(data['Close'], length=20)
        data['SMA_50'] = ta.sma(data['Close'], length=50)
        data['SMA_200'] = ta.sma(data['Close'], length=200)
        data['EMA_12'] = ta.ema(data['Close'], length=12)
        data['EMA_26'] = ta.ema(data['Close'], length=26)

    def calculate_atr(self, data: pd.DataFrame, length: int = 14):
        """Average True Range"""
        data[f'ATR_{length}'] = ta.atr(data['High'], data['Low'], data['Close'], length=length)

    def calculate_adx(self, data: pd.DataFrame, length: int = 14) -> pd.DataFrame:
        """Average Directional Index"""
        adx = ta.adx(data['High'], data['Low'], data['Close'], length=length)
        if adx is not None:
            data = pd.concat([data, adx], axis=1)
        return data
