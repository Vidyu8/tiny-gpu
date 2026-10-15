; y[i] = 3*x[i] + y[i]   x@0  y@16
tid r1
ld  r2, [r1 + 0]
ld  r3, [r1 + 16]
ldi r4, 3
mul r2, r2, r4
add r3, r3, r2
st  [r1 + 16], r3
halt
