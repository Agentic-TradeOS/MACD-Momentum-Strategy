"""
MACD Momentum Strategy
Trend-following strategy using Moving Average Convergence Divergence.

Entry: Buy when MACD line crosses above signal line (bullish crossover)
Exit: Sell when MACD line crosses below signal line (bearish crossover)

Author: Agentic Trading
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    duration_days: int = 0
    exit_reason: str = ""


class MACDMomentumStrategy:
    """
    MACD Momentum Strategy

    Uses the MACD indicator (difference between fast and slow EMAs) and its
    signal line (EMA of MACD) to identify momentum shifts.

    Parameters:
    -----------
    fast_period : int
        Fast EMA period (default: 12)
    slow_period : int
        Slow EMA period (default: 26)
    signal_period : int
        Signal line EMA period (default: 9)
    stop_loss_pct : float
        Stop loss percentage (default: 0.06)
    take_profit_pct : float
        Take profit percentage (default: 0.20)
    position_size_pct : float
        Position size as percentage of equity (default: 0.20)
    min_histogram : float
        Minimum histogram value required for a bullish entry signal (default: 0.0)

    Example:
    --------
    >>> strategy = MACDMomentumStrategy(fast_period=12, slow_period=26, signal_period=9)
    >>> results = strategy.backtest(df, initial_capital=100_000)
    >>> print(f"Total Return: {results['total_return']:.2%}")
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        stop_loss_pct: float = 0.06,
        take_profit_pct: float = 0.20,
        position_size_pct: float = 0.20,
        min_histogram: float = 0.0,
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct
        self.min_histogram = min_histogram

    def calculate_macd(self, close: pd.Series):
        fast_ema = close.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = close.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['macd'], df['signal_line'], df['histogram'] = self.calculate_macd(df['close'])

        macd_prev = df['macd'].shift(1)
        signal_prev = df['signal_line'].shift(1)

        bullish_cross = (macd_prev < signal_prev) & (df['macd'] > df['signal_line'])
        bearish_cross = (macd_prev > signal_prev) & (df['macd'] < df['signal_line'])

        df['signal'] = 0
        df.loc[bullish_cross & (df['histogram'] > self.min_histogram), 'signal'] = 1
        df.loc[bearish_cross, 'signal'] = -1

        return df

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.001,
    ) -> Dict:
        df = self.generate_signals(data)
        capital = initial_capital
        equity_curve = []
        trades = []
        position = None

        for timestamp, row in df.iterrows():
            if pd.isna(row['macd']):
                equity_curve.append({'date': timestamp, 'equity': capital, 'drawdown': 0})
                continue

            if row['signal'] == 1 and position is None:
                pos_value = capital * self.position_size_pct
                entry_price = row['close'] * (1 + slippage)
                shares = pos_value / entry_price
                capital -= pos_value * commission
                position = {
                    'entry_date': timestamp,
                    'entry_price': entry_price,
                    'shares': shares,
                    'stop_loss': entry_price * (1 - self.stop_loss_pct),
                    'take_profit': entry_price * (1 + self.take_profit_pct),
                }

            elif position is not None:
                price = row['close']
                exit_reason = None
                exit_price = price

                if price <= position['stop_loss']:
                    exit_reason, exit_price = 'stop_loss', position['stop_loss']
                elif price >= position['take_profit']:
                    exit_reason, exit_price = 'take_profit', position['take_profit']
                elif row['signal'] == -1:
                    exit_reason = 'bearish_cross'
                    exit_price = price * (1 - slippage)

                if exit_reason:
                    gross_pnl = position['shares'] * (exit_price - position['entry_price'])
                    net_pnl = gross_pnl - (position['shares'] * exit_price * commission)
                    trades.append(Trade(
                        entry_date=position['entry_date'],
                        exit_date=timestamp,
                        symbol='UNKNOWN',
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        quantity=position['shares'],
                        pnl=net_pnl,
                        pnl_pct=(exit_price - position['entry_price']) / position['entry_price'],
                        duration_days=(timestamp - position['entry_date']).days,
                        exit_reason=exit_reason,
                    ))
                    capital += net_pnl
                    position = None

            current_equity = capital + (position['shares'] * row['close'] if position else 0)
            peak = max((e['equity'] for e in equity_curve), default=current_equity)
            drawdown = (peak - current_equity) / peak if peak > 0 else 0
            equity_curve.append({'date': timestamp, 'equity': current_equity, 'drawdown': drawdown})

        equity_df = pd.DataFrame(equity_curve)
        total_return = (equity_df['equity'].iloc[-1] - initial_capital) / initial_capital
        daily_returns = equity_df['equity'].pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
        winners = [t for t in trades if t.pnl > 0]

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': equity_df['drawdown'].max(),
            'win_rate': len(winners) / len(trades) if trades else 0,
            'total_trades': len(trades),
            'equity_curve': equity_curve,
            'trades': trades,
        }


if __name__ == "__main__":
    print("MACD Momentum Strategy")
    print("Entry: MACD line crosses above signal line")
    print("Exit:  MACD line crosses below signal line or stop/take-profit hit")
