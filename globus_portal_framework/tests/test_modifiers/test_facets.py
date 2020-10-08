import datetime
from django.test import TestCase

from globus_portal_framework.modifiers import facets
from globus_portal_framework.tests import (
    get_mock_data, PROCESSED_PORTAL_FACETS
)


class FacetModifierTests(TestCase):
    """See test_gsearch for the application of modifiers on search data.
    This class only unit tests the modifiers themselves."""
    def setUp(self):
        self.facets = get_mock_data(PROCESSED_PORTAL_FACETS)
        for facet in self.facets:
            if facet['type'] != 'date_histogram':
                continue
            for bucket in facet['buckets']:
                dt = datetime.datetime.now().fromtimestamp(bucket['datetime'])
                bucket['datetime'] = dt

    def test_all_facet_modifiers_throw_no_exceptions(self):
        all_mods = [
            facets.drop_empty,
            facets.reverse,
            facets.sort_terms,
            facets.sort_terms_numerically,
        ]
        for mod in all_mods:
            self.facets = mod(self.facets)
        self.assertEqual(len(self.facets), 6)

    def test_drop_empty(self):
        self.facets[0]['buckets'] = []
        self.facets = facets.drop_empty(self.facets)
        self.assertEqual(len(self.facets), 5)

    def test_reverse(self):
        self.assertEqual(self.facets[0]['buckets'][0]['value'],
                         'Sheep Results')
        self.assertEqual(self.facets[0]['buckets'][2]['value'],
                         'Lollipop Results')
        self.facets = facets.reverse(self.facets)

        self.assertEqual(self.facets[0]['buckets'][0]['value'],
                         'Lollipop Results')
        self.assertEqual(self.facets[0]['buckets'][2]['value'],
                         'Sheep Results')

    def test_sort_terms(self):
        pre_sort_names = [b['value'] for b in self.facets[0]['buckets']]
        pre_expected = ['Sheep Results', 'Rainbow Results', 'Lollipop Results']
        self.assertEqual(pre_sort_names, pre_expected)

        self.facets = facets.sort_terms(self.facets)
        post_sort_names = [b['value'] for b in self.facets[0]['buckets']]
        post_expected = ['Lollipop Results', 'Rainbow Results',
                         'Sheep Results']
        self.assertEqual(post_sort_names, post_expected)

    def test_sort_terms_numerically(self):
        pre_sort_names = [b['value'] for b in self.facets[1]['buckets']]
        self.assertEqual(pre_sort_names, ['2018', '2016', '2017'])

        self.facets = facets.sort_terms(self.facets)
        post_sort_names = [b['value'] for b in self.facets[1]['buckets']]
        self.assertEqual(post_sort_names, ['2016', '2017', '2018'])
