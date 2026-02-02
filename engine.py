"""
Backtest engine for executing trades and calculating performance metrics
"""

import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital=3.0):
        """
        Initialize backtest engine
        
        Args:
            initial_capital: Starting capital in USD
        """
        self.initial_capital = initial_capital
        
    def execute_trades(self, df, signals):
        """
        Execute trades based on signals and track outcomes
        
        Args:
            df: Price dataframe
            signals: List of signal dictionaries from strategy
            
        Returns:
            DataFrame with trade results
        """
        trades = []
        
        for signal in signals:
            entry_idx = signal['entry_index']
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            tp1 = signal['tp1']
            tp2 = signal['tp2']
            direction = signal['direction']
            
            # Look forward to find exit
            exit_price = None
            exit_reason = None
            bars_in_trade = 0
            max_bars = 60  # Max 5 hours (60 * 5min bars)
            
            for i in range(entry_idx + 1, min(entry_idx + max_bars, len(df))):
                bar = df.iloc[i]
                bars_in_trade += 1
                
                if direction == 'LONG':
                    # Check stop loss first
                    if bar['low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'STOP_LOSS'
                        break
                    # Check TP2
                    elif bar['high'] >= tp2:
                        exit_price = tp2
                        exit_reason = 'TP2'
                        break
                    # Check TP1
                    elif bar['high'] >= tp1:
                        exit_price = tp1
                        exit_reason = 'TP1'
                        break
                
                elif direction == 'SHORT':
                    # Check stop loss first
                    if bar['high'] >= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'STOP_LOSS'
                        break
                    # Check TP2
                    elif bar['low'] <= tp2:
                        exit_price = tp2
                        exit_reason = 'TP2'
                        break
                    # Check TP1
                    elif bar['low'] <= tp1:
                        exit_price = tp1
                        exit_reason = 'TP1'
                        break
            
            # If no exit found, close at time stop
            if exit_price is None:
                exit_price = df.iloc[min(entry_idx + max_bars - 1, len(df) - 1)]['close']
                exit_reason = 'TIME_STOP'
            
            # Calculate P&L in pips
            if direction == 'LONG':
                pips = (exit_price - entry_price) / 0.0001
            else:
                pips = (entry_price - exit_price) / 0.0001
            
            win = pips > 0
            
            trades.append({
                'entry_time': signal['timestamp'],
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'pips': pips,
                'win': win,
                'bars_in_trade': bars_in_trade,
                'level_type': signal['level_type']
            })
        
        return pd.DataFrame(trades)
    
    def calculate_metrics(self, trades_df):
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades_df: DataFrame of executed trades
            
        Returns:
            Dictionary of performance metrics
        """
        if len(trades_df) == 0:
            return {
                'total_trades': 0,
                'winners': 0,
                'losers': 0,
                'win_rate': 0,
                'total_pips': 0,
                'avg_pips': 0,
                'avg_win_pips': 0,
                'avg_loss_pips': 0,
                'profit_factor': 0,
                'avg_bars_in_trade': 0
            }
        
        total_trades = len(trades_df)
        winners = trades_df[trades_df['win'] == True]
        losers = trades_df[trades_df['win'] == False]
        
        win_rate = (len(winners) / total_trades) * 100 if total_trades > 0 else 0
        total_pips = trades_df['pips'].sum()
        avg_pips = trades_df['pips'].mean()
        
        # Profit factor
        gross_profit = winners['pips'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['pips'].sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': round(win_rate, 2),
            'total_pips': round(total_pips, 2),
            'avg_pips': round(avg_pips, 2),
            'avg_win_pips': round(winners['pips'].mean(), 2) if len(winners) > 0 else 0,
            'avg_loss_pips': round(losers['pips'].mean(), 2) if len(losers) > 0 else 0,
            'profit_factor': round(profit_factor, 2),
            'avg_bars_in_trade': round(trades_df['bars_in_trade'].mean(), 1) if len(trades_df) > 0 else 0
        }
