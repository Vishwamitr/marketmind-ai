import pandas as pd
import numpy as np

from typing import List, Union

def calculate_metrics(history: Union[List[dict], pd.DataFrame]) -> dict:
    """
    Calculate performance metrics from portfolio history.
    """
    if isinstance(history, list):
        if not history:
            return {}
        df = pd.DataFrame(history)
    else:
        df = history
        if df.empty:
            return {}
    df.set_index('timestamp', inplace=True)
    
    # 1. Total Return
    initial_value = df['total_value'].iloc[0]
    final_value = df['total_value'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value
    
    # 2. Daily Returns
    df['daily_return'] = df['total_value'].pct_change().fillna(0)
    
    # 3. CAGR (Compound Annual Growth Rate)
    # Assuming daily data
    days = (df.index[-1] - df.index[0]).days
    if days > 0:
        cagr = (final_value / initial_value) ** (365 / days) - 1
    else:
        cagr = 0.0

    # 4. Sharpe Ratio (Annualized)
    # Assuming Risk Free Rate = 0 for now
    mean_daily_return = df['daily_return'].mean()
    std_daily_return = df['daily_return'].std()
    
    if std_daily_return != 0:
        sharpe_ratio = (mean_daily_return / std_daily_return) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0
        
    # 5. Max Drawdown
    df['cum_max'] = df['total_value'].cummax()
    df['drawdown'] = (df['total_value'] - df['cum_max']) / df['cum_max']
    max_drawdown = df['drawdown'].min()
    
    return {
        'Initial Value': initial_value,
        'Final Value': final_value,
        'Total Return': total_return,
        'CAGR': cagr,
        'Sharpe Ratio': sharpe_ratio,
        'Max Drawdown': max_drawdown
    }
