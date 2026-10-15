; 32x32 diagonal gradient -> mem[tid]
tid r1
ldi r2, 31
and r3, r1, r2      ; x = tid & 31
ldi r2, 5
shr r4, r1, r2      ; y = tid >> 5
add r5, r3, r4      ; x + y   (0..62)
ldi r2, 4
shl r5, r5, r2      ; *16 (wraps, gives banded look)
st  [r1 + 0], r5
halt
