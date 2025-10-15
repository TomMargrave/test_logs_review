"""
log_Details_updated.py

This script simulates automated test execution and generates log files
for multiple releases. It supports:
 - Cleaning up old test logs before generating new ones
 - Using reusable step definitions (e.g., Login, Logout)
 - Executing a sequence of test steps with simulated delays, pass/fail outcomes
 - Collecting summary statistics (tests run, skipped, passed, failed, average latency)
 - Running the same test suite across multiple release names provided by the user

Author: Tom Margrave & ChatGPT
Date: Aug 2025
"""

import json
import random
import os
from datetime import datetime, timedelta
from config_loader import ConfigLoader
from virtual_clock import VirtualClock



# ------------------------------
# LogDetails Class
# ------------------------------
class LogDetails:
    def __init__(self, test_case_file="test_cases.json"):
        """
        Initialize LogDetails with test cases, reusable steps, clock, and YAML config.
        """
        self.my_vars = ConfigLoader("config.yaml")
        self.skip_rate = self.my_vars.get("skip_rate", 0.2)
        self.latency_factor = self.my_vars.get("latency_factor", 1.0)
        self.fail_rate = self.my_vars.get("fail_rate", 0.05)
        self.output_format = self.my_vars.get("output_format", "log")
        # Default to current directory if not set in YAML
        self.output_location = self.my_vars.get("output_location", ".")

        self.releases = self.my_vars.get("releases", ["R1"])
        self.reusable_stop_function = self.my_vars.get("reusable_stop_function", None)
        self.data = self.load_test_cases(test_case_file)
        self.reusable = self.data.get("reusable", {})
        self.tests = self.data.get("tests", [])
        self.clock = VirtualClock()

    def load_test_cases(self, file="test_cases.json"):
        """
        Load test cases from a JSON file.
        """
        with open(file, "r") as f:
            return json.load(f)

    def jitter_delay(self, mean_time, variance=0.2, force_delay=None, latency_factor=1.0):
        """
        Calculate jittered delay for a test step.
        """
        if force_delay:
            return force_delay
        jitter = mean_time * random.uniform(1 - variance, 1 + variance)
        return jitter * latency_factor

    def run_step(self, step, latency_factor=None, fail_rate=None):
        """
        Execute a single test step, applying latency spike if present.
        """
        mean_time = step.get("mean_time", 500)
        variance = step.get("variance", 0.2)
        force_delay = step.get("force_delay", None)
        # Use step-specific latency_factor if spike present
        step_latency_factor = latency_factor if latency_factor is not None else self.latency_factor
        if "latency_spike" in step:
            step_latency_factor *= step["latency_spike"]
        delay = self.jitter_delay(mean_time, variance, force_delay, step_latency_factor)
        step_fail_rate = fail_rate if fail_rate is not None else self.fail_rate
        status = "P"
        if step.get("can_fail", True) and random.random() < step_fail_rate:
            status = "F"
        line = f"{status} {step['action']} ({int(delay)}ms)"
        return line, delay, status

    def expand_steps(self, test):
        """
        Expand steps in a test case, including reusable blocks.
        """
        expanded = []
        for step in test["steps"]:
            if "use" in step:
                block_name = step["use"]
                if block_name not in self.reusable:
                    raise ValueError(f"Reusable block '{block_name}' not defined")
                expanded.extend(self.reusable[block_name])
            else:
                expanded.append(step)
        return expanded

    def run_test(self, test, latency_factor=None, fail_rate=None, release=None):
        """
        Run a single test case, stopping and running reusable function if step fails and stop_on_fail is set.
        """
        logs = []
        test_name = test.get("name")
        start_time = self.clock.formatted_time()
        logs.append(f"--- START TEST_ID: {test_name} Release_ID: {release} ---")
        logs.append(f"-- Description: {test.get('description', 'No description')}")
        logs.append(f"{self.clock.formatted_time()} - START TESTed (0ms)")
        total_latency = 0
        passes = 0
        fails = 0
        steps = self.expand_steps(test)
        test_aborted = False  # Initialize test_aborted to False before the loop
        for step in steps:
            line, delay, status = self.run_step(step, latency_factor, fail_rate)
            self.clock.advance_ms(delay)
            # logs.append(f"{self.clock.formatted_time()} {line} (Release_ID: {release})")
            logs.append(f"{self.clock.formatted_time()} {line}")
            total_latency += delay
            if status == "P":
                passes += 1
            else:
                fails += 1
                if step.get("stop_on_fail", False):
                    logs.append(f"{self.clock.formatted_time()} Test aborted due to failure. Running reusable stop function: {self.reusable_stop_function}")
                    # Run reusable stop function steps if defined
                    if self.reusable_stop_function and self.reusable_stop_function in self.reusable:
                        for stop_step in self.reusable[self.reusable_stop_function]:
                            stop_line, stop_delay, _ = self.run_step(stop_step, latency_factor, fail_rate)
                            self.clock.advance_ms(stop_delay)
                            logs.append(f"{self.clock.formatted_time()} {stop_line} (Release_ID: {release})")
                    test_aborted = True
                    break
        logs.append(f"{self.clock.formatted_time()} - END TEST (0ms)")
        logs.append(f"--- END TEST_ID: {test_name} (Release_ID: {release}) ---\n")
        return logs, {
            "name": test_name,
            "passes": passes,
            "fails": fails,
            "latency": total_latency,
            "start": start_time,
            "end": self.clock.formatted_time(),
            "test_passed": 1 if fails == 0 and not test_aborted else 0
        }

    def generate_test_log(self, release_name):
        """
        Generate a log file for a given release, using config values and output format.
        """
        filename = f"test_log_{release_name}.{self.output_format}"
        filepath = self.output_location
        full_path = os.path.join(filepath, filename)
        summary = {
            "tests_run": 0,
            "tests_skipped": 0,
            "steps_passed": 0,
            "steps_failed": 0,
            "latencies": [],
            "test_passed": 0,
        }

        with open(full_path, "w") as f:
            for test in self.tests:
                if random.random() < self.skip_rate:
                    summary["tests_skipped"] += 1
                    continue
                logs, results = self.run_test(test, self.latency_factor, self.fail_rate, release=release_name)
                for line in logs:
                    f.write(line + "\n")
                summary["tests_run"] += 1
                summary["steps_passed"] += results["passes"]
                summary["steps_failed"] += results["fails"]
                summary["latencies"].append(results["latency"])
                summary["test_passed"] += results["test_passed"]
                gap_seconds = random.randint(1, 10)
                self.clock.advance_ms(gap_seconds * 1000)

            avg_latency = (
                sum(summary["latencies"]) / len(summary["latencies"]) if summary["latencies"] else 0
            )

            summary_text = "\n--- SUMMARY ---\n"
            summary_text += f"Release_ID: {release_name}\n"
            summary_text += f"Tests Run: {summary['tests_run']}\n"
            summary_text += f"Tests Passed: {summary['test_passed']}\n"
            summary_text += f"Tests Skipped: {summary['tests_skipped']}\n"
            summary_text += f"Steps Passed: {summary['steps_passed']}\n"
            summary_text += f"Steps Failed: {summary['steps_failed']}\n"
            summary_text += f"Average Latency: {int(avg_latency)} ms\n"
            f.write(summary_text)

        print(f"✅ Log generated: {filename}")

        # After generating the per-release log, append it to the master log
        self.append_to_master_log(full_path, release_name)

    def append_to_master_log(self, filepath, release_name):
        """
        Append the contents of a per-release log file to a master log file `test_log_all.log`.
        Each appended block is prefixed with a header containing the release name and timestamp.
        The master log is created in the configured output location.
        """
        master_filename = os.path.join(self.output_location, "test_log_all.log")
        try:
            with open(filepath, "r") as src, open(master_filename, "a") as dest:
                dest.write(f"\n--- APPEND FROM {release_name} : {self.clock.formatted_time()} ---\n")
                for line in src:
                    dest.write(line)
                dest.write(f"\n--- END APPEND FROM {release_name} ---\n")
        except Exception as e:
            print(f"Warning: failed to append {filepath} to {master_filename}: {e}")
        
        

    def cleanup_logs(self, folder="."):
        """
        Delete only .log files, not .txt files, in the target folder.
        """
        for file in os.listdir(folder):
            if file.startswith("test_log_") and file.endswith(".log"):
                os.remove(os.path.join(folder, file))
                print(f"🗑 Deleted old log: {file}")

    def make_logs(self):
        """
        Main entry point: clean logs, set clock, and generate logs for each release from YAML config.
        """
        print("Start:", self.clock.formatted_time())
        test_count = len(self.tests)
        self.clock.advance_days(-test_count)
        self.cleanup_logs(self.output_location)
        for release in self.releases:
            self.clock.start_test_at(8, 0, 0)
            print(f"Start: {release} - ", self.clock.formatted_time())
            self.generate_test_log(release)
            self.clock.advance_days(1)

# ------------------------------
# Main Script
# ------------------------------
if __name__ == "__main__":
    LD = LogDetails()
    LD.make_logs()
