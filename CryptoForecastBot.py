import asyncio
import logging
import json
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import telegram
import websockets
import requests
from datetime import datetime, timezone
import talib
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from rich.console import Console
from rich.logging import RichHandler

# Настройка логирования с ротацией и красивым выводом в терминал
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('crypto_forecast_bot.log', maxBytes=10*1024*1024, backupCount=5),
        RichHandler(console=console, show_time=False, show_path=False)
    ]
)
logger = logging.getLogger('__name__')

# Конфигурация стратегии
CONFIG = {
    'BINANCE_API_KEY': '',
    'BINANCE_API_SECRET': '',
    'NEWS_API_KEY': '',
    'TELEGRAM_BOT_TOKEN': '',
    'TELEGRAM_CHAT_ID': '',
    'TRADING_PAIRS': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'CFX/USDT', 'JTO/USDT', 'GMX/USDT', 'FET/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'TRX/USDT', 'DOT/USDT', 'LINK/USDT', 'TON/USDT', 'SHIB/USDT', 'LTC/USDT', 'BCH/USDT', 'NEAR/USDT', 'APT/USDT', 'HBAR/USDT', 'PEPE/USDT', 'FIL/USDT', 'SUI/USDT', 'ARB/USDT', 'OP/USDT', 'ICP/USDT', 'VET/USDT', 'ALGO/USDT', 'INJ/USDT', 'GALA/USDT', 'THETA/USDT', 'FLOW/USDT', 'XLM/USDT', 'ZIL/USDT', 'SAND/USDT', 'MANA/USDT', 'CHZ/USDT'],  # Список пар для анализа, например ['BTC/USDT', 'ETH/USDT'], если пуст использует 'MAX_SYMBOLS'
    'TIMEFRAMES': ['5m', '15m', '30m', '1h', '2h', '4h', '8h', '1d'],  # Таймфреймы для анализа
    'UPDATE_INTERVAL': 60,  # Интервал обновления анализа (сек)
    'RSI_PERIOD': 14,  # Базовый период RSI
    'EMA_FAST': 12,  # Быстрая EMA
    'EMA_SLOW': 26,  # Медленная EMA
    'MACD_SIGNAL': 9,  # Период сигнальной линии MACD
    'BB_PERIOD': 20,  # Период Bollinger Bands
    'STOCH_K': 14,  # Период %K для Stochastic
    'STOCH_D': 3,  # Период %D для Stochastic
    'MIN_LIQUIDITY': 5000,  # Минимальная ликвидность (глубина стакана)
    'SPREAD_THRESHOLD': 0.005,  # Максимальный Bid/Ask спред (0.2%)
    'VOLATILITY_THRESHOLD': 0.015,  # Порог волатильности для адаптации 0.015
    'LOW_LIQUIDITY_HOURS': [(0, 4)],  # Часы низкой ликвидности (UTC)
    'MAX_SYMBOLS': 50,  # Максимум пар для анализа
    'RSI_ADAPT_RANGE': (10, 18),  # Диапазон адаптации RSI
    'EMA_ADAPT_RANGE': (8, 30),  # Диапазон адаптации EMA
    'INITIAL_WEBSOCKET_WAIT': 10,  # Ожидание WebSocket (сек)
    'SENTIMENT_CACHE_DURATION': 300,  # Кэш настроений (5 мин)
    'NEWS_CYCLE_CACHE_DURATION': 3600,  # Кэш новостей на 60 минут
    'SUPPORT_RESISTANCE_WINDOW': 100,  # Окно для уровней поддержки/сопротивления
    'MIN_RR_RATIO': 1.5,  # Минимальное соотношение риск/прибыль
    'SIGNAL_COOLDOWN': 300,  # Минимальный интервал между сигналами (5 мин)
    'MIN_STOP_SIZE': 0.005,  # Минимальный размер стопа
    'MIN_TAKE_SIZE': 0.01,  # Минимальный размер тейка
    'MAX_TAKE_RANGE': 8.0,  # Макс 8*ATR для тейк-профита
    'MIN_SIGNAL_INTERVAL': 1800,  # Минимальный интервал между сигналами для одной монеты (30 мин)
    'ADX_THRESHOLD': 15,  # Порог для определения флэта
    'MIN_PRICE': 0.000001,  # Минимальная цена для пар
    'MIN_ABS_STOP_SIZE': 0.0001,  # Минимальный абсолютный размер стопа
    'MIN_ABS_TAKE_SIZE': 0.0001,  # Минимальный абсолютный размер тейка
    'VOLUME_THRESHOLD': 0.2,  # Порог объёма (в разах от медианы)
    'INDICATOR_CONFIG': {
        '5m': {'rsi_range': (6, 10), 'ema_fast_range': (4, 8), 'ema_slow_range': (10, 18), 'stoch_k': 8, 'stoch_d': 3, 'bb_period': 12},  # NEW
        '15m': {'rsi_range': (8, 12), 'ema_fast_range': (6, 10), 'ema_slow_range': (12, 20), 'stoch_k': 10, 'stoch_d': 3, 'bb_period': 15},
        '30m': {'rsi_range': (10, 14), 'ema_fast_range': (8, 12), 'ema_slow_range': (16, 24), 'stoch_k': 12, 'stoch_d': 3, 'bb_period': 18},
        '1h': {'rsi_range': (12, 16), 'ema_fast_range': (10, 14), 'ema_slow_range': (20, 28), 'stoch_k': 14, 'stoch_d': 3, 'bb_period': 20},
        '2h': {'rsi_range': (14, 18), 'ema_fast_range': (12, 16), 'ema_slow_range': (24, 32), 'stoch_k': 16, 'stoch_d': 4, 'bb_period': 22},
        '4h': {'rsi_range': (16, 20), 'ema_fast_range': (14, 18), 'ema_slow_range': (28, 36), 'stoch_k': 18, 'stoch_d': 4, 'bb_period': 24},
        '8h': {'rsi_range': (18, 22), 'ema_fast_range': (16, 20), 'ema_slow_range': (32, 40), 'stoch_k': 20, 'stoch_d': 5, 'bb_period': 26},
        '1d': {'rsi_range': (20, 24), 'ema_fast_range': (18, 22), 'ema_slow_range': (36, 44), 'stoch_k': 22, 'stoch_d': 5, 'bb_period': 28},
    },
    'MARKET_ADJUSTMENTS': {  # Корректировки для рыночных условий
        'bullish': {'rsi_overbought': 75, 'rsi_oversold': 35, 'tp_multiplier': 8.0, 'sl_multiplier': 0.8},
        'bearish': {'rsi_overbought': 65, 'rsi_oversold': 25, 'tp_multiplier': 8.0, 'sl_multiplier': 0.8},
        'flat': {'rsi_overbought': 65, 'rsi_oversold': 35, 'tp_multiplier': 3.0, 'sl_multiplier': 1.2},
    },
}

