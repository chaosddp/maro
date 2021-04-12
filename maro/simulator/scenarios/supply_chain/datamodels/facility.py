# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from maro.backends.backend import AttributeType
from maro.backends.frame import NodeAttribute, node

from .base import DataModelBase


@node("facility")
class FacilityDataModel(DataModelBase):

    def __init__(self):
        super(FacilityDataModel, self).__init__()

    def reset(self):
        super(FacilityDataModel, self).reset()