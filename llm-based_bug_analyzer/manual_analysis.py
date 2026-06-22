#!/usr/bin/env python3
"""
Manual LLM-based inconsistency analysis for MBFuzzer.

This script is intentionally close to the original baseline pipeline.

Baseline pipeline in replay_all.py:
    1. read_packet_hex_strings_from_file()
    2. send_to_multiple_to_brokers()
    3. ask_for_llm_diff_info()
    4. ask_for_llm_final_info()

Manual pipeline implemented here:
    1. read_packet_hex_strings_from_file()
    2. send_to_multiple_to_brokers()
    3. build the same Prompt A, but save it to a file
    4. build a Prompt B template, but save it to a file

The goal is to manually copy Prompt A and Prompt B into ChatGPT,
without using the OpenAI API.
"""

import argparse
import os
import replay_all as baseline


TARGET_IPS = [
    "172.199.0.2",  # hivemq
    "172.199.0.3",  # vernemq
    "172.199.0.4",  # emqx
    "172.199.0.5",  # flashmq
    "172.199.0.6",  # nanomq
    "172.199.0.7",  # mosquitto
]

TARGET_PORT = 1883


def build_prompt_a(llm_prompt):
    """
    This reproduces the first prompt built by ask_for_llm_diff_info(),
    but does not send it to the LLM.
    """
    prompt = ""
    prompt += "(1) Followings are a sequence of MQTT requests sent by the client.\n"
    prompt += f"{llm_prompt['request']}\n"
    prompt += "(2) Followings are the sequence of responses from several brokers.\n"
    prompt += f"{llm_prompt['response']}\n"
    prompt += (
        "(3) Now you are an expert in the MQTT protocol, please describe "
        "what the differences between these brokers in responding to handle "
        "such request.\n"
        "Please provide the detail description of the analysis.\n"
        "Important constraint for this first step: only summarize observable "
        "behavioral differences among brokers. Do not decide whether there is "
        "a protocol violation, and do not judge which broker is correct. "
        "The protocol-violation decision will be performed in a second step.\n"
    )
    return prompt


def build_prompt_b_template(llm_prompt):
    """
    This reproduces the second prompt built by ask_for_llm_final_info(),
    but leaves a placeholder for the answer produced from Prompt A.
    """
    prompt = ""
    prompt += "(1) Followings are protocol violations related to several MQTT messages.\n"
    prompt += llm_prompt["augment"]
    prompt += "(2) Followings are a sequence of MQTT requests sent by the client.\n"
    prompt += f"{llm_prompt['request']}\n"
    prompt += "(3) The processing of the above requests by each broker has the following differences:\n"
    prompt += "[PASTE HERE THE ANSWER OBTAINED FROM PROMPT A]\n"
    prompt += (
        "(4) Now that you are an MQTT protocol expert, determine whether "
        "the observed broker responses reveal a potential broker-side "
        "non-compliance bug. First identify the expected behavior according "
        "to the violation rules in (1). Then compare each broker response "
        "against that expected behavior and indicate which broker, if any, "
        "appears potentially non-compliant.\n"
        "Please start with '# Analysis Process.' and end with exactly one "
        "of the following conclusions:\n"
        "Broker Non-Compliance Found!\n"
        "No broker non-compliance found!\n")
    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Generate manual LLM prompts for one selected MBFuzzer .raw inconsistency."
    )
    parser.add_argument(
        "raw_file",
        help="Path to the selected .raw inconsistency file."
    )
    parser.add_argument(
        "-o",
        "--output",
        default="manual_llm_prompts.txt",
        help="Output file containing the selected .raw path and the prompts."
    )
    args = parser.parse_args()

    raw_file = args.raw_file
    output_file = args.output

    if not os.path.isfile(raw_file):
        raise FileNotFoundError(f"Raw file not found: {raw_file}")

    packet_hex_strings = baseline.read_packet_hex_strings_from_file(raw_file)

    # This function:
    #   - parses requests,
    #   - replays them against all brokers,
    #   - parses broker responses,
    #   - builds llm_prompt['request'], llm_prompt['response'],
    #     and llm_prompt['augment'].
    llm_prompt = baseline.send_to_multiple_to_brokers(
        TARGET_IPS,
        TARGET_PORT,
        packet_hex_strings
    )

    # Instead of calling the LLM API,
    # we only save the prompts.
    prompt_a = build_prompt_a(llm_prompt)
    prompt_b_template = build_prompt_b_template(llm_prompt)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Manual MBFuzzer inconsistency analysis\n")
        f.write("=" * 80 + "\n\n")

        f.write("Selected raw file:\n")
        f.write(f"{os.path.abspath(raw_file)}\n\n")

        f.write("Number of packets read from .raw file:\n")
        f.write(f"{len(packet_hex_strings)}\n\n")

        f.write("=" * 80 + "\n")
        f.write("PROMPT A - Broker behavior difference summary\n")
        f.write("=" * 80 + "\n\n")
        f.write(prompt_a)
        f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("PROMPT B - Protocol violation analysis template\n")
        f.write("=" * 80 + "\n\n")
        f.write(prompt_b_template)
        f.write("\n")

    print(f"[+] Manual prompts written to: {output_file}")
    print("[+] Next step: copy PROMPT A into ChatGPT.")
    print("[+] Then paste the answer into the placeholder inside PROMPT B.")


if __name__ == "__main__":
    main()