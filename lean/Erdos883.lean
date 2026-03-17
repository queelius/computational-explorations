/-
# Erdős Problem #883: Odd Cycles in Coprime Graphs

## Problem Statement
Let G(n) be the graph on {1,...,n} where vertices a, b are connected iff gcd(a,b) = 1.
Define A* = {i ∈ [n] : 2|i or 3|i} (the extremal set).

**Theorem**: For A ⊆ [n] with |A| > |A*|, G(A) contains a triangle (hence an odd cycle).

**Full Problem**: G(A) contains all odd cycles of length ≤ ⌊n/3⌋ + 1.

## Proof Strategy
1. A* = multiples of 2 or 3, with |A*| = ⌊n/2⌋ + ⌊n/3⌋ - ⌊n/6⌋ ≈ 2n/3
2. Any A exceeding |A*| must contain an element coprime to 6
3. Case analysis on membership of 1, 2, 3 in A
4. Each case produces a coprime triple or leads to contradiction
5. Small cases (n < 15) verified computationally
-/

import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Data.Nat.GCD.Basic
import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Tactic.Omega
import Mathlib.Combinatorics.SimpleGraph.Basic

open Finset Nat

namespace Erdos883

/-! ## Core Definitions -/

/-- Two natural numbers are coprime. -/
def Coprime (a b : ℕ) : Prop := Nat.gcd a b = 1

/-- The coprime graph on a finite set A ⊆ ℕ: vertices are elements of A,
    edges connect pairs with gcd = 1. -/
def CoprimeGraph (A : Finset ℕ) : SimpleGraph A where
  Adj x y := Coprime x.val y.val ∧ x ≠ y
  symm := by
    intro x y ⟨hc, hne⟩
    exact ⟨by rwa [Nat.gcd_comm] at hc, Ne.symm hne⟩
  loopless := by
    intro x ⟨_, hne⟩
    exact hne rfl

/-- A coprime triple: three elements that are pairwise coprime. -/
def IsCopTriple (a b c : ℕ) : Prop :=
  Coprime a b ∧ Coprime a c ∧ Coprime b c

/-- A set A contains a coprime triple. -/
def HasCopTriple (A : Finset ℕ) : Prop :=
  ∃ a b c, a ∈ A ∧ b ∈ A ∧ c ∈ A ∧ a ≠ b ∧ a ≠ c ∧ b ≠ c ∧ IsCopTriple a b c

/-- The extremal set A*(n) = {i ∈ [n] : 2|i or 3|i}. -/
def ExtremalSet (n : ℕ) : Finset ℕ :=
  (Finset.range n).filter (fun i => (i + 1) % 2 = 0 ∨ (i + 1) % 3 = 0)
  |>.image (· + 1)

/-- Elements coprime to 6: residues 1 and 5 mod 6. -/
def CoprimeTo6 (a : ℕ) : Prop := Nat.gcd a 6 = 1

/-- The set R₁ ∪ R₅ = {i ∈ [n] : gcd(i, 6) = 1}. -/
def R15 (n : ℕ) : Finset ℕ :=
  (Finset.range n).filter (fun i => Nat.gcd (i + 1) 6 = 1)
  |>.image (· + 1)

/-! ## Membership Lemmas for ExtremalSet -/

/-- 2 is in ExtremalSet n for n ≥ 2. -/
lemma two_mem_extremalSet {n : ℕ} (hn : n ≥ 2) : 2 ∈ ExtremalSet n := by
  unfold ExtremalSet
  simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range]
  exact ⟨1, ⟨by omega, Or.inl (by norm_num)⟩, by omega⟩

/-- 3 is in ExtremalSet n for n ≥ 3. -/
lemma three_mem_extremalSet {n : ℕ} (hn : n ≥ 3) : 3 ∈ ExtremalSet n := by
  unfold ExtremalSet
  simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range]
  exact ⟨2, ⟨by omega, Or.inr (by norm_num)⟩, by omega⟩

/-- 6 is in ExtremalSet n for n ≥ 6. -/
lemma six_mem_extremalSet {n : ℕ} (hn : n ≥ 6) : 6 ∈ ExtremalSet n := by
  unfold ExtremalSet
  simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range]
  exact ⟨5, ⟨by omega, Or.inl (by norm_num)⟩, by omega⟩

/-- ExtremalSet and R15 partition [1..n]: every a ∈ [1..n] is in one or the other. -/
lemma extremal_or_r15 {a n : ℕ} (ha1 : 1 ≤ a) (han : a ≤ n) :
    a ∈ ExtremalSet n ∨ a ∈ R15 n := by
  -- a is either divisible by 2 or 3 (ExtremalSet), or coprime to 6 (R15)
  by_cases h26 : Nat.gcd a 6 = 1
  · right
    unfold R15
    simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range]
    exact ⟨a - 1, ⟨by omega, by omega⟩, by omega⟩
  · left
    unfold ExtremalSet
    simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range]
    refine ⟨a - 1, ⟨by omega, ?_⟩, by omega⟩
    -- ¬gcd(a,6)=1 means 2∣a or 3∣a, i.e., a%2=0 or a%3=0
    by_contra h_neither
    push_neg at h_neither
    apply h26
    have hcop2 : Nat.Coprime a 2 := by omega
    have hcop3 : Nat.Coprime a 3 := by omega
    calc Nat.gcd a 6 = Nat.gcd a (2 * 3) := by norm_num
    _ = 1 := Nat.Coprime.mul_right hcop2 hcop3

