; TFE on a resident R32_UINT image, measured with raw image_load on GFX1036.
; vk_store_test words fills the 8x8 input with 100+i. Read row zero at x = -1,0,1,2,8,9,10,11.
; Copy the full-width data and status and the D16 data and status to the first four rows of the SINT image.
; Data rows 0 and 2 contain zero (preserving D16's high half) outside the image. The two status rows retain
; their distinct seeds on all accesses. A coordinate outside a resident view does not give a residency NACK.
; Run: vk_store_test cs_image_tfe_dense.spv words
; mattr: +wavefrontsize32,-wavefrontsize64
v_cmpx_gt_u32_e32 32, v0
v_and_b32_e32 v1, 7, v0
v_lshrrev_b32_e32 v2, 3, v0
v_add_nc_u32_e32 v3, -1, v1
v_add_nc_u32_e32 v4, 4, v1
v_cmp_gt_u32_e32 4, v1
v_cndmask_b32_e64 v3, v4, v3, vcc_lo
v_mov_b32_e32 v4, 0

s_mov_b32 s8, 0x2000
s_mov_b32 s9, 0x1400000
s_mov_b32 s10, 0x22
s_mov_b32 s11, 0x22
s_mov_b32 s12, 0x22
s_mov_b32 s13, 0x22
s_mov_b32 s14, 0x22
s_mov_b32 s15, 0x22
s_mov_b32 s16, 0x3000
s_mov_b32 s17, 0x1500000
s_mov_b32 s18, 0x33
s_mov_b32 s19, 0x33
s_mov_b32 s20, 0x33
s_mov_b32 s21, 0x33
s_mov_b32 s22, 0x33
s_mov_b32 s23, 0x33

v_mov_b32_e32 v8, 0x5a5a03f5
v_mov_b32_e32 v9, 0x5a5a03f4
v_mov_b32_e32 v10, 0x5a5a03f6
image_load v[7:8], v[3:4], s[8:15] dmask:0x1 dim:SQ_RSRC_IMG_2D unorm tfe
image_load v[9:10], v[3:4], s[8:15] dmask:0x1 dim:SQ_RSRC_IMG_2D unorm tfe d16
s_waitcnt vmcnt(0)

v_cmp_eq_u32_e32 2, v2
v_cndmask_b32_e64 v11, v10, v9, vcc_lo
v_cmp_eq_u32_e32 1, v2
v_cndmask_b32_e64 v11, v11, v8, vcc_lo
v_cmp_eq_u32_e32 0, v2
v_cndmask_b32_e64 v11, v11, v7, vcc_lo
image_store v11, v[1:2], s[16:23] dmask:0x1 dim:SQ_RSRC_IMG_2D unorm
s_endpgm
