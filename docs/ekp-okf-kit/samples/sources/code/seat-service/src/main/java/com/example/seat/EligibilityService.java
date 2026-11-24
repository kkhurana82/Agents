// SYNTHETIC SAMPLE for the EKP OKF kit. Modernised seat service (Spring Boot).
package com.example.seat;

@Service
public class EligibilityService {
    private final RuleTable rules;          // loaded from rules/seat-eligibility.yaml
    private final SeatEventPublisher events;

    public SeatDecision assignSeat(Passenger pax, Seat seat) {
        Optional<Reject> reject = rules.firstReject(pax, seat);
        if (reject.isPresent()) return SeatDecision.rejected(reject.get());
        events.publishSeatAssigned(pax, seat);   // -> Pub/Sub topic seat-assigned
        return SeatDecision.assigned(seat);
    }
}
