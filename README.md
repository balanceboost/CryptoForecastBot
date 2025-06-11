CryptoForecastBot
Описание
Проект требует доработки, настройки и отладки.
CryptoForecastBot — это аналитический бот для прогнозирования движений криптовалютного рынка на бирже Binance. Бот использует технические индикаторы (RSI, MACD, Bollinger Bands, Stochastic, OBV, ATR, ADX), анализ свечных паттернов, уровни поддержки/сопротивления и новостной сентимент (через NewsAPI) для генерации торговых сигналов. Сигналы отправляются в Telegram-канал с указанием точек входа, стоп-лосса и тейк-профита. Бот поддерживает анализ на таймфреймах 5m, 15m, 30m, 1h, 2h, 4h, 8h, 1d, фильтрацию пар по ликвидности, спреду и объёму, а также адаптацию индикаторов под рыночные условия. Он не выполняет сделки автоматически, а предоставляет аналитику для принятия торговых решений.
Основные возможности:

Анализ до 50 торговых пар USDT (настраиваемый список, по умолчанию включает BTC/USDT, ETH/USDT, BNB/USDT и др.).
Поддержка таймфреймов: 5m, 15m, 30m, 1h, 2h, 4h, 8h, 1d.
Технические индикаторы с динамической адаптацией под волатильность и рыночный тренд.
Фильтрация пар по ликвидности, спреду и объёму.
Интеграция с NewsAPI для анализа новостного сентимента.
WebSocket для получения рыночных данных в реальном времени.
Логирование с ротацией файлов и красивым выводом в консоль.
Сохранение сигналов в signals.json для последующего анализа.

Установка

Клонируйте репозиторий:
git clone https://github.com/your-username/CryptoForecastBot.git
cd CryptoForecastBot


Установите зависимости:Убедитесь, что у вас установлен Python 3.8+. Создайте виртуальное окружение и установите зависимости:
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
pip install -r requirements.txt

Содержимое requirements.txt:
ccxt>=2.0.0
pandas>=1.5.0
numpy>=1.23.0
python-telegram-bot>=13.7
websockets>=10.0
requests>=2.28.0
TA-Lib>=0.4.24
rich>=12.0.0


Установите TA-Lib:Для работы индикаторов требуется библиотека TA-Lib. Следуйте инструкциям для вашей ОС:

Ubuntu/Debian:sudo apt-get install libta-lib0 libta-lib-dev
pip install TA-Lib


Windows:Скачайте pre-built бинарники с Unofficial Windows Binaries for Python и установите:pip install TA_Lib‑0.4.24‑cp39‑cp39‑win_amd64.whl


MacOS:brew install ta-lib
pip install TA-Lib





Настройка

Обновите конфигурацию в коде:Откройте файл crypto_forecast_bot.py и обновите словарь CONFIG с вашими ключами и настройками:CONFIG = {
    'BINANCE_API_KEY': 'your_binance_api_key',
    'BINANCE_API_SECRET': 'your_binance_api_secret',
    'NEWS_API_KEY': 'your_newsapi_key',
    'TELEGRAM_BOT_TOKEN': 'your_telegram_bot_token',
    'TELEGRAM_CHAT_ID': 'your_telegram_chat_id',
    'TRADING_PAIRS': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
    'TIMEFRAMES': ['5m', '15m', '30m', '1h', '2h', '4h', '8h', '1d'],
    ...
}


Binance API Key: Получите на Binance API Management.
NewsAPI Key: Зарегистрируйтесь на NewsAPI и получите ключ.
Telegram Bot Token: Создайте бота через @BotFather и получите токен.
Telegram Chat ID: ID вашего Telegram-канала или группы (можно узнать через бота @getidsbot).



Использование

Запустите бота:
python crypto_forecast_bot.py


Мониторинг:

Логи записываются в crypto_forecast_bot.log с ротацией (макс. 10 МБ, 5 резервных копий).
Сигналы сохраняются в signals.json.
Прогнозы отправляются в указанный Telegram-канал в формате:📌 BTC/USDT 1h | Среднесрочно
💰 Цена: $45000.000
📈 Точка входа: $45225.000–$44775.000
🔥 Сигнал: Покупка
🎯 Тейк-профит:
Цель 1: $45250.000
Цель 2: $45500.000
Цель 3: $45750.000
Цель 4: $46000.000
🛑 Стоп-лосс: $44500.000
📊 Рынок: bullish




Остановка:Завершите выполнение с помощью Ctrl+C.


Структура проекта
CryptoForecastBot/
├── crypto_forecast_bot.py       # Основной скрипт бота
├── signals.json                 # Лог сигналов
├── crypto_forecast_bot.log      # Лог работы бота
├── requirements.txt             # Зависимости
└── README.md                    # Документация

Для поддержки автора: TFbR9gXb5r6pcALasjX1FKBArbKc4xBjY8 (USDT, сеть TRC-20)
Контрибьютинг

Форкните репозиторий.
Создайте ветку для вашей фичи (git checkout -b feature/your-feature).
Сделайте коммиты с понятными сообщениями.
Отправьте Pull Request в main.

