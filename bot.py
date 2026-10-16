"""Melhores Promos: Portuguese shopping arithmetic, without user storage."""
import json
import logging
import os
import re
import signal
import threading
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

NAME = 'Melhores Promos'
USERNAME = 'Mel_horesPromosbot'
BIO = 'Calcule descontos e compare preços por unidade, gratuitamente e sem sair do Telegram.'
DESCRIPTION = ('Melhores Promos é uma calculadora de compras gratuita. Calcule o preço final com desconto e compare dois produtos pelo preço por unidade. Toque em Iniciar e escolha uma ferramenta. Não é um catálogo de ofertas: os cálculos usam os valores informados por você. Sem cadastro ou assinatura.')
WELCOME = ('Bem-vindo ao Melhores Promos!\n\nCalcule descontos ou compare preços por unidade com os valores que você informar. Escolha uma ferramenta abaixo.\n\nServiço gratuito. Não buscamos ofertas em lojas.')
DISCOUNT_PROMPT = 'DESCONTO\nEnvie preço e desconto percentual separados por espaço.\nExemplo: 100 20\nPara centavos: 99,90 15\nUse números sem separador de milhar. O cálculo não inclui frete ou taxas.'
COMPARE_PROMPT = 'COMPARAR\nEnvie quatro números: preço A, quantidade A, preço B, quantidade B.\nExemplo: 12 500 20 1000\nUse a mesma unidade nas duas quantidades (ex.: gramas). Use números sem separador de milhar.'
PRIVACY = ('Este bot não mantém cadastro, banco de dados ou histórico de mensagens. Os valores e o identificador do chat são processados apenas para responder. Os logs não incluem o conteúdo das mensagens. O Telegram pode conservar mensagens conforme suas próprias políticas. Não envie dados pessoais.\n\n/start: menu\n/desconto: calcular desconto\n/comparar: comparar preços\n/help: ajuda\n/privacy: privacidade')


def numbers(text, count):
    parts = text.strip().split()
    if len(parts) != count:
        raise ValueError('Quantidade de valores incorreta.')
    values = []
    for part in parts:
        if not re.fullmatch(r'\d{1,9}(?:[.,]\d{1,4})?', part):
            raise ValueError('Use apenas números positivos, sem separador de milhar.')
        value = Decimal(part.replace(',', '.'))
        if not value.is_finite():
            raise ValueError('Valor inválido.')
        values.append(value)
    return values


def display(value, places='0.01'):
    return format(value.quantize(Decimal(places), rounding=ROUND_HALF_UP), 'f').replace('.', ',')


def discount(text):
    price, percent = numbers(text, 2)
    if price <= 0 or percent > 100:
        raise ValueError('O preço deve ser maior que zero e o desconto deve estar entre 0 e 100%.')
    saving = price * percent / 100
    return f'Preço informado: {display(price)}\nDesconto: {display(percent)}%\nEconomia: {display(saving)}\nPreço final: {display(price - saving)}\n\nValores na mesma moeda do preço informado. Frete e taxas não incluídos.'


def compare(text):
    pa, qa, pb, qb = numbers(text, 4)
    if min(pa, qa, pb, qb) <= 0:
        raise ValueError('Preços e quantidades devem ser maiores que zero.')
    a, b = pa / qa, pb / qb
    # Cross multiplication avoids rounding artefacts when deciding equality.
    if pa * qb == pb * qa:
        conclusion = 'Os dois têm o mesmo preço por unidade.'
    else:
        choice = 'A' if a < b else 'B'
        difference = (max(a, b) - min(a, b)) / max(a, b) * 100
        conclusion = f'O produto {choice} custa {display(difference)}% menos por unidade.'
    return f'Preço por unidade (aproximado):\nA: {display(a, "0.000001")}\nB: {display(b, "0.000001")}\n\n{conclusion}\n\nVálido para a mesma moeda e unidade de medida. Não compara qualidade, frete ou taxas.'


