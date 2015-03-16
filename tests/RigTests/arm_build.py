
from kraken import plugins
import kraken.examples.arm_component
from kraken.examples.arm_component import ArmComponent
from kraken.core.profiler import Profiler
import json


Profiler.getInstance().push("arm_build")

arm = ArmComponent("arm")

builder = plugins.getBuilder()
builder.build(arm)

Profiler.getInstance().pop()
print json.dumps(Profiler.getInstance().generateReport(), sort_keys=False, indent=4, separators=(',', ': '))