# Adding an Exchange

1. Create adapter in `src/pulse/exchanges/{name}/adapter.py`
2. Implement `ExchangeClient` ABC:
   - `connect()` / `disconnect()`
   - `subscribe(channels)`
   - `parse_message(raw)` → dict
   - `normalize(data, data_type)` → canonical dict
   - `health_check()` → status dict
3. Add config entry in `config/exchanges.yaml`
4. Register normalizer in `src/pulse/models/normalize.py`
5. (Optional) Add tests in `tests/test_exchanges/`

No changes to core, API, or dashboard needed.
