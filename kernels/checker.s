; 32x32 checkerboard, 4px squares
tid r1
ldi r2, 31
and r3, r1, r2      ; x
ldi r2, 5
shr r4, r1, r2      ; y
ldi r2, 2
shr r3, r3, r2
shr r4, r4, r2
xor r3, r3, r4
ldi r2, 1
and r3, r3, r2
ldi r5, 255
mul r3, r3, r5
st  [r1 + 0], r3
halt
