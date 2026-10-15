; C[i] = A[i] + B[i]      A@0  B@16  C@32
tid r1
ld  r2, [r1 + 0]
ld  r3, [r1 + 16]
add r4, r2, r3
st  [r1 + 32], r4
halt
