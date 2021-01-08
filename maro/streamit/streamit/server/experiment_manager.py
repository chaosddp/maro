
from .experiment import Experiment


class ExperimentManager:
    def __init__(self):
        self._experiments = []

    def new_experiment(self, enable_dump=False):
        experiment = Experiment(self, enable_dump)

        self._experiments.append(experiment)

        return experiment

    def remove(self, experiment):
        self._experiments.remove(experiment)

    def cancel(self, wsock):
        for experiment in self._experiments:
            experiment.remove_dispatcher(wsock)