#!/usr/bin/env python3

from pathlib import Path

from typing import Dict, List, Tuple, Union

import re, subprocess, time

cli_options: Dict[str, List[str]] = dict()
cli_options["all"] = ["-DnameNode=hdfs://namenode:9000",
                      "-DjobTracker=resourcemanager:8032",
                      "-DresourceManager=resourcemanager:8032"]
cli_options["hive2"] = ["-DjdbcURL=jdbc:hive2://hiveserver2:10000/default"]

blacklist: List[str] = []

example_dir = Path("~/examples/apps").expanduser()

def get_workflow_example_dirs(example_dir: Path) -> List[Path]:
    result: List[Path] = []
    for child_dir in example_dir.iterdir():
        if (child_dir.is_dir()
            and not (child_dir / "coordinator.xml").exists()
            and not (child_dir / "bundle.xml").exists()
            and (child_dir / "job.properties").exists()):
            result.append(child_dir)

    return result

def launch_example(example_dir: Path) -> Union[str, int]:
    command = ["/opt/oozie/bin/oozie",
               "job",
               "-config",
               str(example_dir / "job.properties"),
               "-run"]
    command.extend(cli_options["all"])
    if example_dir.name in cli_options:
        command.extend(cli_options[example_dir.name])

    print("Running command: {}.".format(" ".join(command)))
    process_result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return_code = process_result.returncode
    if return_code != 0:
        return return_code
    
    output = process_result.stdout.decode()

    match = re.search("job:(.*)", output)
    if match is None:
        raise ValueError("The job id could not be determined for example {}".format(example_dir.name))
    
    job_id = match.group(1).strip()

    return job_id

def query_job(job_id: str) -> str:
    query_command = ["/opt/oozie/bin/oozie",
                     "job",
                     "-info",
                     job_id]

    query_process_result = subprocess.run(query_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    query_output = query_process_result.stdout.decode()

    match = re.search("Status.*:(.*)\n", query_output)
    if match is None:
        raise ValueError("The status could not be determined for job id {}".format(job_id))
    
    status = match.group(1).strip()

    return status

def kill_job(job_id: str) -> int:
    kill_command = ["/opt/oozie/bin/oozie",
                     "job",
                     "-kill",
                     job_id]

    process_result = subprocess.run(kill_command, stderr=subprocess.PIPE)
    return process_result.returncode

def wait_for_job_to_finish(job_id: str, poll_time: int = 1, timeout: int = 60) -> str:
    start_time = time.time()
    
    status = query_job(job_id)
    while status == "RUNNING" and (time.time() - start_time) < timeout:
        time.sleep(poll_time)
        status = query_job(job_id)

    if status == "RUNNING":
        print("Timed out waiting for example {} to finish, killing it.".format(example_dir.name))
        kill_job(job_id)
        return "Timed out."
    else:
        print("Status: {}.".format(status))
        return status

def run_examples(examples: List[Path], poll_time: int = 1, timeout: int = 60) -> Dict[str, str]:
    results: Dict[str, str] = dict()
    
    for example_dir in examples:
        if example_dir.name in blacklist:
            print("Omitting blacklisted example: {}.".format(example_dir.name))
        else:
            print("Running example {}.".format(example_dir.name))
            launch_result = launch_example(example_dir)

            if isinstance(launch_result, int):
                print("Starting example {} failed with exit code {}.".format(example_dir.name, launch_result))
                results[example_dir.name] = "Starting failed with exit code {}.".format(launch_result)
            else:
                results[example_dir.name] = wait_for_job_to_finish(launch_result, poll_time, timeout)
        print()

    return results

def print_report(results: Dict[str, str]):
    sorted_tests = list(results.keys())
    sorted_tests.sort()

    for test in sorted_tests:
        print("{}:\t{}".format(test, results[test]))

def main() -> None:
    example_dirs = get_workflow_example_dirs(example_dir)
    results = run_examples(example_dirs, 1, 60)
    print_report(results)

if __name__ == "__main__":
    main()
