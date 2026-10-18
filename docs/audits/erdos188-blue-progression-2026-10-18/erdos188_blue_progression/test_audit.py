"""Meaningful rejection and arithmetic controls for the independent acceptor."""
from fractions import Fraction as Q
import unittest
from .audit import (Config, InvalidCertificate, Verifier, trig_bounds, pi_bounds, verify_tree, verify_directions)

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.cfg=Config((Q(1,4),Q(0)),(Q(0),Q(1,4)),((Q(1,8),Q(1,8)),),(Q(1),))
        self.witness=((0,),(0,),(0,),(0,))
    def check(self,codes=(0,),witness=None,box=(Q(0),Q(1,10000),Q(1,20000)),config=None,depth=2):
        return verify_tree(config or self.cfg,box,codes,witness or self.witness,60,depth)
    def test_cover(self):
        self.assertEqual(self.check()['leaves'],1)
    def test_trig_zero(self):
        self.assertEqual(trig_bounds(Q(0)),((1<<40,1<<40),(0,0)))
    def test_pi(self):
        lo,hi=pi_bounds();self.assertLess(Q(314159,100000),lo);self.assertLess(hi,Q(31416,10000))
    def test_reject_missing_leaf(self):
        with self.assertRaises(InvalidCertificate):self.check(())
    def test_reject_extra_leaf(self):
        with self.assertRaises(InvalidCertificate):self.check((0,0))
    def test_reject_negative_index(self):
        with self.assertRaises(InvalidCertificate):self.check((-2,))
    def test_reject_invalid_cell(self):
        with self.assertRaises(InvalidCertificate):self.check(witness=((1,),(0,),(0,),(0,)))
    def test_reject_invalid_j(self):
        for j in [-1,60]:
            with self.assertRaises(InvalidCertificate):self.check(witness=((0,),(j,),(0,),(0,)))
    def test_reject_invalid_midpoint(self):
        with self.assertRaises(InvalidCertificate):self.check(box=(Q(0),Q(1,10000),Q(1)))
    def test_reject_depth_overflow(self):
        with self.assertRaises(InvalidCertificate):self.check((-1,),depth=0)
    def test_reject_uncovered(self):
        cfg=Config(self.cfg.p1,self.cfg.p2,self.cfg.centres,(Q(1,100),))
        with self.assertRaises(InvalidCertificate):self.check(config=cfg)
    def test_subdivision(self):
        self.assertEqual(self.check((-1,0,0,0,0))['leaves'],4)
    def test_directions(self):
        self.assertEqual(verify_directions([(Q(0),Q(1)),(Q(1),Q(31416,10000))]),2)
    def test_direction_gap(self):
        with self.assertRaises(InvalidCertificate):verify_directions([(Q(0),Q(1)),(Q(1001,1000),Q(31416,10000))])
    def test_direction_short(self):
        with self.assertRaises(InvalidCertificate):verify_directions([(Q(0),Q(3))])
    def test_direction_overlap(self):
        with self.assertRaises(InvalidCertificate):verify_directions([(Q(0),Q(2)),(Q(1),Q(4))])
    def test_source_config(self):
        import json
        from pathlib import Path
        cfg=Config.from_json(json.loads(Path(__file__).with_name('cfg_k60.json').read_text()))
        self.assertEqual(cfg.grid,(63,55))
        self.assertEqual(len(cfg.centres),90)
        self.assertEqual(len(cfg.radii),90)
    def test_uniform_radii_parser(self):
        cfg=Config.from_json({'k':24,'P1':['1','0'],'P2':['1/2','1'],'centres':[['0','0'],['1/2','1/2']],'h':'1/3'})
        self.assertEqual(cfg.radii,(Q(1,3),Q(1,3)))
    def test_bad_config(self):
        with self.assertRaises(InvalidCertificate):Config((Q(0),Q(0)),self.cfg.p2,self.cfg.centres,self.cfg.radii)
        with self.assertRaises(InvalidCertificate):Config(self.cfg.p1,self.cfg.p2,self.cfg.centres,(Q(-1),))
    def test_cached_translation(self):
        verifier=Verifier(self.cfg)
        box=(Q(0),Q(1,10000),Q(1,20000))
        first=verifier.verify(box,(0,),self.witness,60,2)
        second=verifier.verify(box,(0,),self.witness,60,2)
        self.assertEqual(first,second)
        self.assertEqual(len(verifier.translations),1)
if __name__=='__main__':unittest.main()
