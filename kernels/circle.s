; 32x32 shaded disc, radius 12 centred at (16,16)
tid r1
ldi r2, 31
and r3, r1, r2      ; x
ldi r2, 5
shr r4, r1, r2      ; y
addi r3, r3, -16    ; dx
addi r4, r4, -16    ; dy
mul r3, r3, r3
mul r4, r4, r4
add r3, r3, r4      ; d = dx^2 + dy^2
ldi r5, 144
slt r6, r3, r5      ; inside?
ldi r7, 255
sub r7, r7, r3      ; 255 - d  (radial shade)
mul r7, r7, r6      ; zero outside
st  [r1 + 0], r7
halt
