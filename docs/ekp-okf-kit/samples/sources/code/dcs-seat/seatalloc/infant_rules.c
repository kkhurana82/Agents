/*
 * seatalloc/infant_rules.c
 * SYNTHETIC SAMPLE for the EKP OKF kit. Not real airline code.
 */
#include "seat_types.h"

/* Returns SEAT_OK, or a reject code if the passenger may not take the seat. */
int check_exit_row_infant(const pax_t *pax, const seat_t *seat)
{
    if (seat->attrs & SEAT_ATTR_EXIT_ROW) {
        if (pax->infant_count > 0) {
            return SEAT_REJ_INF_EXIT;   /* infant may not sit in an exit row */
        }
    }
    return SEAT_OK;
}
