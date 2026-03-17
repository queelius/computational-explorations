/-
# NPG-15: Schur Numbers in Abelian Groups

## Problem Statement
For a finite abelian group G, define the Schur number S(G, k) as the minimum
|A| such that every k-coloring of A ⊆ G has a monochromatic Schur triple
(a + b = c with a, b, c same color).

## Key Questions
1. How does S(G, k) depend on the group structure?
2. Is S(ℤ/nℤ, k) = Θ(S(k) mod n) for large n?
3. For which groups is S(G, 2) = |G|? (Every element is in a Schur triple)

## Novelty
This extends classical Schur numbers to arbitrary groups, connecting
additive combinatorics with group theory.
-/

import Mathlib.Algebra.Group.Defs
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Data.Fin.Basic
import Mathlib.GroupTheory.Subgroup.Basic
import Mathlib.Tactic.Omega

open Finset

namespace NPG15

variable {G : Type*} [AddCommGroup G] [DecidableEq G]

/-! ## Basic Definitions -/

/-- A Schur triple in an additive group: three elements a, b, c with a + b = c
    and a ≤ b ≤ c (when ordered) or a, b > 0 (classical definition).
    The standard definition allows a = b but requires c distinct from a, b
    in most sources. We use the "positive" convention: a + b = c with a, b, c ∈ A
    and all positive (mapped from [N] with 1-indexing).

    For abstract groups, we use: a + b = c with a, b, c ∈ A (allowing a = b but
    note this makes {0} NOT sum-free since 0 + 0 = 0). -/
def IsSchurTriple (a b c : G) : Prop := a + b = c

/-- A set A ⊆ G is sum-free if no a, b, c ∈ A satisfy a + b = c.
    Note: under this definition, any set containing 0 is NOT sum-free
    (since 0 + 0 = 0). This matches the standard group-theoretic convention. -/
def IsSumFree (A : Finset G) : Prop :=
  ∀ a b c, a ∈ A → b ∈ A → c ∈ A → a + b = c → False

/-- A k-coloring of a finite set. -/
def Coloring (A : Finset G) (k : ℕ) := A → Fin k

/-- Color class: elements of A assigned color i. -/
def colorClass (χ : Coloring A k) (i : Fin k) : Finset G :=
  A.filter (fun x => χ ⟨x, ·⟩ = i)

/-- A coloring is Schur-free if every color class is sum-free. -/
def IsSchurFreeColoring (A : Finset G) (k : ℕ) (χ : Coloring A k) : Prop :=
  ∀ i : Fin k, IsSumFree (colorClass χ i)

/-! ## Schur Number for Groups -/

/-- S(G, k) = minimum |A| such that no k-coloring of A is Schur-free.
    We use the contrapositive: max |A| with a Schur-free k-coloring. -/
noncomputable def schurNumber (G : Type*) [AddCommGroup G] [DecidableEq G] [Fintype G]
    (k : ℕ) : ℕ :=
  Finset.sup (Finset.univ : Finset (Finset G))
    (fun A => if (∃ χ : Coloring A k, IsSchurFreeColoring A k χ) then A.card else 0)

/-! ## Key Lemmas -/

/-- CORRECTED: {0} is NOT sum-free since 0 + 0 = 0 is a valid Schur triple.
    Previous version was mathematically incorrect. -/
lemma singleton_zero_not_sum_free : ¬IsSumFree ({0} : Finset G) := by
  intro h
  -- 0 + 0 = 0, and 0 ∈ {0}, so this is a Schur triple
  exact h 0 0 0 (mem_singleton_self 0) (mem_singleton_self 0)
    (mem_singleton_self 0) (add_zero 0)

/-- A singleton {a} with a ≠ 0 IS sum-free (since a + a = 2a ≠ a when a has
    order > 2, and a + a = 0 ∉ {a} when a has order 2). -/
lemma singleton_nonzero_sum_free {a : G} (ha : a + a ≠ a) : IsSumFree ({a} : Finset G) := by
  intro x y z hx hy hz hxyz
  simp at hx hy hz
  -- hx : x = a, hy : y = a, hz : z = a
  subst hx; subst hy; subst hz
  -- hxyz : a + a = a, which contradicts ha
  exact ha hxyz

/-- The set of elements of order > 2 is sum-free in ℤ/nℤ for certain n. -/
-- This requires more structure to state precisely

/-- CORRECTED: S(G, 1) is the max sum-free set size in G, NOT necessarily ≤ 1.
    For ℤ/nℤ with n odd, the odd residues form a sum-free set of size (n-1)/2.
    The previous claim "S(G,1) ≤ 1" was INCORRECT.

    Instead, we note: any set containing 0 has a Schur triple (0+0=0). -/
