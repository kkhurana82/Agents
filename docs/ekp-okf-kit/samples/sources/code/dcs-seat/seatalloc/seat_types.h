/* SYNTHETIC SAMPLE. Passenger and seat records used by seat allocation. */
typedef struct pax {
    char  surname[32];
    short infant_count;      /* lap infants travelling with this passenger */
    char  cabin;
} pax_t;

typedef struct seat {
    char           row[4];
    char           letter;
    unsigned short attrs;    /* SEAT_ATTR_* bit flags */
} seat_t;

#define SEAT_ATTR_EXIT_ROW  0x0004
#define SEAT_OK             0
#define SEAT_REJ_INF_EXIT   41