/-- Elements of ExtremalSet are divisible by 2 or 3. -/
private lemma mem_extremalSet_dvd {a n : ℕ} (ha : a ∈ ExtremalSet n) : 2 ∣ a ∨ 3 ∣ a := by
  unfold ExtremalSet at ha
  simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range] at ha
  obtain ⟨i, ⟨_, h⟩, rfl⟩ := ha
  -- h : (i + 1) % 2 = 0 ∨ (i + 1) % 3 = 0, goal : 2 ∣ (i + 1) ∨ 3 ∣ (i + 1)
  rcases h with h | h
  · left; exact Nat.dvd_of_mod_eq_zero h
  · right; exact Nat.dvd_of_mod_eq_zero h

/-- ExtremalSet and R15 are disjoint: no element is both divisible by 2 or 3 AND coprime to 6. -/
lemma extremal_r15_disjoint (n : ℕ) : Disjoint (ExtremalSet n) (R15 n) := by
  rw [Finset.disjoint_left]
  intro a haE haR
  have hdvd := mem_extremalSet_dvd haE  -- 2 ∣ a ∨ 3 ∣ a
  -- a ∈ R15 n means gcd(a, 6) = 1
  unfold R15 at haR
  simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range] at haR
  obtain ⟨i, ⟨_, hi_gcd⟩, rfl⟩ := haR
  -- hi_gcd : gcd(i+1, 6) = 1, but hdvd : 2∣(i+1) or 3∣(i+1)
  rcases hdvd with h2 | h3
  · -- 2 ∣ (i+1) contradicts gcd(i+1, 6) = 1
    have : 2 ∣ Nat.gcd (i + 1) 6 := Nat.dvd_gcd h2 (by norm_num : (2 : ℕ) ∣ 6)
    omega
  · -- 3 ∣ (i+1) contradicts gcd(i+1, 6) = 1
    have : 3 ∣ Nat.gcd (i + 1) 6 := Nat.dvd_gcd h3 (by norm_num : (3 : ℕ) ∣ 6)
    omega

/-! ## Size of Extremal Set -/

/-- The size of A*(n) equals ⌊n/2⌋ + ⌊n/3⌋ - ⌊n/6⌋ (inclusion-exclusion). -/
theorem extremalSet_card (n : ℕ) :
    (ExtremalSet n).card = n / 2 + n / 3 - n / 6 := by
  -- By inclusion-exclusion on multiples of 2, multiples of 3, multiples of 6
  -- |{2|i}| = ⌊n/2⌋, |{3|i}| = ⌊n/3⌋, |{6|i}| = ⌊n/6⌋
  sorry -- Requires careful finset arithmetic with filters

/-- Approximation: |A*(n)| ≈ 2n/3 (within 2 of 2n/3). -/
theorem extremalSet_approx (n : ℕ) (hn : n ≥ 6) :
    3 * (ExtremalSet n).card ≤ 2 * n + 3 ∧ 2 * n ≤ 3 * (ExtremalSet n).card + 3 := by
  sorry

/-! ## Key Structural Lemmas -/

/-- Elements coprime to 6 are coprime to both 2 and 3. -/
lemma coprimeTo6_coprime_2 {a : ℕ} (ha : CoprimeTo6 a) : Coprime a 2 := by
  unfold CoprimeTo6 at ha
  unfold Coprime
  -- gcd(a, 6) = 1 implies gcd(a, 2) = 1 since 2 | 6
  -- Proof: gcd(a,2) | a and gcd(a,2) | 2 | 6, so gcd(a,2) | gcd(a,6) = 1
  exact Nat.Coprime.coprime_dvd_right (show 2 ∣ 6 by norm_num) ha

lemma coprimeTo6_coprime_3 {a : ℕ} (ha : CoprimeTo6 a) : Coprime a 3 := by
  unfold CoprimeTo6 at ha
  unfold Coprime
  exact Nat.Coprime.coprime_dvd_right (show 3 ∣ 6 by norm_num) ha

/-- 2 and 3 are coprime. -/
lemma coprime_2_3 : Coprime 2 3 := by
  unfold Coprime
  native_decide

/-- If x is coprime to 6, then {x, 2, 3} is a coprime triple. -/
lemma triple_from_coprime6 {x : ℕ} (hx : CoprimeTo6 x) (hx2 : x ≠ 2) (hx3 : x ≠ 3) :
    IsCopTriple x 2 3 := by
  unfold IsCopTriple
  exact ⟨coprimeTo6_coprime_2 hx, coprimeTo6_coprime_3 hx, coprime_2_3⟩

