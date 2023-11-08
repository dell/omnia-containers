#ifndef _IPXE_EFI_ENTROPY_H
#define _IPXE_EFI_ENTROPY_H

/** @file
 *
 *    EFI entropy source
 *
 */

FILE_LICENCE ( GPL2_OR_LATER );

#ifdef ENTROPY_EFI
#define ENTROPY_PREFIX_efi
#else
#define ENTROPY_PREFIX_efi __efi_
#endif

static inline __always_inline double
ENTROPY_INLINE ( efi, min_entropy_per_sample ) ( void ) {
    /* TODO: actually meansure min entropy per sample */
    return 1.3;
}

extern uint8_t efi_sample ( void );
static inline __always_inline int
ENTROPY_INLINE ( efi, get_noise ) ( noise_sample_t *noise ) {

    /* get sample */
    *noise = efi_sample();

    /* success */
    return 0;
}

#endif /* _IPXE_EFI_ENTROPY_H */