class Bot:
    def __init__(self, token):
        self.token = token

    def api(self, method, **params):
        request = urllib.request.Request(f'https://api.telegram.org/bot{self.token}/{method}', data=json.dumps(params).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'Telegram {method} HTTP {exc.code}') from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError(f'Telegram {method} network failure') from None
        if not result.get('ok'):
            raise RuntimeError(f'Telegram {method} failed')
        return result['result']

    def configure(self):
        me = self.api('getMe')
        if me.get('username', '').lower() != USERNAME.lower():
            raise RuntimeError('BOT_TOKEN must belong to @Mel_horesPromosbot')
        self.api('setMyName', name=NAME)
        for language in ('', 'pt'):
            self.api('setMyShortDescription', short_description=BIO, language_code=language)
            self.api('setMyDescription', description=DESCRIPTION, language_code=language)
            self.api('setMyCommands', language_code=language, commands=[{'command': c, 'description': d} for c, d in [('start', 'Menu principal'), ('desconto', 'Calcular desconto'), ('comparar', 'Comparar preço por unidade'), ('help', 'Como usar'), ('privacy', 'Privacidade')]])

    def send(self, chat, text, prompt=False):
        keyboard = {'inline_keyboard': [[{'text': title, 'callback_data': data}] for title, data in [('Calcular desconto', 'discount'), ('Comparar preços', 'compare'), ('Exemplos', 'examples'), ('Ajuda e privacidade', 'help')]]}
        self.api('sendMessage', chat_id=chat, text=text, reply_markup={'force_reply': True, 'input_field_placeholder': 'Ex.: 100 20'} if prompt else keyboard)

    def handle(self, update):
        callback = update.get('callback_query')
        message = callback.get('message', {}) if callback else update.get('message', {})
        if message.get('chat', {}).get('type') != 'private':
            return
        chat = message['chat']['id']
        if callback:
            self.api('answerCallbackQuery', callback_query_id=callback['id'])
            data = callback.get('data')
            if data == 'discount':
                self.send(chat, DISCOUNT_PROMPT, True)
            elif data == 'compare':
                self.send(chat, COMPARE_PROMPT, True)
            elif data == 'help':
                self.send(chat, PRIVACY)
            elif data == 'examples':
                self.send(chat, 'Exemplos ilustrativos:\n\n/desconto 100 20\nResultado: preço final 80,00.\n\n/comparar 12 500 20 1000\nResultado: B custa menos por unidade.\n\nVocê pode enviar esses comandos com seus próprios valores.')
            else:
                self.send(chat, WELCOME)
            return
        text = message.get('text', '').strip()
        if not text:
            self.send(chat, 'Use os botões ou envie números em texto. Não é necessário enviar fotos ou documentos.'); return
        command, _, arguments = text.partition(' ')
        command = command.split('@')[0].lower()
        if command == '/start':
            self.send(chat, WELCOME); return
        if command in ('/help', '/privacy'):
            self.send(chat, PRIVACY); return
        if command in ('/desconto', '/comparar') and not arguments.strip():
            self.send(chat, DISCOUNT_PROMPT if command == '/desconto' else COMPARE_PROMPT, True); return
        try:
            if command == '/desconto':
                result = discount(arguments)
            elif command == '/comparar':
                result = compare(arguments)
            elif command.startswith('/'):
                self.send(chat, 'Comando não reconhecido. Use /start para abrir o menu.'); return
            else:
                prompt = message.get('reply_to_message', {}).get('text', '')
                if prompt.startswith('COMPARAR'):
                    result = compare(text)
                elif prompt.startswith('DESCONTO'):
                    result = discount(text)
                elif len(text.split()) == 4:
                    result = compare(text)
                else:
                    result = discount(text)
            self.send(chat, result)
        except (ValueError, InvalidOperation) as exc:
            self.send(chat, f'{exc}\n\nDesconto: envie 100 20\nComparação: envie 12 500 20 1000\nUse a mesma moeda e unidade de medida para comparar.')


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    token = os.environ.get('BOT_TOKEN', '').strip()
    if not token:
        raise SystemExit('Set BOT_TOKEN in hosting environment. Never commit it.')
    bot = Bot(token)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    bot.configure()
    bot.api('deleteWebhook', drop_pending_updates=False)
    logging.info('Profile configured; polling started')
    offset = 0
    while not stop.is_set():
        try:
            updates = bot.api('getUpdates', offset=offset, timeout=25, allowed_updates=['message', 'callback_query'])
            for update in updates:
                if stop.is_set():
                    break
                try:
                    bot.handle(update)
                except Exception:
                    logging.error('Update failed; user can retry with /start')
                offset = update['update_id'] + 1
        except RuntimeError:
            logging.warning('Polling unavailable; retrying')
            stop.wait(5)
    logging.info('Worker stopped')


if __name__ == '__main__':
    main()