/-- Any set exceeding |A*| must intersect R₁ ∪ R₅. -/
lemma exceeds_extremal_has_coprime6 {A : Finset ℕ} {n : ℕ}
    (hAn : ∀ a ∈ A, a ≤ n)
    (hsize : (ExtremalSet n).card < A.card) :
    ∃ x ∈ A, CoprimeTo6 x := by
  -- If every element of A were in ExtremalSet n, then |A| ≤ |A*|, contradiction.
  by_contra h
  push_neg at h
  -- h : ∀ x ∈ A, ¬CoprimeTo6 x
  -- Every element of A is NOT coprime to 6, meaning 2∣x or 3∣x
  -- Such elements are exactly ExtremalSet n (among [1..n])
  -- So A ⊆ ExtremalSet n, giving |A| ≤ |ExtremalSet n|
  have hle : A.card ≤ (ExtremalSet n).card := by
    apply Finset.card_le_card
    intro a haA
    -- a ∈ A, ¬CoprimeTo6 a means gcd(a, 6) ≠ 1, so 2∣a or 3∣a
    have hncop := h a haA
    unfold CoprimeTo6 at hncop
    -- a ≤ n from hAn, and (2∣a or 3∣a) means a ∈ ExtremalSet n
    unfold ExtremalSet
    simp only [Finset.mem_image, Finset.mem_filter, Finset.mem_range]
    have ha_le := hAn a haA
    -- a = (a - 1) + 1, and a - 1 < n
    refine ⟨a - 1, ⟨by omega, ?_⟩, by omega⟩
    -- Need: (a - 1 + 1) % 2 = 0 ∨ (a - 1 + 1) % 3 = 0, i.e., a % 2 = 0 ∨ a % 3 = 0
    -- From ¬(gcd a 6 = 1), we get 2∣a or 3∣a
    by_contra h_neither
    push_neg at h_neither
    obtain ⟨h2, h3⟩ := h_neither
    -- a % 2 ≠ 0 and a % 3 ≠ 0 means gcd(a, 2) = 1 and gcd(a, 3) = 1
    -- hence gcd(a, 6) = 1, contradicting hncop
    apply hncop
    have : Nat.gcd a 2 = 1 := by omega
    have : Nat.gcd a 3 = 1 := by omega
    -- gcd(a,6) = 1 from gcd(a,2) = 1 ∧ gcd(a,3) = 1
    have hcop2 : Nat.Coprime a 2 := by omega
    have hcop3 : Nat.Coprime a 3 := by omega
    show Nat.gcd a 6 = 1
    calc Nat.gcd a 6 = Nat.gcd a (2 * 3) := by norm_num
    _ = 1 := Nat.Coprime.mul_right hcop2 hcop3
  omega

/-! ## Main Theorem: Case Analysis -/

/-- Case A: If 2, 3 ∈ A and A has an element coprime to 6, then A has a coprime triple. -/
theorem case_A {A : Finset ℕ} (h2 : 2 ∈ A) (h3 : 3 ∈ A)
    (hx : ∃ x ∈ A, CoprimeTo6 x ∧ x ≠ 2 ∧ x ≠ 3) :
    HasCopTriple A := by
  obtain ⟨x, hxA, hxcop, hx2, hx3⟩ := hx
  refine ⟨x, 2, 3, hxA, h2, h3, hx2, hx3, ?_, triple_from_coprime6 hxcop hx2 hx3⟩
  -- 2 ≠ 3
  omega

/-- Case B1/C1: If 1 ∈ A and A has two other elements, then {1, a, b} with gcd(a,b)=1. -/
theorem case_with_1 {A : Finset ℕ} (h1 : 1 ∈ A)
    (hab : ∃ a b, a ∈ A ∧ b ∈ A ∧ a ≠ 1 ∧ b ≠ 1 ∧ a ≠ b ∧ Coprime a b) :
    HasCopTriple A := by
  obtain ⟨a, b, haA, hbA, ha1, hb1, hab_ne, hab_cop⟩ := hab
  refine ⟨1, a, b, h1, haA, hbA, ?_, ?_, hab_ne, ?_⟩
  · exact Ne.symm ha1
  · exact Ne.symm hb1
  · unfold IsCopTriple Coprime
    exact ⟨by simp [Nat.gcd_comm], by simp [Nat.gcd_comm], hab_cop⟩

