import threading

from django.db import connection
from django.test import TransactionTestCase

from courrier.models import Registre
from courrier.services import generer_numero


class NumerotationConcurrenteTest(TransactionTestCase):
    """La numérotation à verrou ne doit jamais produire de doublon."""

    def setUp(self):
        # ARR est déjà seedé par la data migration ; get_or_create pour être robuste.
        self.registre, _ = Registre.objects.get_or_create(
            code='ARR', defaults={'libelle': 'Arrivée', 'sens': 'ARRIVEE'})

    def test_deux_threads_numeros_distincts(self):
        resultats = []
        verrou = threading.Lock()

        def worker():
            numero = generer_numero(self.registre)
            with verrou:
                resultats.append(numero)
            connection.close()  # chaque thread a sa propre connexion

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(resultats), 2)
        self.assertEqual(len(set(resultats)), 2, f'Doublon de numéro détecté : {resultats}')
