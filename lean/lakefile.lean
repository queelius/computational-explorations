import Lake
open Lake DSL

package erdos where
  leanOptions := #[
    ⟨`autoImplicit, false⟩
  ]

@[default_target]
lean_lib Erdos43
lean_lib Erdos883
lean_lib NPG2_DensitySchur
lean_lib NPG15_SchurGroups
lean_lib CoprimeRamsey
lean_lib CoprimePerfect
lean_lib SchurTwoGroups

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "v4.16.0"