/-- Case B3/C3: If 2 ∉ A (or 3 ∉ A) and |A ∩ R₁₅| ≤ 1, then |A| ≤ |A*|. -/
theorem case_impossible {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 2)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (h_not_2 : 2 ∉ A)
    (h_r15 : (A ∩ R15 n).card ≤ 1) :
    A.card ≤ (ExtremalSet n).card := by
  -- Every a ∈ A with 1 ≤ a ≤ n is in ExtremalSet n or R15 n (by extremal_or_r15).
  -- So A ⊆ (A ∩ ExtremalSet n) ∪ (A ∩ R15 n), and these are disjoint.
  -- |A ∩ ExtremalSet n| ≤ |ExtremalSet n \ {2}| = |ExtremalSet n| - 1  (since 2 ∈ A* but 2 ∉ A)
  -- |A| = |A ∩ A*| + |A ∩ R₁₅| ≤ (|A*| - 1) + 1 = |A*|
  have h_partition : ∀ a ∈ A, a ∈ ExtremalSet n ∨ a ∈ R15 n := by
    intro a ha; exact extremal_or_r15 (hAn a ha).1 (hAn a ha).2
  -- A ∩ ExtremalSet n ⊆ ExtremalSet n \ {2}
  have h_sub : A ∩ ExtremalSet n ⊆ ExtremalSet n \ {2} := by
    intro a ha
    simp only [mem_inter, mem_sdiff, mem_singleton] at ha ⊢
    refine ⟨ha.2, ?_⟩
    intro h_eq; subst h_eq; exact h_not_2 ha.1
  -- |A ∩ A*| ≤ |A*| - 1
  have h2_mem : 2 ∈ ExtremalSet n := two_mem_extremalSet hn
  have h_card_inter : (A ∩ ExtremalSet n).card ≤ (ExtremalSet n).card - 1 := by
    calc (A ∩ ExtremalSet n).card
        ≤ (ExtremalSet n \ {2}).card := Finset.card_le_card h_sub
      _ = (ExtremalSet n).card - 1 := by
          rw [card_sdiff_singleton h2_mem]  -- Finset.card_erase_of_mem variant
  -- |A| ≤ |A ∩ A*| + |A ∩ R₁₅| (partition)
  have h_le : A.card ≤ (A ∩ ExtremalSet n).card + (A ∩ R15 n).card := by
    -- Every element of A is in one of the two intersections
    calc A.card ≤ (A ∩ ExtremalSet n ∪ A ∩ R15 n).card := by
            apply Finset.card_le_card
            intro a ha
            rcases h_partition a ha with h | h
            · exact mem_union_left _ (mem_inter.mpr ⟨ha, h⟩)
            · exact mem_union_right _ (mem_inter.mpr ⟨ha, h⟩)
      _ ≤ (A ∩ ExtremalSet n).card + (A ∩ R15 n).card := card_union_le _ _
  -- Combine: |A| ≤ (|A*| - 1) + 1 = |A*|
  omega

/-- Case B3/C3 symmetric: If 3 ∉ A and |A ∩ R₁₅| ≤ 1, then |A| ≤ |A*|.
    Same proof structure as case_impossible, using 3 ∈ ExtremalSet instead of 2. -/
theorem case_impossible_3 {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 3)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (h_not_3 : 3 ∉ A)
    (h_r15 : (A ∩ R15 n).card ≤ 1) :
    A.card ≤ (ExtremalSet n).card := by
  have h_partition : ∀ a ∈ A, a ∈ ExtremalSet n ∨ a ∈ R15 n := by
    intro a ha; exact extremal_or_r15 (hAn a ha).1 (hAn a ha).2
  have h_sub : A ∩ ExtremalSet n ⊆ ExtremalSet n \ {3} := by
    intro a ha
    simp only [mem_inter, mem_sdiff, mem_singleton] at ha ⊢
    refine ⟨ha.2, ?_⟩
    intro h_eq; subst h_eq; exact h_not_3 ha.1
  have h3_mem : 3 ∈ ExtremalSet n := three_mem_extremalSet hn
  have h_card_inter : (A ∩ ExtremalSet n).card ≤ (ExtremalSet n).card - 1 := by
    calc (A ∩ ExtremalSet n).card
        ≤ (ExtremalSet n \ {3}).card := Finset.card_le_card h_sub
      _ = (ExtremalSet n).card - 1 := by
          rw [card_sdiff_singleton h3_mem]
  have h_le : A.card ≤ (A ∩ ExtremalSet n).card + (A ∩ R15 n).card := by
    calc A.card ≤ (A ∩ ExtremalSet n ∪ A ∩ R15 n).card := by
            apply Finset.card_le_card
            intro a ha
            rcases h_partition a ha with h | h
            · exact mem_union_left _ (mem_inter.mpr ⟨ha, h⟩)
            · exact mem_union_right _ (mem_inter.mpr ⟨ha, h⟩)
      _ ≤ (A ∩ ExtremalSet n).card + (A ∩ R15 n).card := card_union_le _ _
  omega

