from streamit.client import get_experiment_data_stream
from streamit.common import DataType
import time
import os


os.environ["MARO_STREAMABLE_ENABLED"] = "True"


if __name__ == "__main__":

    start_time = time.time()

    stream = get_experiment_data_stream()
    stream.start()

    total_eps = 10
    durations = 102

    with stream.experiment(f"test_expmt_{time.time()}", "cim", "toy.1.1", total_eps, durations):
        stream.category("port_detail", True, DataType.csv, "index", "empty", "full", "shortage")
        stream.category("vessel_detail", True, DataType.csv, "index", "empty", "full", "remaining_space")

        for ep in range(total_eps):
            print(ep)

            with stream.episode(ep):
                for tick in range(durations):
                    with stream.tick(tick):
                        # ports
                        for i in range(10):
                            stream.csv("port_detail", i, i * 10, i * 100, i * 1000)

                        # vessels
                        for i in range(10):
                            stream.csv("vessel_detail", i, i * 20, i * 200, i * 2000)

                time.sleep(1)

    stream.close()

    print("total time cost:", time.time() - start_time)