import unittest
import easy_mornings_server.__main__ as main


class TestMain(unittest.TestCase):

    def test(self):
        main.run(verbose=True)