lemma zero_gives_schur_triple (A : Finset G) (h0 : (0 : G) ∈ A) : ¬IsSumFree A := by
  intro hsf
  exact hsf 0 0 0 h0 h0 h0 (add_zero 0)

/-! ## Comparison with Classical Schur -/

/-- Classical Schur number S(k) corresponds to schurNumber ℤ k restricted to [n]. -/
-- S(2) = 4, S(3) = 13, S(4) = 44, S(5) = 160

/-- In ℤ/nℤ, the Schur structure depends on n's factorization. -/
-- For n = 2m + 1 (odd), odd residues form sum-free set of size m

/-! ## Novel Questions -/

/-- Q1: For which groups G is every 2-coloring of G forced to have a Schur triple? -/
def hasUniversalSchur (G : Type*) [AddCommGroup G] [DecidableEq G] [Fintype G] : Prop :=
  ∀ χ : G → Fin 2, ∃ a b c : G, a + b = c ∧ χ a = χ b ∧ χ b = χ c

/-- Q2: Is there a group-theoretic characterization of max sum-free set size? -/
-- Conjecture: Related to number of elements of order 2

/-- Q3: How does Schur number scale with group exponent? -/
-- For cyclic groups ℤ/nℤ, the odd numbers {1, 3, 5, ..., n-2} form sum-free set
-- of size (n-1)/2 when n is odd

/-! ## Computational Observations -/

/-- In ℤ/6ℤ:
    - Odd elements {1, 3, 5} are sum-free (size 3)
    - {2, 4} is sum-free (size 2)
    - Maximum sum-free: {1, 5} or {1, 3, 5} depending on interpretation

    Key: 1 + 5 = 6 ≡ 0 ∉ {1, 3, 5} ✓
         3 + 3 = 6 ≡ 0 ∉ {1, 3, 5} ✓
         1 + 3 = 4 ∉ {1, 3, 5} ✓ (wait, 4 is even)
         Actually need to check: 1 + 3 = 4, 3 + 5 = 8 ≡ 2, 1 + 5 = 6 ≡ 0
         None of 0, 2, 4 are in {1, 3, 5}, so it's sum-free!
-/

/-! ## Connection to Problem #483 -/

/-- Problem #483 asks: Is S(k) < c^k for some constant c?

    NPG-15 generalizes: For which groups G is S(G, k) < c^k · f(G)?

    Hypothesis: The answer depends on the group's structure:
    - Cyclic groups: similar to ℤ (exponential in k)
    - Groups with many involutions: potentially different behavior
-/

/-! ## Proved Theorems -/

/-! ### Boolean Group Theory

A "boolean group" is one where every element has order ≤ 2, i.e., a + a = 0.
Examples: (ℤ/2ℤ)^n. Key property: a + a = 0 ⟹ a = -a, so a + b = c ⟺ b + a = c ⟺ a = c - b.
-/

/-- In a boolean group (a + a = 0 for all a), sum-free sets avoid 0.
    Proof: 0 + 0 = 0 is a Schur triple. -/
lemma boolean_sum_free_avoids_zero
    (hbool : ∀ g : G, g + g = 0)
    (A : Finset G) (hsf : IsSumFree A) :
    (0 : G) ∉ A := by
  -- This follows directly from zero_gives_schur_triple
  intro h0
  exact zero_gives_schur_triple A h0 hsf

/-- In a boolean group, -a = a (every element is its own inverse). -/
lemma boolean_neg_eq_self
    (hbool : ∀ g : G, g + g = 0) (a : G) : -a = a := by
  -- a + a = 0 means a is its own additive inverse
  -- Standard: from h : a + a = 0, derive -a = a
  have h2a := hbool a  -- a + a = 0
  -- eq_neg_of_add_eq_zero_left : a + b = 0 → a = -b
  have := eq_neg_of_add_eq_zero_left h2a  -- a = -a
  exact this.symm

/-- In a boolean group, if a ≠ b then a + b ≠ 0.
    Proof: a + b = 0 → b = -a = a (boolean) → contradiction. -/
lemma boolean_sum_ne_zero
    (hbool : ∀ g : G, g + g = 0)
    {a b : G} (hab : a ≠ b) :
    a + b ≠ 0 := by
  intro h
  have hb_neg_a : b = -a := by
    -- From a + b = 0: b = -a
    have := eq_neg_of_add_eq_zero_right h
    exact this
  rw [boolean_neg_eq_self hbool] at hb_neg_a
  exact hab hb_neg_a.symm