Лицензия
Проект распространяется под лицензией MIT. Подробности в файле LICENSE.
Предупреждение
Торговля криптовалютами сопряжена с высокими рисками. Прогнозы бота не являются финансовыми рекомендациями. Используйте бота на свой страх и риск. Автор не несёт ответственности за финансовые убытки.

CryptoForecastBot
Overview
The project requires further development, customization, and debugging.
CryptoForecastBot is an analytical bot designed for forecasting cryptocurrency market movements on the Binance exchange. It leverages technical indicators (RSI, MACD, Bollinger Bands, Stochastic, OBV, ATR, ADX), candlestick pattern analysis, support/resistance levels, and news sentiment (via NewsAPI) to generate trading signals. The signals are sent to a Telegram channel, including entry points, stop-loss, and take-profit levels. The bot supports analysis on timeframes 5m, 15m, 30m, 1h, 2h, 4h, 8h, 1d, filters pairs by liquidity, spread, and volume, and adapts indicators to market conditions. It does not execute trades automatically but provides analytics for informed trading decisions.
Key Features:

Analysis of up to 50 USDT trading pairs (configurable, defaults include BTC/USDT, ETH/USDT, BNB/USDT, etc.).
Supported timeframes: 5m, 15m, 30m, 1h, 2h, 4h, 8h, 1d.
Technical indicators with dynamic adaptation to volatility and market trends.
Filtering pairs by liquidity, spread, and volume.
Integration with NewsAPI for news sentiment analysis.
WebSocket for real-time market data.
Logging with file rotation and formatted console output.
Signal storage in signals.json for further analysis.

Installation

Clone the repository:
git clone https://github.com/your-username/CryptoForecastBot.git
cd CryptoForecastBot


Install dependencies:Ensure you have Python 3.8+ installed. Create a virtual environment and install dependencies:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Contents of requirements.txt:
ccxt>=2.0.0
pandas>=1.5.0
numpy>=1.23.0
python-telegram-bot>=13.7
websockets>=10.0
requests>=2.28.0
TA-Lib>=0.4.24
rich>=12.0.0


Install TA-Lib:The TA-Lib library is required for technical indicators. Follow the instructions for your OS:

Ubuntu/Debian:sudo apt-get install libta-lib0 libta-lib-dev
pip install TA-Lib


Windows:Download pre-built binaries from Unofficial Windows Binaries for Python and install:pip install TA_Lib‑0.4.24‑cp39‑cp39‑win_amd64.whl


macOS:brew install ta-lib
pip install TA-Lib





Configuration

Update configuration in code:Open crypto_forecast_bot.py and update the CONFIG dictionary with your keys and settings:CONFIG = {
    'BINANCE_API_KEY': 'your_binance_api_key',
    'BINANCE_API_SECRET': 'your_binance_api_secret',
    'NEWS_API_KEY': 'your_newsapi_key',
    'TELEGRAM_BOT_TOKEN': 'your_telegram_bot_token',
    'TELEGRAM_CHAT_ID': 'your_telegram_chat_id',
    'TRADING_PAIRS': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
    'TIMEFRAMES': ['5m', '15m', '30m', '1h', '2h', '4h', '8h', '1d'],
    ...
}


Binance API Key: Obtain from Binance API Management.
NewsAPI Key: Sign up at NewsAPI to get a key.
Telegram Bot Token: Create a bot via @BotFather and get the token.
Telegram Chat ID: Find your channel or group ID using @getidsbot.



Usage

Run the bot:
python crypto_forecast_bot.py


Monitoring:

Logs are written to crypto_forecast_bot.log with rotation (max 10 MB, 5 backups).
Signals are saved in signals.json.
Forecasts are sent to the specified Telegram channel in the format:📌 BTC/USDT 1h | Medium-term
💰 Price: $45000.000
📈 Entry Point: $45225.000–$44775.000
🔥 Signal: Buy
🎯 Take-Profit:
Target 1: $45250.000
Target 2: $45500.000
Target 3: $45750.000
Target 4: $46000.000
🛑 Stop-Loss: $44500.000
📊 Market: bullish




Stopping:Terminate the bot with Ctrl+C.


Project Structure
CryptoForecastBot/
├── crypto_forecast_bot.py       # Main bot script
├── signals.json                 # Signal log
├── crypto_forecast_bot.log      # Bot operation log
├── requirements.txt             # Dependencies
└── README.md                    # Documentation

To support the author: TFbR9gXb5r6pcALasjX1FKBArbKc4xBjY8 (USDT, TRC-20 network)
Contributing

Fork the repository.
Create a feature branch (git checkout -b feature/your-feature).
Commit your changes with clear messages.
Submit a Pull Request to the main branch.

License
This project is licensed under the MIT License. See the LICENSE file for details.
Disclaimer
Cryptocurrency trading involves high risks. The bot’s forecasts are not financial advice. Use this bot at your own risk. The author is not responsible for any financial losses.
