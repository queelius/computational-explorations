> Historical research note from October 18, 2026; promoted October 20.
> Read README.md in this directory for current status and reproduction.
> Statements about unresolved work describe that historical stage.

# Matching barrier consequence

Claim. Every 17-vertex graph F with at least 42 edges and at least five edges after every four-vertex deletion has matching number at least five.

Proof. If nu(F)<=4, the Tutte-Berge formula supplies S, s=|S|, with q=o(F-S)>=9+s. Since q<=17-s, s<=4. Write the component orders of F-S as n_i. There are q odd components. Subtract one vertex from each odd component; the remaining number r of vertices is at most 8-2s. Consequently the sum of binomial(n_i,2) is at most binomial(r+1,2): concentrating all extras into one odd component maximizes this sum, and an even component with t vertices costs t extras while contributing binomial(t,2)<=binomial(t+1,2). Formal pairwise merges: merge two odd components while keeping one singleton; merge an even component into an odd component; merge two even components. All preserve q and do not decrease the bound. Thus

e(F)<=binomial(s,2)+s(17-s)+binomial(9-2s,2).

For s=0,1,2 these caps are 36,37,41, contradicting e>=42. For s=3, F-S has at most binomial(3,2)=3 edges; deleting one additional vertex leaves at most three. For s=4 it has no edges. Both contradict the residual condition. QED.

This strengthens the earlier tau>=5 statement. It does not by itself prove P10 containment: the relationship between matching and path length still requires a structural argument. No priority claim.

Primary proof source for the standard matching theorem: Douglas B. West, *A short proof of the Berge--Tutte Formula and the Gallai--Edmonds Structure Theorem*, Theorem 4, https://www.cse.iitd.ac.in/~naveen/courses/CSL851/galledm.pdf . The source also gives a maximal barrier whose components are all odd, which simplifies the component-concentration argument.