/-- In a boolean group, a + b ≠ a when b ≠ 0.
    Proof: a + b = a → b = 0, contradiction. -/
lemma boolean_sum_ne_left
    (hbool : ∀ g : G, g + g = 0)
    {a b : G} (hb : b ≠ 0) :
    a + b ≠ a := by
  intro h
  -- a + b = a → a + b = a + 0 → b = 0 (by left cancellation)
  have : a + b = a + 0 := by rw [add_zero]; exact h
  have : b = 0 := add_left_cancel this
  exact hb this

/-- In a boolean group, a + b ≠ b when a ≠ 0. -/
lemma boolean_sum_ne_right
    (hbool : ∀ g : G, g + g = 0)
    {a b : G} (ha : a ≠ 0) :
    a + b ≠ b := by
  rw [add_comm]
  exact boolean_sum_ne_left hbool ha

/-- **Theorem B (Boolean Group Schur Forcing)**:
    In a boolean group G with |G| ≥ 4, every 2-coloring of G has a
    monochromatic Schur triple.

    Proof outline:
    1. Let χ : G → Fin 2. Let i = χ(0).
    2. If any nonzero a has χ(a) = i, then a + a = 0 gives triple (a, a, 0)
       all colored i. Done.
    3. Otherwise, all nonzero elements have color j = 1 - i.
       Since |G| ≥ 4, pick distinct nonzero a, b.
       Then a + b is nonzero (≠ 0 since a ≠ b in boolean group),
       ≠ a (since b ≠ 0), ≠ b (since a ≠ 0).
       So a + b is a third nonzero element with χ(a+b) = j.
       Triple (a, b, a+b) is monochromatic. Done. -/
