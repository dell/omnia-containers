/*
 * Copyright (C) 2013 IBM
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
 * 02110-1301, USA.
 */

FILE_LICENCE ( GPL2_OR_LATER );

#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <ipxe/entropy.h>
#include <ipxe/timer.h>
#include <ipxe/efi/efi.h>

EFI_EVENT waiter;

static int efi_entropy_enable ( void ) {
    EFI_BOOT_SERVICES *bs = efi_systab->BootServices;
    EFI_STATUS efirc;
    int rc = 0;
    if ( ( efirc = bs->CreateEvent ( EVT_TIMER, TPL_NOTIFY,
                    NULL, NULL, &waiter ) ) != 0){
         rc = -EEFI ( efirc );
    }
    return rc;
}

static void efi_entropy_disable ( void ) {
    EFI_BOOT_SERVICES *bs = efi_systab->BootServices;

    bs->CloseEvent(waiter);
}

uint8_t efi_sample ( void ) {
    EFI_BOOT_SERVICES *bs = efi_systab->BootServices;
    unsigned long before;
    unsigned long after;
    EFI_TIMER_DELAY delay = TimerRelative;
    UINTN discard;

    bs->SetTimer(waiter, delay, 0);
    bs->WaitForEvent(1, &waiter, &discard);
    before = currticks();
    bs->SetTimer(waiter, delay, 10);
    bs->WaitForEvent(1, &waiter, &discard);
    after = currticks();
    return ( after - before );
}
PROVIDE_ENTROPY_INLINE ( efi, min_entropy_per_sample );
PROVIDE_ENTROPY ( efi, entropy_enable, efi_entropy_enable );
PROVIDE_ENTROPY ( efi, entropy_disable, efi_entropy_disable );
PROVIDE_ENTROPY_INLINE ( efi, get_noise );