/-- Case D: If 2 ∉ A and 3 ∉ A, then |A ∩ R₁₅| ≥ 3 (for |A| > |A*|). -/
theorem case_D_needs_three {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 3)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (h_not_2 : 2 ∉ A) (h_not_3 : 3 ∉ A)
    (hsize : (ExtremalSet n).card < A.card) :
    3 ≤ (A ∩ R15 n).card := by
  -- Partition: every a ∈ A is in ExtremalSet n or R15 n
  have h_partition : ∀ a ∈ A, a ∈ ExtremalSet n ∨ a ∈ R15 n := by
    intro a ha; exact extremal_or_r15 (hAn a ha).1 (hAn a ha).2
  -- A ∩ ExtremalSet n ⊆ ExtremalSet n \ {2, 3}
  have h_sub : A ∩ ExtremalSet n ⊆ ExtremalSet n \ {2, 3} := by
    intro a ha
    simp only [mem_inter, mem_sdiff, mem_insert, mem_singleton] at ha ⊢
    refine ⟨ha.2, ?_⟩
    push_neg
    exact ⟨fun h_eq => by subst h_eq; exact h_not_2 ha.1,
           fun h_eq => by subst h_eq; exact h_not_3 ha.1⟩
  -- 2, 3 ∈ ExtremalSet n and 2 ≠ 3
  have h2_mem : 2 ∈ ExtremalSet n := two_mem_extremalSet (by omega)
  have h3_mem : 3 ∈ ExtremalSet n := three_mem_extremalSet hn
  -- {2, 3} ⊆ ExtremalSet n
  have h23_sub : ({2, 3} : Finset ℕ) ⊆ ExtremalSet n := by
    intro x hx
    simp only [mem_insert, mem_singleton] at hx
    rcases hx with rfl | rfl
    · exact h2_mem
    · exact h3_mem
  -- |A ∩ A*| ≤ |A*| - 2
  have h_card_inter : (A ∩ ExtremalSet n).card ≤ (ExtremalSet n).card - 2 := by
    calc (A ∩ ExtremalSet n).card
        ≤ (ExtremalSet n \ {2, 3}).card := Finset.card_le_card h_sub
      _ = (ExtremalSet n).card - ({2, 3} : Finset ℕ).card := by
          rw [Finset.card_sdiff h23_sub]
      _ = (ExtremalSet n).card - 2 := by
          -- |{2, 3}| = 2 since 2 ≠ 3
          norm_num
  -- |A| ≤ |A ∩ A*| + |A ∩ R₁₅| by partition
  have h_le : A.card ≤ (A ∩ ExtremalSet n).card + (A ∩ R15 n).card := by
    calc A.card ≤ (A ∩ ExtremalSet n ∪ A ∩ R15 n).card := by
            apply Finset.card_le_card
            intro a ha
            rcases h_partition a ha with h | h
            · exact mem_union_left _ (mem_inter.mpr ⟨ha, h⟩)
            · exact mem_union_right _ (mem_inter.mpr ⟨ha, h⟩)
      _ ≤ (A ∩ ExtremalSet n).card + (A ∩ R15 n).card := card_union_le _ _
  -- Combine: |A| > |A*| and |A ∩ A*| ≤ |A*| - 2 gives |A ∩ R₁₅| ≥ 3
  omega

/-- Density argument: among elements coprime to 6 with prime factors ≥ 5,
    the density of elements sharing a prime p ≥ 5 with a given x is ≤ 1/5.
    So for |A| > 2n/3, A contains an element coprime to any given x coprime to 6. -/
lemma density_coprime_exists {A : Finset ℕ} {n : ℕ} {x : ℕ}
    (hAn : ∀ a ∈ A, a ≤ n)
    (hsize : 2 * n < 3 * A.card)
    (hx : CoprimeTo6 x) (hx_pos : 0 < x) :
    ∃ z ∈ A, z ≠ x ∧ Coprime z x := by
  -- Elements not coprime to x: at most n/5 + n/7 + ... ≤ n/4
  -- Elements coprime to x: at least 3n/4
  -- Since |A| > 2n/3 > n/2, A contains such an element
  sorry

/-! ## Main Theorem -/

/-- **Problem #883 (Triangle Case)**: If A ⊆ [n] with |A| > |A*(n)|,
    then G(A) contains a triangle. -/
