data
.LC0:
    .word 1
    .word 2
    .word 3
    .word 4
    .word 6
.LC1:
    .word 1
    .word 2
    .word 3
    .word 4
.LC2:
    .word 1
    .word 2
.LC3:
    .word 3
    .word 4
dataend
add1:
    addi    sp,sp,-48
    sw    s0,44(sp)
    addi    s0,sp,48
    sw    a0,-36(s0)
    li    a2,-36(s0)
    sw    a2,-20(s0)
    lw    a2,-20(s0)
    mv    a0,a2
    lw    s0,44(sp)
    addi    sp,sp,48
    jr    ra
add:
    addi    sp,sp,-48
    sw    ra,40(sp)
    sw    s0,40(sp)
    addi    s0,sp,48
    sw    a0,-36(s0)
    sw    a1,-40(s0)
    lw    a0,-40(s0)
    call    add1
    mv    a2,a0
    sw    a2,-20(s0)
    lw    a2,-36(s0)
    lw    a3,-20(s0)
    add    a4,a2,a3
    mv    a0,a4
    lw    ra,44(sp)
    lw    s0,44(sp)
    addi    sp,sp,48
    jr    ra
main:
    addi    sp,sp,-96
    sw    ra,88(sp)
    sw    s0,88(sp)
    addi    s0,sp,96
    li    a2,1
    sw    a2,-20(s0)
    li    a2,2
    sw    a2,-24(s0)
    lui    a2,%hi(.LC0)
    lw    a3,%lo(.LC0)(a2)
    sw    a3,-60(s0)
    addi    a4,a2,%lo(.LC0)
    lw    a2,4(a4)
    sw    a2,-56(s0)
    lw    a2,8(a4)
    sw    a2,-52(s0)
    lw    a2,12(a4)
    sw    a2,-48(s0)
    lw    a2,16(a4)
    sw    a2,-44(s0)
    lui    a2,%hi(.LC1)
    lw    a3,%lo(.LC1)(a2)
    sw    a3,-76(s0)
    addi    a4,a2,%lo(.LC1)
    lw    a2,4(a4)
    sw    a2,-72(s0)
    lw    a2,8(a4)
    sw    a2,-68(s0)
    lw    a2,12(a4)
    sw    a2,-64(s0)
    li    a2,2
    sw    a2,-44(s0)
    li    a2,3
    sw    a2,-56(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    add    a4,a2,a3
    li    a2,3
    ble    a4,a2,.L2
    lw    a2,-44(s0)
    li    a3,4
    ble    a2,a3,.L3
.L2:
    lw    a2,-20(s0)
    addi    a3,a2,1
    sw    a3,-20(s0)
.L5
    lw    a2,-20(s0)
    sub    a3,a2,2
    sw    a3,-20(s0)
    lw    a2,-20(s0)
    li    a3,3
    bge    a2,a3,.L4
    j    .L5
.L4:
.L7
    lw    a2,-20(s0)
    li    a3,3
    ble    a2,a3,.L6
    lw    a2,-20(s0)
    addi    a3,a2,2
    sw    a3,-20(s0)
    j    .L7
.L3:
    lw    a2,-20(s0)
    addi    a3,a2,3
    sw    a3,-20(s0)
.L6:
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    add    a4,a2,a3
    sw    a4,-28(s0)
    lw    a2,-44(s0)
    lw    a3,-36(s0)
    add    a4,a2,a3
    sw    a4,-60(s0)
    lw    a2,-36(s0)
    sw    a2,-60(s0)
    lui    a2,%hi(.LC2)
    lw    a3,%lo(.LC2)(a2)
    sw    a3,-84(s0)
    addi    a4,a2,%lo(.LC2)
    lw    a2,4(a4)
    sw    a2,-80(s0)
    lui    a2,%hi(.LC3)
    lw    a3,%lo(.LC3)(a2)
    sw    a3,-92(s0)
    addi    a4,a2,%lo(.LC3)
    lw    a2,4(a4)
    sw    a2,-88(s0)
    lw    a2,-92(s0)
    lw    a3,-84(s0)
    add    a4,a2,a3
    sw    a4,-32(s0)
    li    a0,1
    lw    a1,-20(s0)
    call    add
    mv    a2,a0
    sw    a2,-36(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    add    a4,a2,a3
    lw    a2,-36(s0)
    addi    a3,a2,1
    mv    a0,a4
    mv    a1,a3
    call    add
    mv    a2,a0
    sw    a2,-40(s0)
    lw    a2,-20(s0)
    addi    a3,a2,1
    sw    a3,-20(s0)
    lw    a2,-20(s0)
    sub    a3,a2,1
    sw    a3,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    add    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    sub    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    or    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    xor    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    and    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    mul    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    lw    a3,-24(s0)
    div    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20(s0)
    addi    a3,a2,1
    sw    a3,-20(s0)
    lw    a2,-24(s0)
    sub    a3,1,a2
    sw    a3,-20(s0)
    lw    a2,-56(s0)
    lw    a3,-24(s0)
    or    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-64(s0)
    xori    a3,a2,1
    sw    a3,-20(s0)
    lw    a2,-56(s0)
    lw    a3,-84(s0)
    and    a4,a2,a3
    sw    a4,-20(s0)
    lw    a2,-20,s0
    addi    a2,a2,1
    sw    a2,-20,s0
    lw    a3,-20,s0
    addi    a3,a3,-1
    sw    a3,-20,s0
    li    a4,1
    mv    a0,a4
    lw    ra,92(sp)
    lw    s0,92(sp)
    addi    sp,sp,96
    jr    ra
