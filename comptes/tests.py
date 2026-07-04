from django.test import TestCase

from comptes.models import Direction


class DirectionDescendantsTest(TestCase):
    """Direction.get_descendants() sur 3 niveaux."""

    def setUp(self):
        self.sg = Direction.objects.create(sigle='SG', nom='Secrétariat Général')
        self.dgb = Direction.objects.create(sigle='DGB', nom='Direction Générale du Budget', parent=self.sg)
        self.dbe = Direction.objects.create(sigle='DBE', nom="Direction du Budget de l'État", parent=self.dgb)
        self.div = Direction.objects.create(sigle='DIVDEP', nom='Division des dépenses', parent=self.dbe)
        # branche sœur (ne doit pas apparaître dans le sous-arbre DGB)
        self.dgi = Direction.objects.create(sigle='DGI', nom='Direction Générale des Impôts', parent=self.sg)

    def test_sous_arbre_dgb_sur_trois_niveaux(self):
        sigles = {d.sigle for d in self.dgb.get_descendants()}
        self.assertEqual(sigles, {'DGB', 'DBE', 'DIVDEP'})
        self.assertNotIn('DGI', sigles)
        self.assertNotIn('SG', sigles)

    def test_descendant_ids_sans_soi(self):
        ids = self.dgb.descendant_ids(inclure_soi=False)
        self.assertEqual(set(ids), {self.dbe.id, self.div.id})

    def test_feuille(self):
        self.assertEqual([d.sigle for d in self.div.get_descendants()], ['DIVDEP'])

    def test_racine_complete(self):
        sigles = {d.sigle for d in self.sg.get_descendants()}
        self.assertEqual(sigles, {'SG', 'DGB', 'DBE', 'DIVDEP', 'DGI'})