theorem erdos883_triangle {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 15)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (hsize : (ExtremalSet n).card < A.card) :
    HasCopTriple A := by
  -- Step 1: Get x ∈ A coprime to 6
  have hAn' : ∀ a ∈ A, a ≤ n := fun a ha => (hAn a ha).2
  obtain ⟨x, hxA, hx_cop⟩ := exceeds_extremal_has_coprime6 hAn' hsize
  -- x ≠ 2 and x ≠ 3 (since gcd(2,6) = 2 ≠ 1 and gcd(3,6) = 3 ≠ 1)
  have hx2 : x ≠ 2 := by
    intro h; subst h; unfold CoprimeTo6 at hx_cop; norm_num at hx_cop
  have hx3 : x ≠ 3 := by
    intro h; subst h; unfold CoprimeTo6 at hx_cop; norm_num at hx_cop
  -- Step 2: Case split on 2 ∈ A, 3 ∈ A
  by_cases h2 : 2 ∈ A
  · by_cases h3 : 3 ∈ A
    · -- **Case A**: 2, 3 ∈ A → {x, 2, 3} is a coprime triple
      exact case_A h2 h3 ⟨x, hxA, hx_cop, hx2, hx3⟩
    · -- **Case B**: 2 ∈ A, 3 ∉ A
      by_cases h1 : 1 ∈ A
      · -- Sub-case B1: 1 ∈ A
        -- x coprime to 6, so gcd(x, 2) = 1 (Coprime x 2)
        have hcop_x2 : Coprime x 2 := coprimeTo6_coprime_2 hx_cop
        -- If x ≠ 1: {1, 2, x} is a coprime triple
        by_cases hx1 : x = 1
        · -- x = 1. Need another element from R15.
          -- |A ∩ R15| ≥ 2, or contradiction via case_impossible_3
          by_cases hr15 : (A ∩ R15 n).card ≤ 1
          · -- |A ∩ R15| ≤ 1 → |A| ≤ |A*| by case_impossible_3, contradicting hsize
            have := case_impossible_3 (by omega : n ≥ 3) hAn h3 hr15
            omega
          · -- |A ∩ R15| ≥ 2 → get y ∈ A ∩ R15, y ≠ 1
            push_neg at hr15
            -- Two distinct elements in A ∩ R15
            have h1lt : 1 < (A ∩ R15 n).card := by omega
            rw [Finset.one_lt_card] at h1lt
            obtain ⟨a, haAR, b, hbAR, hab⟩ := h1lt
            -- At least one is ≠ 1
            have ⟨y, hyAR, hy1⟩ : ∃ y ∈ A ∩ R15 n, y ≠ 1 := by
              by_cases ha1 : a = 1
              · exact ⟨b, hbAR, by omega⟩
              · exact ⟨a, haAR, ha1⟩
            have hyA : y ∈ A := (mem_inter.mp hyAR).1
            have hyR15 : y ∈ R15 n := (mem_inter.mp hyAR).2
            -- y coprime to 6 (from R15 membership)
            have hy_cop : CoprimeTo6 y := by
              unfold R15 at hyR15
              simp only [mem_image, mem_filter, mem_range] at hyR15
              obtain ⟨i, ⟨_, hi_gcd⟩, rfl⟩ := hyR15
              unfold CoprimeTo6; exact hi_gcd
            -- y ≠ 2 (gcd(2,6) ≠ 1)
            have hy2 : y ≠ 2 := by
              intro h; subst h; unfold CoprimeTo6 at hy_cop; norm_num at hy_cop
            -- {1, 2, y} via case_with_1
            exact case_with_1 h1 ⟨2, y, h2, hyA, by omega, Ne.symm hy1,
              hy2.symm, by rw [Nat.gcd_comm]; exact coprimeTo6_coprime_2 hy_cop⟩
        · -- x ≠ 1: {1, 2, x} via case_with_1
          exact case_with_1 h1 ⟨2, x, h2, hxA, by omega, Ne.symm hx1,
            hx2.symm, by rw [Nat.gcd_comm]; exact hcop_x2⟩
      · -- Sub-case B2: 1 ∉ A, 2 ∈ A, 3 ∉ A
        -- Need density argument to find coprime pair in R15
        sorry -- Requires density_coprime_exists
  · by_cases h3 : 3 ∈ A
    · -- **Case C**: 2 ∉ A, 3 ∈ A (symmetric to Case B)
      by_cases h1 : 1 ∈ A
      · -- Sub-case C1: 1 ∈ A
        have hcop_x3 : Coprime x 3 := coprimeTo6_coprime_3 hx_cop
        by_cases hx1 : x = 1
        · -- x = 1. Need another element from R15.
          by_cases hr15 : (A ∩ R15 n).card ≤ 1
          · have := case_impossible (by omega : n ≥ 2) hAn h2 hr15
            omega
          · -- |A ∩ R15| ≥ 2 → get y ∈ A ∩ R15, y ≠ 1 (symmetric to Case B)
            push_neg at hr15
            have h1lt : 1 < (A ∩ R15 n).card := by omega
            rw [Finset.one_lt_card] at h1lt
            obtain ⟨a, haAR, b, hbAR, hab⟩ := h1lt
            have ⟨y, hyAR, hy1⟩ : ∃ y ∈ A ∩ R15 n, y ≠ 1 := by
              by_cases ha1 : a = 1
              · exact ⟨b, hbAR, by omega⟩
              · exact ⟨a, haAR, ha1⟩
            have hyA : y ∈ A := (mem_inter.mp hyAR).1
            have hyR15 : y ∈ R15 n := (mem_inter.mp hyAR).2
            have hy_cop : CoprimeTo6 y := by
              unfold R15 at hyR15
              simp only [mem_image, mem_filter, mem_range] at hyR15
              obtain ⟨i, ⟨_, hi_gcd⟩, rfl⟩ := hyR15
              unfold CoprimeTo6; exact hi_gcd
            have hy3 : y ≠ 3 := by
              intro h; subst h; unfold CoprimeTo6 at hy_cop; norm_num at hy_cop
            -- {1, 3, y} via case_with_1
            exact case_with_1 h1 ⟨3, y, h3, hyA, by omega, Ne.symm hy1,
              hy3.symm, by rw [Nat.gcd_comm]; exact coprimeTo6_coprime_3 hy_cop⟩
        · -- x ≠ 1: {1, 3, x} via case_with_1
          exact case_with_1 h1 ⟨3, x, h3, hxA, by omega, Ne.symm hx1,
            hx3.symm, by rw [Nat.gcd_comm]; exact hcop_x3⟩
      · -- Sub-case C2: 1 ∉ A, 2 ∉ A, 3 ∈ A
        sorry -- Requires density_coprime_exists
    · -- **Case D**: 2 ∉ A, 3 ∉ A
      -- ≥3 elements in R15 by case_D_needs_three
      have h3r15 := case_D_needs_three (by omega : n ≥ 3) hAn h2 h3 hsize
      -- Need density argument among R15 elements to find coprime triple
      sorry -- Requires density_coprime_exists for coprime pair in R15

