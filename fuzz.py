import sys
import fuzzer.fuzzing_engine as fe
import helper_functions.directory_operation as do
import fuzzer.q_learning as QLearning
import fuzzer.random_scheduler as RandomScheduler
import fuzzer.state_independent_scheduler as StateIndependentScheduler
import globals as g
import signal
import time
import os
import fuzzer.server_module as server_module
import fuzzer.retain_recv_module as retain_recv_module


def handle_exit(signum, frame):
    print("Received Ctrl+C signal. Exiting...")
    do.dump_fuzzing_info_log(GLOBAL_SCHEDULER)
    os._exit(0)

def create_message_scheduler():
    if g.SCHEDULER_POLICY == "q_learning":
        return QLearning.QLearningTable()

    if g.SCHEDULER_POLICY == "random":
        return RandomScheduler.RandomScheduler()

    if g.SCHEDULER_POLICY == "state_independent":
        return StateIndependentScheduler.StateIndependentScheduler()

    raise ValueError(f"Unknown scheduler policy: {g.SCHEDULER_POLICY}")

def main():
    global GLOBAL_SCHEDULER
    # Set up signal handler
    signal.signal(signal.SIGINT, handle_exit)

    # Create fuzzing directory 
    do.create_initial_fuzzing_directory()

    MessageScheduler = create_message_scheduler()
    GLOBAL_SCHEDULER = MessageScheduler

    print(f"Using scheduler policy: {g.SCHEDULER_POLICY}")
    print(
        f"Dependency rules enabled: {g.ENABLE_DEPENDENCY_RULES}, "
        f"probability: {g.DEPENDENCY_RULE_PROBABILITY}"
    )
        
    cacheBroker = retain_recv_module.CacheBroker(port=1885)
    cacheBroker.start()

    g.FUZZING_START_TIME = time.time()
    # Start mqtt broker fuzzers
    broker = server_module.MQTTBroker(port=1884, MessageModel=MessageScheduler)
    broker.start()

    while broker.check_fuzzing_bridge_status() == False:
        print(f"Initial waiting for brokers (will be soon) {broker.client_sessions.keys()}")
        time.sleep(3)

    while_start_time = g.FUZZING_START_TIME

    # Run client fuzzing loop
    while True:
        fe.single_fuzzing_engine_client(MessageScheduler)
        if g.DEBUG_FLAG_CLIENT_MSG_SENDING == True:
            break
        
        cur_time = time.time()
        elapsed_time = cur_time - while_start_time
        if elapsed_time >= 60:
            while_start_time = cur_time
            do.dump_fuzzing_info_log(MessageScheduler)
    
    print("Fuzzing loop finished.")
    do.dump_fuzzing_info_log(MessageScheduler)


if __name__ == "__main__":
    main()
