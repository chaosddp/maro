
import os

from maro.simulator.scenarios import AbsBusinessEngine

from maro.event_buffer import MaroEvents, CascadeEvent, AtomEvent

from .frame_builder import build_frame
from .world_builder import build_world


class SupplyChainBusinessEngine(AbsBusinessEngine):
    def __init__(self, **kwargs):
        super().__init__(scenario_name="supply_chain", **kwargs)

        self._register_events()

        self._build_world()

        self._frame = build_frame(True, self.calc_max_snapshots(), [])

    @property
    def frame(self):
        return self._frame

    @property
    def snapshots(self):
        return self._frame.snapshots

    @property
    def configs(self):
        pass

    def step(self, tick: int):
        for unit_type, units in self.world.items():
            for unit in units:
                unit.step(None)

    def post_step(self, tick: int):

        return tick+1 == self._max_tick

    def reset(self):
        self._frame.reset()
        self._frame.snapshots.reset()

        # TODO: reset frame nodes.

    def _register_events(self):
        self._event_buffer.register_event_handler(MaroEvents.TAKE_ACTION, self._on_action_recieved)

    def _build_world(self):
        self.update_config_root_path(__file__)

        config_path = os.path.join(self._config_path, "config.yml")

        self.world = build_world(config_path)

    def _on_action_recieved(self, event):
        action = event.payload

        if action:
            pass

            # TODO: how to dispatch it to units?