class CryptoForecastBot:
    def __init__(self):
        logger.info("Инициализация CryptoForecastBot...")
        self.exchange = ccxt.binance({
            'apiKey': CONFIG['BINANCE_API_KEY'],
            'secret': CONFIG['BINANCE_API_SECRET'],
            'enableRateLimit': True,
            'options': {'defaultType': 'spot', 'adjustForTimeDifference': True}
        })
        self.bot = telegram.Bot(token=CONFIG['TELEGRAM_BOT_TOKEN'])
        self.symbols = []
        self.timeframes = CONFIG['TIMEFRAMES']
        self.websocket_url = 'wss://stream.binance.com:9443/ws'
        self.data = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.sentiment_cache = {}
        self.sentiment_cache_time = {}
        self.news_cycle_cache = {}
        self.last_signal_time = {}
        self.signal_log = []  
        logger.info("Бот успешно инициализирован")

    async def validate_api_key(self):
        try:
            balance = await self.exchange.fetch_balance()
            logger.info(f"API-ключ валиден, баланс: {balance.get('USDT', {})}")
        except Exception as e:
            logger.error(f"Ошибка проверки API-ключа: {e}")
            raise Exception("Невалидный API-ключ")

    async def run(self):
        try:
            logger.info("Запуск основного цикла бота...")
            await self.validate_api_key()
            await self.load_symbols()
            if not self.symbols:
                logger.error("Символы не загружены, завершение...")
                return
            asyncio.create_task(self.websocket_listener())
            await asyncio.sleep(CONFIG['INITIAL_WEBSOCKET_WAIT'])
            while True:
                seen_signals = set()
                tasks = [self.analyze_pair(symbol, tf) for symbol in self.symbols for tf in self.timeframes]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, dict) and result:
                        signal_key = f"{result['symbol']}_{result['timeframe']}"
                        if signal_key not in seen_signals:
                            seen_signals.add(signal_key)
                            await self.send_forecast(result)
                            self.signal_log.append(result)
                            with open('signals.json', 'w') as f:
                                json.dump(self.signal_log, f, indent=2)
                            logger.info(f"Сигнал отправлен для {result['symbol']} на {result['timeframe']}")
                logger.info("Цикл анализа завершен")
                await asyncio.sleep(CONFIG['UPDATE_INTERVAL'])
        except Exception as e:
            logger.error(f"Ошибка основного цикла: {e}")
            await asyncio.sleep(5)
            await self.run()

    async def load_symbols(self):
        try:
            logger.info("Загрузка торговых пар...")
            await self.exchange.load_markets()
            markets = self.exchange.markets
            self.symbols = []
            if CONFIG['TRADING_PAIRS']:
                for symbol in CONFIG['TRADING_PAIRS']:
                    symbol = symbol.upper()
                    if (symbol in markets and 
                        markets[symbol]['active'] and 
                        markets[symbol]['type'] == 'spot' and 
                        markets[symbol].get('quote') == 'USDT'):
                        self.symbols.append(symbol)
                    else:
                        logger.warning(f"Пара {symbol} недоступна или неактивна, пропущена")
                if not self.symbols:
                    logger.warning("Указанные пары недоступны, переход к дефолтным")
                    self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            else:
                self.symbols = [
                    symbol for symbol in markets
                    if markets[symbol]['active'] and
                    markets[symbol]['type'] == 'spot' and
                    markets[symbol].get('quote') == 'USDT' and
                    markets[symbol].get('base') not in ['USDT', 'TUSD', 'USDC', 'BUSD']
                ][:CONFIG['MAX_SYMBOLS']]
                if not self.symbols:
                    logger.warning("Торговые пары не найдены, переход к дефолтным")
                    self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            logger.info(f"Загружено {len(self.symbols)} торговых пар: {self.symbols}")
            self.data = {
                symbol: {tf: pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        for tf in self.timeframes}
                for symbol in self.symbols
            }
        except Exception as e:
            logger.error(f"Ошибка загрузки пар: {e}")
            self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            self.data = {
                symbol: {tf: pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        for tf in self.timeframes}
                for symbol in self.symbols
            }

    async def fetch_ohlcv(self, symbol, timeframe, limit=200):
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            if df['close'].le(CONFIG['MIN_PRICE']).any():
                logger.warning(f"Пропуск {symbol}: цена ниже {CONFIG['MIN_PRICE']}")
                return pd.DataFrame()
            logger.debug(f"Получено {len(df)} записей OHLCV для {symbol} на {timeframe}")
            return df
        except Exception as e:
            logger.error(f"Ошибка получения OHLCV для {symbol} на {timeframe}: {e}")
            return pd.DataFrame()

    async def fetch_order_book(self, symbol):
        try:
            order_book = await self.exchange.fetch_order_book(symbol, limit=5)
            bids = order_book['bids']
            asks = order_book['asks']
            bid_price = bids[0][0] if bids else 0
            ask_price = asks[0][0] if asks else 0
            if bid_price <= 0 or ask_price <= 0 or bid_price >= ask_price:
                logger.warning(f"Некорректный стакан для {symbol}: bid={bid_price}, ask={ask_price}")
                return 0, float('inf')
            spread = (ask_price - bid_price) / bid_price
            liquidity = sum(bid[1] * bid[0] for bid in bids) + sum(ask[1] * ask[0] for ask in asks)
            logger.debug(f"Ликвидность для {symbol}: {liquidity:.4f}, спред: {spread:.4f}")
            return liquidity, spread
        except Exception as e:
            logger.error(f"Ошибка получения стакана для {symbol}: {e}")
            return 0, float('inf')

    async def fetch_news(self, symbol):
        try:
            now = datetime.now(timezone.utc).timestamp()
            coin = symbol.split('/')[0]
            if coin in ['USDT', 'TUSD', 'USDC', 'BUSD']:
                logger.info(f"Пропуск новостей для стейблкоина {symbol}")
                return 0
            if coin in self.news_cycle_cache and now - self.sentiment_cache_time.get(coin, 0) < CONFIG['NEWS_CYCLE_CACHE_DURATION']:
                logger.debug(f"Использую цикл-кэш для {coin}: {self.news_cycle_cache[coin]}")
                return self.news_cycle_cache[coin]
            if coin in self.sentiment_cache and now - self.sentiment_cache_time[coin] < CONFIG['SENTIMENT_CACHE_DURATION']:
                logger.debug(f"Использую кэш настроений для {coin}: {self.sentiment_cache[coin]}")
                return self.sentiment_cache[coin]
            url = f"https://newsapi.org/v2/everything?q={coin}&apiKey={CONFIG['NEWS_API_KEY']}"
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor, lambda: requests.get(url, timeout=10)
            )
            response_json = response.json()
            articles = response_json.get('articles', [])
            if not articles:
                logger.info(f"Нет новостей для {symbol}")
                return 0
            sentiment_score = sum(
                1 if article.get('title') and ('bullish' in article['title'].lower() or 'rise' in article['title'].lower()) else
                -1 if article.get('title') and ('bearish' in article['title'].lower() or 'drop' in article['title'].lower()) else 0
                for article in articles[:10]
            )
            self.sentiment_cache[coin] = sentiment_score
            self.sentiment_cache_time[coin] = now
            self.news_cycle_cache[coin] = sentiment_score
            logger.info(f"Оценка настроений для {symbol}: {sentiment_score}")
            return sentiment_score
        except Exception as e:
            logger.error(f"Ошибка получения новостей для {symbol}: {e}")
            return 0

    def adapt_indicators_dynamic(self, df, timeframe):
        try:
            adx = df['adx'].iloc[-1] if 'adx' in df else 0
            is_trending = adx > CONFIG['ADX_THRESHOLD']
            ema_fast = df['ema_fast'].iloc[-1] if 'ema_fast' in df else 0
            ema_slow = df['ema_slow'].iloc[-1] if 'ema_slow' in df else 0
            market_state = 'bullish' if ema_fast > ema_slow else 'bearish' if ema_fast < ema_slow else 'flat'
            if not is_trending:
                market_state = 'flat'
            tf_config = CONFIG['INDICATOR_CONFIG'].get(timeframe, CONFIG['INDICATOR_CONFIG']['1h'])
            volatility = df['close'].pct_change().std() if not df.empty else 0
            rsi_period = tf_config['rsi_range'][0] if volatility > CONFIG['VOLATILITY_THRESHOLD'] else tf_config['rsi_range'][1]
            ema_fast_period = tf_config['ema_fast_range'][0] if volatility > CONFIG['VOLATILITY_THRESHOLD'] else tf_config['ema_fast_range'][1]
            ema_slow_period = tf_config['ema_slow_range'][0] if volatility > CONFIG['VOLATILITY_THRESHOLD'] else tf_config['ema_slow_range'][1]
            stoch_k = tf_config['stoch_k']
            stoch_d = tf_config['stoch_d']
            bb_period = tf_config['bb_period']
            macd_signal = CONFIG['MACD_SIGNAL'] + 2 if timeframe in ['5m', '15m', '30m'] else CONFIG['MACD_SIGNAL'] 
            logger.debug(f"Адаптированные параметры для {timeframe}: RSI={rsi_period}, EMA_fast={ema_fast_period}, EMA_slow={ema_slow_period}, Stoch_K={stoch_k}, Stoch_D={stoch_d}, BB={bb_period}, MACD_signal={macd_signal}, Market={market_state}")
            return {
                'rsi_period': rsi_period,
                'ema_fast': ema_fast_period,
                'ema_slow': ema_slow_period,
                'macd_signal': macd_signal,
                'stoch_k': stoch_k,
                'stoch_d': stoch_d,
                'bb_period': bb_period,
                'market_state': market_state
            }
        except Exception as e:
            logger.error(f"Ошибка адаптации индикаторов: {e}")
            return {
                'rsi_period': CONFIG['RSI_PERIOD'],
                'ema_fast': CONFIG['EMA_FAST'],
                'ema_slow': CONFIG['EMA_SLOW'],
                'macd_signal': CONFIG['MACD_SIGNAL'],
                'stoch_k': CONFIG['STOCH_K'],
                'stoch_d': CONFIG['STOCH_D'],
                'bb_period': CONFIG['BB_PERIOD'],
                'market_state': 'flat'
            }

    def calculate_indicators(self, df, params):
        try:
            if len(df) < max(params['rsi_period'], params['ema_slow'], params['bb_period']):
                logger.debug(f"Недостаточно данных для индикаторов: {len(df)} записей")
                return df
            df['rsi'] = talib.RSI(df['close'], timeperiod=params['rsi_period'])
            df['ema_fast'] = talib.EMA(df['close'], timeperiod=params['ema_fast'])
            df['ema_slow'] = talib.EMA(df['close'], timeperiod=params['ema_slow'])
            macd, signal, _ = talib.MACD(
                df['close'], fastperiod=params['ema_fast'], slowperiod=params['ema_slow'], signalperiod=params['macd_signal']
            )
            df['macd'] = macd
            df['macd_signal'] = signal
            df['upper_bb'], df['middle_bb'], df['lower_bb'] = talib.BBANDS(df['close'], timeperiod=params['bb_period'])
            df['stoch_k'], df['stoch_d'] = talib.STOCH(
                df['high'], df['low'], df['close'], fastk_period=params['stoch_k'], slowk_period=params['stoch_d']
            )
            df['obv'] = talib.OBV(df['close'], df['volume'])
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            return df
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return df

    def detect_candle_patterns(self, df):
        try:
            df['bullish_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']) > 0
            df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close']) > 0
            df['pin_bar'] = np.logical_and(
                (df['high'] - df['low']) > 2 * abs(df['open'] - df['close']),
                df['close'] > df['open']
            )
            df['candle_confirmed'] = df['bullish_engulfing'].shift(1) | df['hammer'].shift(1) | df['pin_bar'].shift(1)
            return df
        except Exception as e:
            logger.error(f"Ошибка определения свечных паттернов: {e}")
            return df

    def analyze_market_structure(self, df):
        try:
            df['support'] = df['low'].rolling(window=CONFIG['SUPPORT_RESISTANCE_WINDOW']).min()
            df['resistance'] = df['high'].rolling(window=CONFIG['SUPPORT_RESISTANCE_WINDOW']).max()
            df['trend'] = np.where(df['ema_fast'] > df['ema_slow'], 'bullish', 'bearish')
            return df
        except Exception as e:
            logger.error(f"Ошибка анализа рыночной структуры: {e}")
            return df

    def detect_rsi_divergence(self, df):
        try:
            rsi = df['rsi'].iloc[-5:]
            price = df['close'].iloc[-5:]
            bullish_div = (rsi.iloc[-1] > rsi.iloc[-2]) and (price.iloc[-1] < price.iloc[-2]) and (rsi.iloc[-1] < 50)
            bearish_div = (rsi.iloc[-1] < rsi.iloc[-2]) and (price.iloc[-1] > price.iloc[-2]) and (rsi.iloc[-1] > 50)
            return bullish_div, bearish_div
        except Exception as e:
            logger.error(f"Ошибка обнаружения дивергенции RSI: {e}")
            return False, False

    def is_low_liquidity_time(self):
        try:
            now = datetime.now(timezone.utc)
            hour = now.hour
            for start, end in CONFIG['LOW_LIQUIDITY_HOURS']:
                if start <= hour < end:
                    logger.info(f"Низкая ликвидность: {hour}:00 UTC")
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки времени ликвидности: {e}")
            return False

    async def confirm_trend_on_higher_tf(self, symbol, timeframe):
        try:
            tf_index = self.timeframes.index(timeframe)
            if tf_index + 1 >= len(self.timeframes):
                return True
            higher_tf = self.timeframes[tf_index + 1]
            df = await self.fetch_ohlcv(symbol, higher_tf, limit=50)
            if df.empty or len(df) < 50:
                logger.info(f"Пропуск {symbol} на {higher_tf}: недостаточно данных")
                return False
            params = self.adapt_indicators_dynamic(df, higher_tf)
            df = self.calculate_indicators(df, params)
            df = self.analyze_market_structure(df)
            latest = df.iloc[-1]
            is_bullish = latest['ema_fast'] > latest['ema_slow']
            logger.debug(f"Тренд на {higher_tf} для {symbol}: {'bullish' if is_bullish else 'bearish'}")
            return is_bullish
        except Exception as e:
            logger.error(f"Ошибка проверки тренда на старшем таймфрейме: {e}")
            return False

    async def analyze_pair(self, symbol, timeframe):
        try:
            logger.info(f"Анализ пары {symbol} на {timeframe}")
            if self.is_low_liquidity_time():
                logger.info(f"Пропуск {symbol}: низкая ликвидность")
                return None
            coin = symbol.split('/')[0]
            now = datetime.now(timezone.utc).timestamp()
            for tf in self.timeframes:
                signal_key = f"{symbol}_{tf}"
                if signal_key in self.last_signal_time and now - self.last_signal_time[signal_key] < CONFIG['MIN_SIGNAL_INTERVAL']:
                    logger.info(f"Пропуск {symbol} на {timeframe}: сигнал для {coin} слишком частый")
                    return None
            signal_key = f"{symbol}_{timeframe}"
            if signal_key in self.last_signal_time and now - self.last_signal_time[signal_key] < CONFIG['SIGNAL_COOLDOWN']:
                logger.info(f"Пропуск {symbol} на {timeframe}: сигнал слишком частый")
                return None
            df = await self.fetch_ohlcv(symbol, timeframe)
            if df.empty or len(df) < 50:
                logger.info(f"Пропуск {symbol} на {timeframe}: недостаточно данных ({len(df)} записей)")
                return None
            liquidity, spread = await self.fetch_order_book(symbol)
            if liquidity < CONFIG['MIN_LIQUIDITY'] or spread > CONFIG['SPREAD_THRESHOLD']:
                logger.info(f"Пропуск {symbol}: ликвидность={liquidity:.4f}, спред={spread:.4f}")
                return None
            median_volume = df['volume'].rolling(window=20).median().iloc[-1]
            if df['volume'].iloc[-1] < CONFIG['VOLUME_THRESHOLD'] * median_volume:
                logger.info(f"Пропуск {symbol} на {timeframe}: низкий объём")
                return None
            volatility = df['close'].pct_change().std() if not df.empty else 0
            params = self.adapt_indicators_dynamic(df, timeframe)
            df = self.calculate_indicators(df, params)
            df = self.detect_candle_patterns(df)
            df = self.analyze_market_structure(df)
            sentiment = await self.fetch_news(symbol)
            latest = df.iloc[-1]
            obv_trend = latest['obv'] > df['obv'].shift(1).iloc[-1] if 'obv' in df else False
            candle_signal = latest.get('candle_confirmed', False)
            near_support = latest['close'] <= latest['support'] * 1.002 if 'support' in latest else False
            near_resistance = latest['close'] >= latest['resistance'] * 0.998 if 'resistance' in latest else False
            is_flat = latest.get('adx', 0) < CONFIG['ADX_THRESHOLD']
            bullish_div, bearish_div = self.detect_rsi_divergence(df)
            entry_price = latest.get('close', 0)
            atr = latest.get('atr', latest['high'] - latest['low'])
            last_low = df['low'].iloc[-1]
            last_high = df['high'].iloc[-1]
            support = latest.get('support', last_low)
            resistance = latest.get('resistance', last_high)
            market_state = params['market_state']
            market_adjust = CONFIG['MARKET_ADJUSTMENTS'][market_state]
            logger.debug(f"{symbol} {timeframe}: entry_price={entry_price:.4f}, atr={atr:.4f}, support={support:.4f}, resistance={resistance:.4f}, volatility={volatility:.4f}, adx={latest.get('adx', 0):.2f}, market={market_state}")
            signal = None
            if is_flat:
                if (latest['close'] > resistance and
                    latest['rsi'] < market_adjust['rsi_overbought'] and
                    latest['macd'] > latest['macd_signal'] and
                    (candle_signal or near_support or bullish_div) and
                    sentiment >= -3):
                    signal = 'buy'
                    logger.info(f"Флэтовый сигнал покупки для {symbol}: пробой сопротивления {resistance:.4f}")
                elif (latest['close'] < support and
                      latest['rsi'] > market_adjust['rsi_oversold'] and
                      latest['macd'] < latest['macd_signal'] and
                      (candle_signal or near_resistance or bearish_div) and
                      sentiment <= 3):
                    signal = 'sell'
                    logger.info(f"Флэтовый сигнал продажи для {symbol}: пробой поддержки {support:.4f}")
            else:
                if (latest['rsi'] < 60 and
                    latest['macd'] > latest['macd_signal'] and
                    obv_trend and
                    (candle_signal or near_support or bullish_div) and
                    sentiment >= -3 and
                    await self.confirm_trend_on_higher_tf(symbol, timeframe)):
                    signal = 'buy'
                elif (latest['rsi'] > 40 and
                      latest['macd'] < latest['macd_signal'] and
                      not obv_trend and
                      (candle_signal or near_resistance or bearish_div) and
                      sentiment <= 3 and
                      not await self.confirm_trend_on_higher_tf(symbol, timeframe)):
                    signal = 'sell'
            if not signal:
                logger.info(f"Нет сигнала для {symbol} на {timeframe}: rsi={latest.get('rsi', 50):.2f}, macd={latest.get('macd', 0):.4f}, macd_signal={latest.get('macd_signal', 0):.4f}, obv_trend={obv_trend}, sentiment={sentiment}, candle={candle_signal}, near_support={near_support}, near_resistance={near_resistance}, is_flat={is_flat}, bullish_div={bullish_div}, bearish_div={bearish_div}")
                return None
            tf_multiplier = 1.0 + (self.timeframes.index(timeframe) / len(self.timeframes)) * 0.5
            if signal == 'buy':
                stop_loss = min(support * 0.99, entry_price - market_adjust['sl_multiplier'] * atr * tf_multiplier)
                take_profit = max(resistance * 1.01, entry_price + market_adjust['tp_multiplier'] * atr * tf_multiplier)
                stop_loss = min(stop_loss, entry_price - max(CONFIG['MIN_STOP_SIZE'], CONFIG['MIN_ABS_STOP_SIZE']))
                take_profit = max(take_profit, entry_price + max(CONFIG['MIN_TAKE_SIZE'], CONFIG['MIN_ABS_TAKE_SIZE']))
                take_profit = min(take_profit, entry_price + CONFIG['MAX_TAKE_RANGE'] * atr)
            else:
                stop_loss = max(resistance * 1.01, entry_price + market_adjust['sl_multiplier'] * atr * tf_multiplier)
                take_profit = min(support * 0.99, entry_price - market_adjust['tp_multiplier'] * atr * tf_multiplier)
                stop_loss = max(stop_loss, entry_price + max(CONFIG['MIN_STOP_SIZE'], CONFIG['MIN_ABS_STOP_SIZE']))
                take_profit = min(take_profit, entry_price - max(CONFIG['MIN_TAKE_SIZE'], CONFIG['MIN_ABS_TAKE_SIZE']))
                take_profit = max(take_profit, entry_price - CONFIG['MAX_TAKE_RANGE'] * atr)
            logger.debug(f"Raw values for {symbol} {timeframe}: entry_price={entry_price:.8f}, stop_loss={stop_loss:.8f}, take_profit={take_profit:.8f}")
            if abs(entry_price - stop_loss) < CONFIG['MIN_ABS_STOP_SIZE']:
                logger.info(f"Пропуск {symbol} на {timeframe}: слишком узкий стоп")
                return None
            if abs(take_profit - entry_price) < CONFIG['MIN_ABS_TAKE_SIZE']:
                logger.info(f"Пропуск {symbol} на {timeframe}: слишком узкий тейк")
                return None
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            logger.info(
                f"{symbol} {timeframe}: Signal={signal}, RSI={latest.get('rsi', 50):.2f}, "
                f"MACD={latest.get('macd', 0):.4f}, MACD_signal={latest.get('macd_signal', 0):.4f}, "
                f"OBV_trend={obv_trend}, Sentiment={sentiment}, "
                f"Candle={candle_signal}, Near_support={near_support}, Near_resistance={near_resistance}, "
                f"ATR={atr:.4f}, Price={entry_price:.4f}, Stop_loss={stop_loss:.4f}, Take_profit={take_profit:.4f}, "
                f"RR={rr_ratio:.2f}, Support={support:.4f}, Resistance={resistance:.4f}, Market={market_state}"
            )
            if rr_ratio < CONFIG['MIN_RR_RATIO']:
                logger.info(f"Пропуск {symbol} на {timeframe}: RR={rr_ratio:.2f} ниже минимального {CONFIG['MIN_RR_RATIO']}")
                return None
            for tf in self.timeframes:
                self.last_signal_time[f"{symbol}_{tf}"] = now
            logger.info(f"Сигнал {signal} для {symbol} на {timeframe}")
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'signal': signal,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'volatility': volatility,
                'score': (latest.get('rsi', 50) + sentiment) / 2,
                'atr': atr,
                'market_state': market_state
            }
        except Exception as e:
            logger.error(f"Ошибка анализа пары {symbol} на {timeframe}: {e}")
            return None

    async def send_forecast(self, forecast):
        try:
            symbol = forecast['symbol']
            timeframe = forecast['timeframe']
            entry_price = forecast['entry']
            stop_loss = forecast['stop_loss']
            volatility = forecast['volatility']
            atr = forecast.get('atr', 0.01 * entry_price)
            position_type = (
                "Краткосрочно" if timeframe in ['5m', '15m', '30m', '1h'] else
                "Среднесрочно" if timeframe in ['2h', '4h'] else
                "Долгосрочная"
            )
            entry_range_min = entry_price - min(0.005 * entry_price, 0.5 * atr)
            entry_range_max = entry_price + min(0.005 * entry_price, 0.5 * atr)
            take_profits = [
                entry_price + 0.5 * atr if forecast['signal'] == 'buy' else entry_price - 0.5 * atr,
                entry_price + 2.0 * atr if forecast['signal'] == 'buy' else entry_price - 2.0 * atr,
                entry_price + 3.5 * atr if forecast['signal'] == 'buy' else entry_price - 3.5 * atr,
                entry_price + 5.0 * atr if forecast['signal'] == 'buy' else entry_price - 5.0 * atr
            ]
            if any(abs(tp - entry_price) < CONFIG['MIN_ABS_TAKE_SIZE'] for tp in take_profits):
                logger.info(f"Пропуск прогноза для {symbol} на {timeframe}: тейк-профит слишком близко")
                return None
            message = (
                f"📌 {symbol} {timeframe} | {position_type}\n"
                f"💰 Цена: ${entry_price:.3f}\n"
                f"📈 Точка входа: ${entry_range_max:.3f}–${entry_range_min:.3f}\n"
                f"🔥 Сигнал: {'Покупка' if forecast['signal'] == 'buy' else 'Продажа'}\n\n"
                f"🎯 Тейк-профит:\n"
                f"Цель 1: {take_profits[0]:.3f}\n"
                f"Цель 2: {take_profits[1]:.3f}\n"
                f"Цель 3: {take_profits[2]:.3f}\n"
                f"Цель 4: {take_profits[3]:.3f}\n\n"
                f"🛑 Стоп-лосс: {stop_loss:.3f}\n"
                f"📊 Рынок: {forecast['market_state']}"
            )
            await self.bot.send_message(chat_id=CONFIG['TELEGRAM_CHAT_ID'], text=message)
            logger.info(f"Отправлен прогноз для {symbol} на {timeframe}")
        except Exception as e:
            logger.error(f"Ошибка отправки прогноза: {e}")
            return None

    async def websocket_listener(self):
        logger.info("Запуск WebSocket слушателя...")
        max_subscriptions = 100
        subscriptions = [
            f"{symbol.lower().replace('/', '')}@kline_{tf}"
            for symbol in self.symbols[:CONFIG['MAX_SYMBOLS']//len(self.timeframes)]
            for tf in self.timeframes
        ][:max_subscriptions]
        while True:
            try:
                async with websockets.connect(self.websocket_url, ping_interval=20, ping_timeout=20) as ws:
                    subscribe_msg = {
                        "method": "SUBSCRIBE",
                        "params": subscriptions,
                        "id": 1
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info(f"Подписка на WebSocket: {len(subscriptions)} потоков")
                    while True:
                        try:
                            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
                            if 'k' in message:
                                symbol = next(
                                    (s for s in self.symbols if s.lower().replace('/', '') in message['s'].lower()),
                                    None
                                )
                                if not symbol:
                                    continue
                                tf = message['k']['i']
                                kline = message['k']
                                new_row = pd.DataFrame([{
                                    'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                                    'open': float(kline['o']),
                                    'high': float(kline['h']),
                                    'low': float(kline['l']),
                                    'close': float(kline['c']),
                                    'volume': float(kline['v'])
                                }])
                                if new_row['close'].iloc[0] <= CONFIG['MIN_PRICE']:
                                    continue
                                if not self.data[symbol][tf].empty:
                                    self.data[symbol][tf] = pd.concat([self.data[symbol][tf], new_row], ignore_index=True).tail(50)
                                else:
                                    self.data[symbol][tf] = new_row
                                logger.debug(f"Обновлены данные для {symbol} на {tf}: close={new_row['close'].iloc[0]}")
                        except asyncio.TimeoutError:
                            logger.warning("Таймаут WebSocket, повторная попытка...")
                            break
                        except Exception as e:
                            logger.error(f"Ошибка обработки WebSocket сообщения: {e}")
                            continue
            except Exception as e:
                logger.error(f"Ошибка WebSocket соединения: {e}")
                await asyncio.sleep(5)

async def main():
    try:
        logger.info("Запуск бота...")
        bot = CryptoForecastBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")

if __name__ == "__main__":
    asyncio.run(main())
