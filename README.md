# MBFuzzer Scheduling Experiments

This repository contains a modified version of the MBFuzzer codebase focused on experimenting with message scheduling policies for MQTT broker fuzzing.

MBFuzzer is a multi-party black-box fuzzer for MQTT brokers. It coordinates multiple message senders, uses dependency rules to exercise multi-party MQTT interactions, and relies on differential testing to detect inconsistent broker behavior.


## Reference

This work is based on:

> Xiangpu Song et al., **MBFuzzer: A Multi-Party Protocol Fuzzer for MQTT Brokers**, USENIX Security 2025.

## Repository scope

This repository does not include the full original artifact package.

In particular, the Docker environment and the complete raw fuzzing output directories are not included. Large generated files, raw queues, intermediate test cases, and full crash/diff directories were excluded to keep the repository lightweight.

Selected textual fuzzing reports are available in:

```text
reports/
```


## Main changes

This branch introduces changes related to the fuzzing message scheduling logic.

At a high level, the modifications include:

configurable usage of dependency rules;
support for multiple scheduling policies;
experiments with the original Q-learning scheduler, a random scheduler, and a state-independent scheduler;
selected fuzzing campaigns with the resulting textual reports stored in reports/;
an additional manual analysis script for inspecting a specific .raw inconsistency file without using API calls.

The manual analysis utility reuses the replay and prompt-construction logic of the original LLM-based analyzer, but saves the prompts locally so that the analysis can be performed manually.

## Repository structure
fuzz.py                     Main MBFuzzer entry point
globals.py                  Global configuration parameters
fuzzer/                     Fuzzing engine and scheduling-related logic
generators/                 MQTT message generation logic
parsers/                    MQTT response parsing logic
type/                       Support classes used by the fuzzer
llm-based_bug_analyzer/     Inconsistency replay and analysis utilities
reports/                    Selected fuzzing reports
Notes

This branch is intended as an experimental extension of MBFuzzer focused on scheduling-policy comparison and selected inconsistency analysis.

For the full original artifact, Docker setup, and complete reproduction instructions, refer to the official MBFuzzer artifact released by the authors.
