# SYNTHETIC SAMPLE
resource "google_pubsub_topic" "seat_assigned" {
  name   = "seat-assigned"
  labels = { system = "dcs", component = "seat-assignment" }
  message_retention_duration = "86400s"
}
