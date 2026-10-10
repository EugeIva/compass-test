import csv
import io
import pytest
from find_duplicates import (
    normalize_string,
    email_local_part,
    names_match,
    emails_match,
    zips_match,
    addresses_match,
    score_pair,
    classify,
    find_duplicates,
)


class TestNormalize:
    def test_lowercase_and_strip(self):
        assert normalize_string('  Hello WORLD  ') == 'hello world'

    def test_remove_punctuation(self):
        assert normalize_string('Tellus. Rd.') == 'tellus rd'

    def test_collapse_whitespace(self):
        assert normalize_string('Ap    #312   Ave') == 'ap 312 ave'


class TestEmailLocalPart:
    def test_normal(self):
        assert email_local_part('foo@bar.com') == 'foo'

    def test_no_at_sign(self):
        assert email_local_part('invalid') == ''

    def test_empty(self):
        assert email_local_part('') == ''

    def test_case_insensitive(self):
        assert email_local_part('FOO@Bar.com') == 'foo'


class TestNamesMatch:
    def test_exact(self):
        first, last = names_match('Ciara', 'French', 'Ciara', 'French')
        assert first == 15 and last == 20

    def test_initial_matches_full(self):
        first, last = names_match('C', 'French', 'Ciara', 'French')
        assert first == 12 and last == 20

    def test_full_matches_initial(self):
        first, last = names_match('Ciara', 'French', 'C', 'French')
        assert first == 12 and last == 20

    def test_first_letter_match(self):
        first, last = names_match('Ciara', 'French', 'Charles', 'French')
        assert first == 5 and last == 20

    def test_no_match(self):
        first, last = names_match('Ciara', 'French', 'Victor', 'Savage')
        assert first == 0 and last == 0

    def test_empty_names(self):
        first, last = names_match('', 'French', '', 'Savage')
        assert first == 0 and last == 0


class TestEmailsMatch:
    def test_exact(self):
        assert emails_match('a@b.com', 'a@b.com') == 40

    def test_same_local_diff_domain(self):
        assert emails_match('a@outlook.net', 'a@yahoo.net') == 35

    def test_different(self):
        assert emails_match('a@b.com', 'c@b.com') == 0

    def test_empty(self):
        assert emails_match('', 'a@b.com') == 0

    def test_case_insensitive(self):
        assert emails_match('A@B.COM', 'a@b.com') == 40


class TestZipsMatch:
    def test_match(self):
        assert zips_match('39746', '39746') == 15

    def test_mismatch(self):
        assert zips_match('39746', '76837') == 0

    def test_empty(self):
        assert zips_match('', '39746') == 0


class TestAddressesMatch:
    def test_exact(self):
        assert addresses_match('449-6990 Tellus. Rd.', '449-6990 Tellus. Rd.') == 10

    def test_subset(self):
        assert addresses_match('Ap #312-8611 Lacus. Ave', '312-8611 Lacus. Ave') == 10

    def test_single_token(self):
        assert addresses_match('Main St.', 'Main Ave.') == 5

    def test_no_match(self):
        assert addresses_match('Oak St.', 'Elm Rd.') == 0

    def test_empty(self):
        assert addresses_match('', 'Oak St.') == 0

    def test_po_box_variants(self):
        result = addresses_match('P.O. Box 775, 8910 Arcu. Road', '8910 Arcu. Road')
        assert result == 10


class TestScorePair:
    def make_row(self, name='Ciara', name1='French', email='a@b.com', postalZip='39746', address='449-6990 Tellus. Rd.'):
        return dict(contactID='1', name=name, name1=name1, email=email, postalZip=postalZip, address=address)

    def test_full_match(self):
        a = self.make_row()
        b = self.make_row(name='C')
        assert score_pair(a, b) >= 70

    def test_no_match(self):
        a = self.make_row()
        b = self.make_row(name='Victor', name1='Savage', email='c@d.com', postalZip='82025', address='P.O. Box 775, 8910 Arcu. Road')
        assert score_pair(a, b) < 20


class TestClassify:
    def test_high(self):
        assert classify(80) == 'High'

    def test_high_boundary_low(self):
        assert classify(70) == 'High'

    def test_medium(self):
        assert classify(55) == 'Medium'

    def test_medium_boundaries(self):
        assert classify(40) == 'Medium'
        assert classify(69) == 'Medium'

    def test_low(self):
        assert classify(30) == 'Low'

    def test_low_boundaries(self):
        assert classify(20) == 'Low'
        assert classify(39) == 'Low'

    def test_below_threshold(self):
        assert classify(19) is None
        assert classify(0) is None


class TestFindDuplicatesIntegration:
    CSV_DATA = """\
contactID,name,name1,email,postalZip,address
1,Ciara,French,mollis.lectus.pede@outlook.net,39746,449-6990 Tellus. Rd.
2,Victor,Savage,orci@protonmail.net,82025,P.O. Box 7758910 Arcu. Road
3,C,French,mollis.lectus.pede@yahoo.net,39746,449-6990 Tellus. Rd.
4,V,Savage,orci@att.net,82025,P.O. Box 7758910 Arcu. Road
"""

    def test_finds_correct_pairs(self):
        reader = csv.DictReader(io.StringIO(self.CSV_DATA))
        rows = list(reader)
        results = list(find_duplicates(rows))
        pairs = {(r['contactID_source'], r['contactID_match']): r['accuracy'] for r in results}
        assert ('1', '3') in pairs
        assert pairs[('1', '3')] == 'High'
        assert ('2', '4') in pairs
        assert pairs[('2', '4')] == 'High'

    def test_output_columns(self):
        reader = csv.DictReader(io.StringIO(self.CSV_DATA))
        rows = list(reader)
        for r in find_duplicates(rows):
            assert set(r.keys()) == {'contactID_source', 'contactID_match', 'accuracy'}

    def test_source_less_than_match(self):
        reader = csv.DictReader(io.StringIO(self.CSV_DATA))
        rows = list(reader)
        for r in find_duplicates(rows):
            assert int(r['contactID_source']) < int(r['contactID_match'])