theorem boolean_group_forces_schur [Fintype G]
    (hbool : ∀ g : G, g + g = 0)
    (hcard : Fintype.card G ≥ 4)
    (χ : G → Fin 2) :
    ∃ a b c : G, a + b = c ∧ χ a = χ c ∧ χ b = χ c := by
  -- Case split: is there a nonzero element with the same color as 0?
  by_cases h : ∃ a : G, a ≠ 0 ∧ χ a = χ 0
  · -- Case 1: ∃ nonzero a with χ(a) = χ(0)
    obtain ⟨a, ha_ne, ha_col⟩ := h
    exact ⟨a, a, 0, hbool a, ha_col ▸ rfl, ha_col⟩
  · -- Case 2: all nonzero elements have χ(a) ≠ χ(0)
    push_neg at h
    -- h : ∀ (a : G), a ≠ 0 → χ a ≠ χ 0
    -- Step 1: All nonzero elements share the same color.
    -- Since Fin 2 has exactly two values, χ a ≠ χ 0 for all nonzero a
    -- means all nonzero elements have the unique other color.
    have all_nonzero_eq : ∀ a b : G, a ≠ 0 → b ≠ 0 → χ a = χ b := by
      intro a b ha hb
      have hχa := h a ha  -- χ a ≠ χ 0
      have hχb := h b hb  -- χ b ≠ χ 0
      -- In Fin 2, each element is 0 or 1. If both ≠ χ 0, they must be equal.
      rcases Fin.eq_zero_or_one (χ a) with ha0 | ha1 <;>
        rcases Fin.eq_zero_or_one (χ b) with hb0 | hb1 <;>
          rcases Fin.eq_zero_or_one (χ 0) with h00 | h01
      -- 8 cases, but only those where χ a ≠ χ 0 and χ b ≠ χ 0 survive
      all_goals (first | (rw [ha0, hb0]; rfl) | (rw [ha1, hb1]; rfl) |
        (exfalso; apply hχa; rw [ha0, h00]) | (exfalso; apply hχa; rw [ha1, h01]) |
        (exfalso; apply hχb; rw [hb0, h00]) | (exfalso; apply hχb; rw [hb1, h01]))
    -- Step 2: Extract two distinct nonzero elements from G.
    -- |G| ≥ 4 → |univ| ≥ 4 → |univ \ {0}| ≥ 3 → card > 1
    have huniv_card : Finset.univ.card = Fintype.card G := Finset.card_univ
    have h0_mem : (0 : G) ∈ (Finset.univ : Finset G) := Finset.mem_univ 0
    have herase_card : (Finset.univ.erase (0 : G)).card = Fintype.card G - 1 := by
      rw [Finset.card_erase_of_mem h0_mem, huniv_card]
    have herase_gt : 1 < (Finset.univ.erase (0 : G)).card := by
      rw [herase_card]; omega
    rw [Finset.one_lt_card] at herase_gt
    obtain ⟨a, ha_mem, b, hb_mem, hab⟩ := herase_gt
    -- a, b are nonzero (they're in univ \ {0})
    have ha_ne : a ≠ 0 := Finset.ne_of_mem_erase ha_mem
    have hb_ne : b ≠ 0 := Finset.ne_of_mem_erase hb_mem
    -- Step 3: a + b is nonzero, distinct from both a and b
    have hab_ne_zero : a + b ≠ 0 := boolean_sum_ne_zero hbool hab
    have hab_ne_a : a + b ≠ a := boolean_sum_ne_left hbool hb_ne
    have hab_ne_b : a + b ≠ b := boolean_sum_ne_right hbool ha_ne
    -- Step 4: All three have the same color (all nonzero)
    have hχ_ab : χ a = χ b := all_nonzero_eq a b ha_ne hb_ne
    have hχ_sum : χ a = χ (a + b) := all_nonzero_eq a (a + b) ha_ne hab_ne_zero
    -- Step 5: (a, b, a+b) is the monochromatic Schur triple
    exact ⟨a, b, a + b, rfl, hχ_sum, hχ_ab.symm ▸ hχ_sum⟩

/-- **Theorem A' (Sum-Free Interval Property)**:
    In ℤ/nℤ with n ≥ 3, if a, b ∈ (n/3, 2n/3) then a + b mod n ∉ (n/3, 2n/3).
    This proves the interval {⌈n/3⌉+1, ..., ⌊2n/3⌋} is sum-free.

    Note: Full formalization requires ZMod, deferred to future work. -/
-- theorem interval_sum_free_in_ZMod (n : ℕ) (hn : n ≥ 3) : sorry

/-- **Theorem C (Embedding Preserves Sum-Free)**:
    An injective group homomorphism preserves sum-free sets. -/
theorem embedding_preserves_sum_free
    {H : Type*} [AddCommGroup H] [DecidableEq H]
    (f : G →+ H) (hf : Function.Injective f)
    (A : Finset G) (hsf : IsSumFree A) :
    IsSumFree (A.map ⟨f, hf⟩) := by
  intro x y z hx hy hz hxyz
  -- x, y, z ∈ f(A) means x = f(a), y = f(b), z = f(c) for a,b,c ∈ A
  rw [Finset.mem_map] at hx hy hz
  obtain ⟨a, haA, rfl⟩ := hx
  obtain ⟨b, hbA, rfl⟩ := hy
  obtain ⟨c, hcA, rfl⟩ := hz
  -- f(a) + f(b) = f(c) and f is a homomorphism, so f(a + b) = f(c)
  -- By injectivity, a + b = c
  have hab : a + b = c := by
    apply hf
    rw [map_add]
    exact hxyz
  -- But A is sum-free, contradiction
  exact hsf a b c haA hbA hcA hab

/-- **Corollary**: Sum-free number is monotonic: if H ≤ G (via embedding),
    then any sum-free set in H maps to a sum-free set in G of the same size. -/
-- This follows from embedding_preserves_sum_free and card_map.

/-! ## Status Summary

### Proved (no sorry):
- singleton_zero_not_sum_free       — {0} is not sum-free
- singleton_nonzero_sum_free        — {a} with a+a≠a is sum-free
- zero_gives_schur_triple           — 0 ∈ A → A not sum-free
- boolean_neg_eq_self               — a+a=0 → -a = a
- boolean_sum_free_avoids_zero      — sum-free in boolean group ⟹ 0∉A
- boolean_sum_ne_zero               — a≠b → a+b≠0 in boolean group
- boolean_sum_ne_left               — b≠0 → a+b≠a in boolean group
- boolean_sum_ne_right              — a≠0 → a+b≠b in boolean group
- embedding_preserves_sum_free      — injective hom preserves sum-free

### Proved (via Fintype.card extraction + Fin 2 case analysis):
- boolean_group_forces_schur        — Case 1: nonzero shares color with 0 → (a,a,0);
                                       Case 2: all nonzero same color → (a,b,a+b)

### Not formalized:
- interval_sum_free_in_ZMod         — requires ZMod infrastructure
- schur_number computation          — requires decidable quantifiers over Fintype
-/

end NPG15

/-! ## Notes on Formalization Strategy

1. The main challenge is defining "Schur number" non-constructively
   while allowing computational verification for finite groups.

2. For specific groups (ℤ/nℤ), we can compute explicitly.

3. The connection to Kelley-Meka may provide proof strategies:
   - Fourier analysis on finite abelian groups is well-developed
   - Bohr sets generalize naturally to arbitrary groups

4. AI-assisted proof search can help with:
   - Exhaustive case analysis for small groups
   - Finding counterexamples to conjectures
   - Verifying computational bounds
-/
