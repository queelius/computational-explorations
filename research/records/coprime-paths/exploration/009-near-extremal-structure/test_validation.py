import unittest, tempfile, gzip, json, importlib.util
from pathlib import Path
BASE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v',BASE/'validate_endpoint_cuts.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Validation(unittest.TestCase):
 def test_full_archive(self):
  r=v.validate(BASE/'endpoint-cuts.json.gz');self.assertEqual(r['orbits'],30793);self.assertEqual(r['negative'],44)
 def test_missing_record(self):
  d=json.load(gzip.open(BASE/'endpoint-cuts.json.gz'));d['records'].pop()
  with tempfile.TemporaryDirectory(dir=BASE) as td:
   p=Path(td)/'bad.gz'
   with gzip.open(p,'wt') as f:json.dump(d,f)
   with self.assertRaises(AssertionError):v.validate(p)
 def test_invalid_path(self):
  d=json.load(gzip.open(BASE/'endpoint-cuts.json.gz'));d['records'][0]['path']=[1]*10
  with tempfile.TemporaryDirectory(dir=BASE) as td:
   p=Path(td)/'bad.gz'
   with gzip.open(p,'wt') as f:json.dump(d,f)
   with self.assertRaises(AssertionError):v.validate(p)
if __name__=='__main__':unittest.main()