/-- Small cases: verified computationally for n = 3,...,14. -/
theorem erdos883_small (n : ℕ) (hn : 3 ≤ n) (hn' : n < 15)
    {A : Finset ℕ}
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (hsize : (ExtremalSet n).card < A.card) :
    HasCopTriple A := by
  -- Verified by exhaustive computation in src/verify_883.py
  -- Each n from 3 to 14 checked over all subsets of required size
  sorry -- Computational verification (see src/verify_883.py)

/-- **Main Theorem**: Problem #883 holds for all n ≥ 3. -/
theorem erdos883 {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 3)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (hsize : (ExtremalSet n).card < A.card) :
    HasCopTriple A := by
  by_cases h15 : n ≥ 15
  · exact erdos883_triangle h15 hAn hsize
  · have : n < 15 := by omega
    exact erdos883_small n hn this hAn hsize

/-! ## Extremal Set Properties -/

/-- A*(n) is triangle-free in the coprime graph.
    Proof: every element is div by 2 or 3. By pigeonhole on 3 elements and 2 types,
    at least two share a type ⟹ gcd ≥ 2 or 3 ⟹ not coprime. -/
theorem extremalSet_triangle_free (n : ℕ) (hn : n ≥ 6) :
    ¬HasCopTriple (ExtremalSet n) := by
  intro ⟨a, b, c, haA, hbA, hcA, _, _, _, ⟨hab_cop, hac_cop, hbc_cop⟩⟩
  unfold Coprime at hab_cop hac_cop hbc_cop
  -- Each element satisfies 2 ∣ x or 3 ∣ x
  have ha := mem_extremalSet_dvd haA
  have hb := mem_extremalSet_dvd hbA
  have hc := mem_extremalSet_dvd hcA
  -- Pigeonhole: 3 elements classified into {div by 2, div by 3}.
  -- At least 2 share a type, giving gcd ≥ 2 or ≥ 3, contradicting gcd = 1.
  rcases ha with ha | ha <;> rcases hb with hb | hb <;> rcases hc with hc | hc
  -- 8 cases, each closed by finding a same-type pair
  · -- 2∣a, 2∣b, 2∣c → gcd(a,b) ≥ 2
    obtain ⟨k, hk⟩ := Nat.dvd_gcd ha hb; rw [hab_cop] at hk; omega
  · -- 2∣a, 2∣b, 3∣c → gcd(a,b) ≥ 2
    obtain ⟨k, hk⟩ := Nat.dvd_gcd ha hb; rw [hab_cop] at hk; omega
  · -- 2∣a, 3∣b, 2∣c → gcd(a,c) ≥ 2
    obtain ⟨k, hk⟩ := Nat.dvd_gcd ha hc; rw [hac_cop] at hk; omega
  · -- 2∣a, 3∣b, 3∣c → gcd(b,c) ≥ 3
    obtain ⟨k, hk⟩ := Nat.dvd_gcd hb hc; rw [hbc_cop] at hk; omega
  · -- 3∣a, 2∣b, 2∣c → gcd(b,c) ≥ 2
    obtain ⟨k, hk⟩ := Nat.dvd_gcd hb hc; rw [hbc_cop] at hk; omega
  · -- 3∣a, 2∣b, 3∣c → gcd(a,c) ≥ 3
    obtain ⟨k, hk⟩ := Nat.dvd_gcd ha hc; rw [hac_cop] at hk; omega
  · -- 3∣a, 3∣b, 2∣c → gcd(a,b) ≥ 3
    obtain ⟨k, hk⟩ := Nat.dvd_gcd ha hb; rw [hab_cop] at hk; omega
  · -- 3∣a, 3∣b, 3∣c → gcd(a,b) ≥ 3
    obtain ⟨k, hk⟩ := Nat.dvd_gcd ha hb; rw [hab_cop] at hk; omega

/-- A*(n) achieves the maximum size among triangle-free sets (tightness). -/
theorem extremalSet_maximal (n : ℕ) (hn : n ≥ 6)
    {B : Finset ℕ}
    (hBn : ∀ b ∈ B, 1 ≤ b ∧ b ≤ n)
    (hBtf : ¬HasCopTriple B) :
    B.card ≤ (ExtremalSet n).card := by
  -- Contrapositive of erdos883
  by_contra h
  push_neg at h
  have : HasCopTriple B := erdos883 (by omega) hBn h
  exact hBtf this

/-! ## Extension: Non-Bipartiteness -/

/-- A triangle implies the coprime graph is non-bipartite. -/
theorem triangle_implies_non_bipartite {A : Finset ℕ} (ht : HasCopTriple A) :
    ¬∃ (f : ℕ → Bool), ∀ a b, a ∈ A → b ∈ A → Coprime a b → a ≠ b → f a ≠ f b := by
  -- A triangle is an odd cycle (length 3), which cannot be 2-colored
  obtain ⟨a, b, c, haA, hbA, hcA, hab, hac, hbc, ⟨hab_cop, hac_cop, hbc_cop⟩⟩ := ht
  intro ⟨f, hf⟩
  -- f(a) ≠ f(b), f(a) ≠ f(c), f(b) ≠ f(c)
  have h1 : f a ≠ f b := hf a b haA hbA hab_cop hab
  have h2 : f a ≠ f c := hf a c haA hcA hac_cop hac
  have h3 : f b ≠ f c := hf b c hbA hcA hbc_cop hbc
  -- But Bool has only two values, so we can't have all three distinct
  cases ha : f a <;> cases hb : f b <;> cases hc : f c <;> simp_all

/-- **Corollary**: For |A| > |A*|, the coprime graph on A is non-bipartite. -/
theorem erdos883_non_bipartite {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 3)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (hsize : (ExtremalSet n).card < A.card) :
    ¬∃ (f : ℕ → Bool), ∀ a b, a ∈ A → b ∈ A → Coprime a b → a ≠ b → f a ≠ f b :=
  triangle_implies_non_bipartite (erdos883 hn hAn hsize)

/-! ## Extension to Full Cycle Spectrum (Partial) -/

/- WARNING: This is an UNPROVED AXIOM, not a theorem.
   It is used only by erdos883_pancyclic_large below, which is a stub (concludes True).
   This axiom does NOT affect the triangle-forcing results above. -/
/-- **Bondy's Theorem** (stated, not proved): If G has > m²/4 edges, then G
    contains cycles of all lengths from 3 to m. -/
axiom bondys_theorem {G : SimpleGraph (Fin m)}
    (hedge : G.edgeFinset.card > m * m / 4) :
    ∀ ℓ, 3 ≤ ℓ → ℓ ≤ m → ∃ (cycle : List (Fin m)), cycle.length = ℓ -- simplified

/-- **Partial Result**: For |A| ≥ 0.9n, the coprime graph contains all cycle lengths.

    Proof sketch: coprime density ≈ 6/π² ≈ 0.608 > 1/2 for the full set,
    and for |A| ≥ 0.9n the density remains > 1/2.
    Then edges > m²/4 and Bondy's theorem applies. -/
/- STUB: This "theorem" concludes True and proves nothing.
   It is a placeholder for future work on the full pancyclicity result. -/
theorem erdos883_pancyclic_large {A : Finset ℕ} {n : ℕ}
    (hn : n ≥ 100)
    (hAn : ∀ a ∈ A, 1 ≤ a ∧ a ≤ n)
    (hsize : 9 * n ≤ 10 * A.card) :
    ∀ ℓ, 3 ≤ ℓ → ℓ ≤ A.card →
      True := by  -- Placeholder: actual statement would assert cycle existence
  intro ℓ _ _; trivial

/-! ## Summary of Proof Status

| Component | Status | Proof Method |
|-----------|--------|-------------|
| `coprime_2_3` | PROVED | native_decide |
| `triple_from_coprime6` | PROVED | Direct construction |
| `case_A` | PROVED | Applies triple_from_coprime6 |
| `case_with_1` | PROVED | gcd(1, x) = 1 |
| `triangle_implies_non_bipartite` | PROVED | Bool pigeonhole |
| `coprimeTo6_coprime_2` | PROVED | Nat.Coprime.coprime_dvd_right |
| `coprimeTo6_coprime_3` | PROVED | Nat.Coprime.coprime_dvd_right |
| `mem_extremalSet_dvd` | PROVED | unfold + Nat.dvd_of_mod_eq_zero |
| `extremalSet_triangle_free` | PROVED | Pigeonhole: 8-way case + dvd_gcd + omega |
| `two_mem_extremalSet` | PROVED | Direct construction (i=1) |
| `three_mem_extremalSet` | PROVED | Direct construction (i=2) |
| `six_mem_extremalSet` | PROVED | Direct construction (i=5) |
| `extremal_or_r15` | PROVED | By cases on gcd(a,6)=1, Coprime.mul_right |
| `extremal_r15_disjoint` | PROVED | dvd_gcd contradiction |
| `exceeds_extremal_has_coprime6` | PROVED | by_contra + subset + Coprime.mul_right |
| `case_impossible` | PROVED | Partition + card_sdiff_singleton + omega |
| `case_impossible_3` | PROVED | Symmetric to case_impossible (3 ∉ A) |
| `case_D_needs_three` | PROVED | Partition + card_sdiff + omega |
| `extremalSet_maximal` | PARTIAL (depends on sorry) | Contrapositive of erdos883 |
| `erdos883_non_bipartite` | PARTIAL (depends on sorry) | triangle_implies_non_bipartite + erdos883 |
| `erdos883` | PARTIAL (depends on sorry) | Delegates to erdos883_triangle + erdos883_small |
| `erdos883_triangle` | PARTIAL | Case A proved; B1/C1 with x≠1 proved; 3 sorry branches |
| `extremalSet_card` | sorry | Finset inclusion-exclusion |
| `extremalSet_approx` | sorry | Follows from extremalSet_card |
| `density_coprime_exists` | sorry | Analytic estimate (density of multiples) |
| `erdos883_small` | sorry | Computational (verified in Python) |
| `bondys_theorem` | AXIOM | Unproved; only used by pancyclic stub |
| `erdos883_pancyclic_large` | STUB | Concludes True; placeholder only |

**Score**: 17 fully proved, 7 sorry (4 standalone + 3 inside erdos883_triangle), 1 axiom

The 3 sorry branches in erdos883_triangle all reduce to `density_coprime_exists`:
- Case B/C with 1 ∉ A: needs density argument for coprime pair
- Case D: needs density argument for coprime pair among ≥3 R15 elements

The density_coprime_exists is the single remaining mathematical gap.
Note: `extremalSet_maximal`, `erdos883_non_bipartite`, and `erdos883` are marked PARTIAL
because they transitively depend on sorry through erdos883_triangle and erdos883_small.
-/

end Erdos883
