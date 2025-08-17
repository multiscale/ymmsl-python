from copy import deepcopy

import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


def convert_v0_1_to_v0_2(config: v0_1.PartialConfiguration) -> v0_2.Configuration:
    """Convert a v0.1 ymmsl object to v0.2.

    Args:
        config: An input configuration in yMMSL v0.1 format

    Returns:
        The corresponding configuration expressed in yMMSL v0.2.
    """
    description = '' if config.description is None else config.description
    settings = deepcopy(config.settings)
    resources = deepcopy(config.resources)
    checkpoints = deepcopy(config.checkpoints)
    resume = deepcopy(config.resume)

    return v0_2.Configuration(description, settings, resources, checkpoints, resume)
