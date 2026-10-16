import unittest
from bot import Bot, BIO, DESCRIPTION, discount, compare

class FakeBot(Bot):
    def __init__(self):
        super().__init__('fake'); self.calls = []
    def api(self, method, **params):
        self.calls.append((method, params))
        return {'username': 'Mel_horesPromosbot'} if method == 'getMe' else True

class Tests(unittest.TestCase):
    def test_discount(self):
        self.assertIn('Preço final: 80,00', discount('100 20'))
        self.assertIn('Preço final: 84,92', discount('99,90 15'))
        self.assertIn('Preço final: 0,00', discount('100 100'))
        self.assertIn('Preço final: 100,00', discount('100 0'))
    def test_compare(self):
        self.assertIn('produto B custa 16,67%', compare('12 500 20 1000'))
        self.assertIn('mesmo preço', compare('10 100 20 200'))
        self.assertIn('produto A', compare('10 1000 20 1000'))
    def test_invalid(self):
        for text in ('0 10', '100 101', '-100 10', 'NaN 20', '1e5 20', '100', '1.000,00 20'):
            with self.assertRaises(ValueError): discount(text)
        with self.assertRaises(ValueError): compare('12 0 20 1000')
    def test_profile(self):
        self.assertLessEqual(len(BIO), 120)
        self.assertLessEqual(len(DESCRIPTION), 512)
        bot = FakeBot(); bot.configure()
        self.assertEqual(sum(m == 'setMyDescription' for m,p in bot.calls), 2)
    def test_flows(self):
        bot = FakeBot()
        for text in ('/start', '/desconto', '/comparar', '/desconto 100 20', '/comparar 12 500 20 1000', '99,90 15', '/help', '/privacy', '/unknown', 'abc'):
            bot.handle({'message': {'chat': {'id': 42, 'type': 'private'}, 'text': text}})
        for data in ('discount', 'compare', 'examples', 'help', 'unknown'):
            bot.handle({'callback_query': {'id': 'q', 'data': data, 'message': {'chat': {'id': 42, 'type': 'private'}}}})
        bot.handle({'message': {'chat': {'id': 42, 'type': 'private'}, 'text': '12 500 20 1000', 'reply_to_message': {'text': 'COMPARAR\n'}}})
        self.assertIn('produto B', bot.calls[-1][1]['text'])
        count = len(bot.calls)
        bot.handle({'message': {'chat': {'id': -1, 'type': 'group'}, 'text': '/start'}})
        self.assertEqual(count, len(bot.calls))

if __name__ == '__main__': unittest.main()
