# LogDetails Test Log Generator

## Purpose

This project generates synthetic test logs for automated evaluation by AI. It simulates test execution, step latencies, pass/fail outcomes, and supports configuration via YAML and JSON. Logs are tagged by release and can be customized for output format and test flow.

## Features

- Configurable via `config.yaml` (skip rate, latency factor, fail rate, output format, releases, stop/restart function, etc.)
- Test cases and reusable steps defined in `test_cases.json`
- Simulates step latency, pass/fail, and can spike latency for specific steps
- If a step fails and is marked to stop, runs a reusable stop/restart function and aborts the test
- Only deletes `.log` files, not `.txt` files
- Output format is configurable (log/txt)
- Each log entry is tagged with the release number
- Designed for easy extension and AI evaluation

## How to Use

1. Edit `config.yaml` to set your configuration values.
2. Edit `test_cases.json` to define your test cases and reusable steps. You can add `latency_spike` and `stop_on_fail` to any step.
3. Run the main script:

   ```bash
   python src/log_Details.py
   ```

4. Logs will be generated in the format specified in `config.yaml` for each release.

## File Structure

- `src/log_Details.py`: Main logic and entry point
- `src/test_cases.json`: Test case and reusable step definitions
- `src/config.yaml`: Configuration values
- `src/virtual_clock.py`: Virtual clock for simulating time
- `src/config_loader.py`: YAML config loader

## Example YAML (`config.yaml`)

```yaml
skip_rate: 0.2
latency_factor: 1.0
fail_rate: 0.05
output_format: log
output_location: "D:\\Projects\\LogDetails\\logs\\"
releases:
  - R1
  - R2
  - R3
reusable_stop_function: STOP_AND_RESTART_AUT
```

## Example JSON (`test_cases.json`)

```json
{
  "reusable": {
    "STOP_AND_RESTART_AUT": [
      { "action": "Stop AUT", "mean_time": 500 },
      { "action": "Restart AUT", "mean_time": 1000 }
    ]
  },
  "tests": [
    {
      "name": "Login_And_Checking_Balance",
      "description": "Verify user can login and view checking account balance.",
      "steps": [
        { "action": "Get Checking balance", "mean_time": 1200, "latency_spike": 5.0, "stop_on_fail": true }
      ]
    }
  ]
}
```

## Contributing

Feel free to fork, submit issues, or pull requests!

## License

MIT
