import unittest,tempfile,gzip,json,importlib.util
from pathlib import Path
BASE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v',BASE/'validate.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Validation(unittest.TestCase):
 def mutate(self,fn):
  d=json.load(gzip.open(BASE/'propagation.json.gz'));fn(d)
  with tempfile.TemporaryDirectory(dir=BASE) as td:
   p=Path(td)/'bad.gz'
   with gzip.open(p,'wt') as f:json.dump(d,f)
   with self.assertRaises(AssertionError):v.validate(p)
 def test_complete(self):self.assertEqual(v.validate(BASE/'propagation.json.gz'),{'cases':44,'proved':44,'implications':1079,'complete':True})
 def test_missing_case(self):self.mutate(lambda d:d['records'].pop())
 def test_duplicate_case(self):self.mutate(lambda d:d['records'].append(d['records'][0]))
 def test_invalid_implication(self):self.mutate(lambda d:d['records'][0]['steps'][0].update(path=[1]*10))
 def test_wrong_forced_color(self):self.mutate(lambda d:d['records'][0]['steps'][0].update(color=1-d['records'][0]['steps'][0]['color']))
 def test_bad_final_path(self):self.mutate(lambda d:d['records'][0]['conflict'].update(path=[1]*10))
 def test_bad_assumption(self):self.mutate(lambda d:d['records'][0].update(a=[1,2,3,4,5,6]))
if __name__=='__main__':unittest.main()
