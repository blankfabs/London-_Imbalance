"""
London Open Imbalance Strategy

Entry requirements (ALL 5 must be met):
1. Location: Price at round number (00/50) or previous day high/low
2. Volume: Current bar volume > 1.5x average volume
3. Rejection: Previous candle has 8+ pip wick at level
4. Confirmation: Current candle closes away from level with 5+ pip body
5. EMA Alignment: 20 EMA sloping in trade direction and price on correct side
"""

import pandas as pd
import numpy as np

class LondonImbalanceStrategy:
    def __init__(self, 
                 volume_multiplier=1.5,
                 min_wick_pips=8,
                 min_body_pips=5,
                 ema_length=20,
                 stop_loss_pips=15,
                 tp1_pips=20,
                 tp2_pips=30):
        """
        Initialize strategy parameters
        
        Args:
            volume_multiplier: Volume must be this times the average
            min_wick_pips: Minimum rejection wick size in pips
            min_body_pips: Minimum confirmation candle body in pips
            ema_length: Period for EMA calculation
            stop_loss_pips: Stop loss distance in pips
            tp1_pips: First take profit target in pips
            tp2_pips: Second take profit target in pips
        """
        self.volume_multiplier = volume_multiplier
        self.min_wick_pips = min_wick_pips
        self.min_body_pips = min_body_pips
        self.ema_length = ema_length
        self.stop_loss_pips = stop_loss_pips
        self.tp1_pips = tp1_pips
        self.tp2_pips = tp2_pips
        self.pip_value = 0.0001  # EURUSD pip size
        
    def pips_to_price(self, pips):
        """Convert pips to price"""
        return pips * self.pip_value
    
    def price_to_pips(self, price):
        """Convert price to pips"""
        return price / self.pip_value
    
    def is_london_session(self, timestamp):
        """
        Check if timestamp is during London session (3am-6am EST)
        In UTC: 8am-11am
        """
        hour = timestamp.hour
        return 8 <= hour < 11
    
    def is_near_round_number(self, price, tolerance_pips=5):
        """
        Check if price is near round number (00 or 50 level)
        
        Args:
            price: Current price
            tolerance_pips: How close to level counts as "near"
        """
        price_in_pips = int(price / self.pip_value)
        last_two_digits = price_in_pips % 100
        
        # Check 00 level
        if abs(last_two_digits) <= tolerance_pips or abs(last_two_digits - 100) <= tolerance_pips:
            return True
        
        # Check 50 level
        if abs(last_two_digits - 50) <= tolerance_pips:
            return True
        
        return False
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators needed for strategy"""
        df = df.copy()
        
        # EMA
        df['ema_20'] = df['close'].ewm(span=self.ema_length, adjust=False).mean()
        df['ema_slope'] = df['ema_20'].diff()
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_spike'] = df['volume'] > (df['volume_ma'] * self.volume_multiplier)
        
        # Candle analysis
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        
        df['body_pips'] = self.price_to_pips(df['body'])
        df['upper_wick_pips'] = self.price_to_pips(df['upper_wick'])
        df['lower_wick_pips'] = self.price_to_pips(df['lower_wick'])
        
        # Previous day high/low (288 5-min bars = 1 day)
        df['prev_day_high'] = df['high'].shift(1).rolling(window=288, min_periods=1).max()
        df['prev_day_low'] = df['low'].shift(1).rolling(window=288, min_periods=1).min()
        
        return df
    
    def detect_signals(self, df):
        """
        Detect entry signals based on all 5 strategy conditions
        
        Returns:
            List of signal dictionaries with entry details
        """
        df = self.calculate_indicators(df)
        signals = []
        
        # Need warmup period for indicators
        for i in range(100, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Skip if not London session
            if not self.is_london_session(row.name):
                continue
            
            # ===== CONDITION 1: LOCATION =====
            at_round_number = self.is_near_round_number(row['close'])
            at_prev_day_high = abs(row['close'] - row['prev_day_high']) < self.pips_to_price(5)
            at_prev_day_low = abs(row['close'] - row['prev_day_low']) < self.pips_to_price(5)
            
            at_key_level = at_round_number or at_prev_day_high or at_prev_day_low
            
            if not at_key_level:
                continue
            
            # ===== CONDITION 2: VOLUME SPIKE =====
            if not prev_row['volume_spike']:
                continue
            
            # ===== CONDITION 3: REJECTION PATTERN =====
            bullish_rejection = prev_row['lower_wick_pips'] >= self.min_wick_pips
            bearish_rejection = prev_row['upper_wick_pips'] >= self.min_wick_pips
            
            # ===== CONDITION 4: CONFIRMATION CANDLE =====
            strong_body = row['body_pips'] >= self.min_body_pips
            bullish_confirm = row['close'] > row['open'] and row['close'] > prev_row['high']
            bearish_confirm = row['close'] < row['open'] and row['close'] < prev_row['low']
            
            # ===== CONDITION 5: EMA ALIGNMENT =====
            ema_bullish = row['ema_slope'] > 0 and row['close'] > row['ema_20']
            ema_bearish = row['ema_slope'] < 0 and row['close'] < row['ema_20']
            
            # ===== LONG SIGNAL =====
            if (bullish_rejection and bullish_confirm and strong_body and ema_bullish):
                signals.append({
                    'timestamp': row.name,
                    'direction': 'LONG',
                    'entry_price': row['close'],
                    'stop_loss': row['close'] - self.pips_to_price(self.stop_loss_pips),
                    'tp1': row['close'] + self.pips_to_price(self.tp1_pips),
                    'tp2': row['close'] + self.pips_to_price(self.tp2_pips),
                    'level_type': 'Round' if at_round_number else 'Prev Day',
                    'entry_index': i
                })
            
            # ===== SHORT SIGNAL =====
            elif (bearish_rejection and bearish_confirm and strong_body and ema_bearish):
                signals.append({
                    'timestamp': row.name,
                    'direction': 'SHORT',
                    'entry_price': row['close'],
                    'stop_loss': row['close'] + self.pips_to_price(self.stop_loss_pips),
                    'tp1': row['close'] - self.pips_to_price(self.tp1_pips),
                    'tp2': row['close'] - self.pips_to_price(self.tp2_pips),
                    'level_type': 'Round' if at_round_number else 'Prev Day',
                    'entry_index': i
                })
        
        return signals
