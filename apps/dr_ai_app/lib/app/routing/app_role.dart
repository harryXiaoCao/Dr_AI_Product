enum AppRole {
  doctor,
  patient,
  payer,
  unsupported;

  static AppRole fromWire(String value) {
    return switch (value.trim().toLowerCase()) {
      'doctor' => AppRole.doctor,
      'patient' => AppRole.patient,
      'payer' => AppRole.payer,
      _ => AppRole.unsupported,
    };
  }

  String get wireValue => name;
}
