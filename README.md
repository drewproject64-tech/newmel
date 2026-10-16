# Melhores Promos — @Mel_horesPromosbot

Simple Portuguese shopping calculator: percentage discounts and unit-price comparisons. Free, no registration, database, admin panel, broadcasts, affiliate links or channel joins. Does not fetch live deals or claim to find the best market price.

## Hosting

Python 3.12+. Build: `pip install -r requirements.txt`. Start: `python bot.py`.
Set `BOT_TOKEN` as a secret in the hosting environment; do not commit it. `.env.example` documents the variable; .env files are not automatically loaded. Run one background worker per token. No disk or database is needed.

Startup checks that the token belongs to @Mel_horesPromosbot, then sets its name, profile bio, pre-Start description and commands in default Portuguese and Portuguese localization. You must run the worker before those live profile changes occur. Add an original shopping/calculator profile image using @BotFather before advertising. No token has been included and this repository alone does not deploy the bot.

## User flow

Start → choose discount or comparison → reply with the numbers → receive calculation and tool buttons. Users may also enter commands directly:

- `/desconto 100 20` gives 80.00 final price.
- `/comparar 12 500 20 1000` compares price per same unit.
- `/help` and `/privacy` explain usage and data handling.

Accepts decimal comma or point, without thousands separators. Decimal arithmetic and half-up display rounding. Comparisons require matching currencies and quantity units. Shipping, taxes and product quality are not included. All numbers shown in examples are illustrative, not offers.

Chat IDs and values are processed transiently to reply. No user records or conversation history are written by the app. Logs omit message content and tokens. Telegram may retain messages according to its policies.

## Telegram Ads

Use Portuguese ads and matching placements. Describe the actual calculator, not unverified promotions, prizes or earnings. There is no gambling, paid chance mechanism, cash reward or moderator-specific behaviour. Keep the service consistent after review. Approval is Telegram's decision; no code guarantees approval. These changes do not establish the reason for any previous bot's rejection.

Rules: https://ads.telegram.org/guidelines
Terms: https://ads.telegram.org/tos

Suggested ad text:
Calcule descontos e compare preços por unidade com o Melhores Promos. Uma ferramenta gratuita de compras dentro do Telegram.

## Verification

`python -m unittest discover -s tests -v`

`python -m py_compile bot.py`

Offline tests cover arithmetic, input validation, command/menu flows and profile text limits. Live Telegram delivery needs the real token and running host.
