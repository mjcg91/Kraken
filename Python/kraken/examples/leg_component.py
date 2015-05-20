from kraken.core.maths import Vec3
from kraken.core.maths.xfo import Xfo
from kraken.core.maths.xfo import xfoFromDirAndUpV

from kraken.core.objects.components.component import Component

from kraken.core.objects.attributes.attribute_group import AttributeGroup
from kraken.core.objects.attributes.float_attribute import FloatAttribute
from kraken.core.objects.attributes.bool_attribute import BoolAttribute

from kraken.core.objects.constraints.pose_constraint import PoseConstraint

from kraken.core.objects.component_group import ComponentGroup
from kraken.core.objects.hierarchy_group import HierarchyGroup
from kraken.core.objects.locator import Locator
from kraken.core.objects.joint import Joint
from kraken.core.objects.ctrlSpace import CtrlSpace
from kraken.core.objects.control import Control

from kraken.core.objects.operators.splice_operator import SpliceOperator

from kraken.core.profiler import Profiler
from kraken.helpers.utility_methods import logHierarchy


class LegComponentGuide(Component):
    """Leg Component Guide"""

    def __init__(self, name='legGuide', parent=None, data=None):
        super(LegComponentGuide, self).__init__(name, parent)

        # Declare Inputs Xfos
        self.legPelvisInput = self.addInput('pelvisInput', dataType='Xfo')

        # Declare Output Xfos
        self.femurOutput = self.addOutput('femur', dataType='Xfo')
        self.shinOutput = self.addOutput('shin', dataType='Xfo')
        self.legEndXfoOutput = self.addOutput('legEndXfo', dataType='Xfo')
        self.legEndPosOutput = self.addOutput('legEndPos', dataType='Xfo')

        # Declare Input Attrs

        # Declare Output Attrs

        # =========
        # Controls
        # =========
        controlsLayer = self.getOrCreateLayer('controls')
        ctrlCmpGrp = ComponentGroup(self.getName(), self, parent=controlsLayer)

        # IO Hierarchies
        inputHrcGrp = HierarchyGroup('inputs', parent=ctrlCmpGrp)
        cmpInputAttrGrp = AttributeGroup('inputs', parent=inputHrcGrp)

        outputHrcGrp = HierarchyGroup('outputs', parent=ctrlCmpGrp)
        cmpOutputAttrGrp = AttributeGroup('outputs', parent=outputHrcGrp)

        # Guide Controls
        self.femurCtrl = Control('femur', parent=ctrlCmpGrp, shape="sphere")
        self.kneeCtrl = Control('knee', parent=ctrlCmpGrp, shape="sphere")
        self.ankleCtrl = Control('ankle', parent=ctrlCmpGrp, shape="sphere")

        if data is None:
            data = {
                    "name": name,
                    "location": "L",
                    "femurXfo": Xfo(Vec3(0.9811, 9.769, -0.4572)),
                    "kneeXfo": Xfo(Vec3(1.4488, 5.4418, -0.5348)),
                    "ankleXfo": Xfo(Vec3(1.841, 1.1516, -1.237))
                   }

        self.loadData(data)


    # =============
    # Data Methods
    # =============
    def saveData(self):
        """Save the data for the component to be persisted.


        Return:
        The JSON data object

        """

        data = {
                'name': self.getName(),
                'location': self.getLocation(),
                'femurXfo': self.femurCtrl.xfo,
                'kneeXfo': self.kneeCtrl.xfo,
                'ankleXfo': self.ankleCtrl.xfo
               }

        return data


    def loadData(self, data):
        """Load a saved guide representation from persisted data.

        Arguments:
        data -- object, The JSON data object.

        Return:
        True if successful.

        """

        if 'name' in data:
            self.setName(data['name'])

        self.setLocation(data['location'])
        self.femurCtrl.xfo = data['femurXfo']
        self.kneeCtrl.xfo = data['kneeXfo']
        self.ankleCtrl.xfo = data['ankleXfo']

        return True


    def getGuideData(self):
        """Returns the Guide data used by the Rig Component to define the layout of the final rig..

        Return:
        The JSON rig data object.

        """

        # Values
        femurPosition = self.femurCtrl.xfo.tr
        kneePosition = self.kneeCtrl.xfo.tr
        anklePosition = self.ankleCtrl.xfo.tr

        # Calculate Bicep Xfo
        rootToWrist = anklePosition.subtract(femurPosition).unit()
        rootToKnee = kneePosition.subtract(femurPosition).unit()

        bone1Normal = rootToWrist.cross(rootToKnee).unit()
        bone1ZAxis = rootToKnee.cross(bone1Normal).unit()

        femurXfo = Xfo()
        femurXfo.setFromVectors(rootToKnee, bone1Normal, bone1ZAxis, femurPosition)

        # Calculate Forearm Xfo
        elbowToWrist = anklePosition.subtract(kneePosition).unit()
        elbowToRoot = femurPosition.subtract(kneePosition).unit()
        bone2Normal = elbowToRoot.cross(elbowToWrist).unit()
        bone2ZAxis = elbowToWrist.cross(bone2Normal).unit()

        kneeXfo = Xfo()
        kneeXfo.setFromVectors(elbowToWrist, bone2Normal, bone2ZAxis, kneePosition)

        femurLen = femurPosition.subtract(kneePosition).length()
        shinLen = kneePosition.subtract(anklePosition).length()

        ankleXfo = Xfo()
        ankleXfo.tr = anklePosition
        ankleXfo.ori = kneeXfo.ori

        upVXfo = xfoFromDirAndUpV(femurPosition, anklePosition, kneePosition)
        upVXfo.tr = kneePosition
        upVXfo.tr = upVXfo.transformVector(Vec3(0, 0, 5))

        data = {
                "class":"kraken.examples.leg_component.LegComponent",
                "name": self.getName(),
                "location":self.getLocation(),
                "femurXfo": femurXfo,
                "kneeXfo": kneeXfo,
                "ankleXfo": ankleXfo,
                "upVXfo": upVXfo,
                "femurLen": femurLen,
                "shinLen": shinLen
               }

        return data


class LegComponent(Component):
    """Leg Component"""

    def __init__(self, name='leg', parent=None):

        Profiler.getInstance().push("Construct Leg Component:" + name)
        super(LegComponent, self).__init__(name, parent)

        # Declare Inputs Xfos
        self.legPelvisInput = self.addInput('pelvisInput', dataType='Xfo')

        # Declare Output Xfos
        self.femurOutput = self.addOutput('femur', dataType='Xfo')
        self.shinOutput = self.addOutput('shin', dataType='Xfo')
        self.legEndXfoOutput = self.addOutput('legEndXfo', dataType='Xfo')
        self.legEndPosOutput = self.addOutput('legEndPos', dataType='Xfo')

        # Declare Input Attrs
        self.debugInput = self.addInput('debug', dataType='Boolean')
        self.rightSideInput = self.addInput('rightSide', dataType='Boolean')

        # Declare Output Attrs
        self.debugOutput = self.addOutput('debug', dataType='Boolean')

        # =========
        # Controls
        # =========
        controlsLayer = self.getOrCreateLayer('controls')
        ctrlCmpGrp = ComponentGroup(self.getName(), self, parent=controlsLayer)

        # IO Hierarchies
        inputHrcGrp = HierarchyGroup('inputs', parent=ctrlCmpGrp)
        cmpInputAttrGrp = AttributeGroup('inputs', parent=inputHrcGrp)

        outputHrcGrp = HierarchyGroup('outputs', parent=ctrlCmpGrp)
        cmpOutputAttrGrp = AttributeGroup('outputs', parent=outputHrcGrp)

        # Femur
        self.femurFKCtrlSpace = CtrlSpace('femurFK', parent=ctrlCmpGrp)
        self.femurFKCtrl = Control('femurFK', parent=self.femurFKCtrlSpace, shape="cube")
        self.femurFKCtrl.alignOnXAxis()

        # Shin
        self.shinFKCtrlSpace = CtrlSpace('shinFK', parent=self.femurFKCtrl)
        self.shinFKCtrl = Control('shinFK', parent=self.shinFKCtrlSpace, shape="cube")
        self.shinFKCtrl.alignOnXAxis()

        # Ankle
        self.legIKCtrlSpace = CtrlSpace('IK', parent=ctrlCmpGrp)
        self.legIKCtrl = Control('IK', parent=self.legIKCtrlSpace, shape="pin")


        # Add Component Params to IK control
        legSettingsAttrGrp = AttributeGroup("DisplayInfo_LegSettings",
            parent=self.legIKCtrl)
        legDebugInputAttr = BoolAttribute('debug', value=True,
            parent=legSettingsAttrGrp)
        self.legBone1LenInputAttr = FloatAttribute('bone1Len', value=1.0,
            parent=legSettingsAttrGrp)
        self.legBone2LenInputAttr = FloatAttribute('bone2Len', value=1.0,
            parent=legSettingsAttrGrp)
        legFkikInputAttr = FloatAttribute('fkik', value=1.0, minValue=0.0,
            maxValue=1.0, parent=legSettingsAttrGrp)
        legSoftIKInputAttr = BoolAttribute('softIK', value=True)
        legSoftDistInputAttr = FloatAttribute('softDist', value=0.0,
            minValue=0.0, parent=legSettingsAttrGrp)
        legStretchInputAttr = BoolAttribute('stretch', value=True)
        legStretchBlendInputAttr = FloatAttribute('stretchBlend', value=0.0,
            minValue=0.0, maxValue=1.0, parent=legSettingsAttrGrp)

        # UpV
        self.legUpVCtrlSpace = CtrlSpace('UpV', parent=ctrlCmpGrp)
        self.legUpVCtrl = Control('UpV', parent=self.legUpVCtrlSpace, shape="triangle")
        self.legUpVCtrl.alignOnZAxis()


        # ==========
        # Deformers
        # ==========
        deformersLayer = self.getOrCreateLayer('deformers')
        defCmpGrp = ComponentGroup(self.getName(), self, parent=deformersLayer)

        femurDef = Joint('femur', parent=defCmpGrp)
        femurDef.setComponent(self)

        shinDef = Joint('shin', parent=defCmpGrp)
        shinDef.setComponent(self)

        ankleDef = Joint('ankle', parent=defCmpGrp)
        ankleDef.setComponent(self)


        # =====================
        # Create Component I/O
        # =====================
        # Setup component Xfo I/O's
        self.legPelvisInputTgt = Locator('pelvisInput', parent=inputHrcGrp)

        self.femurOutputTgt = Locator('femur', parent=outputHrcGrp)
        self.shinOutputTgt = Locator('shin', parent=outputHrcGrp)
        self.legEndXfoOutputTgt = Locator('legEndXfo', parent=outputHrcGrp)
        self.legEndPosOutputTgt = Locator('legEndPos', parent=outputHrcGrp)

        # Set IO Targets
        self.legPelvisInput.setTarget(self.legPelvisInputTgt)

        self.femurOutput.setTarget(self.femurOutputTgt)
        self.shinOutput.setTarget(self.shinOutputTgt)
        self.legEndXfoOutput.setTarget(self.legEndXfoOutputTgt)
        self.legEndPosOutput.setTarget(self.legEndPosOutputTgt)


        # Setup component Attribute I/O's
        debugInputAttr = BoolAttribute('debug', value=True,
            parent=cmpInputAttrGrp)
        self.rightSideInputAttr = BoolAttribute('rightSide', value=True,
            parent=cmpInputAttrGrp)

        debugOutputAttr = BoolAttribute('debug', value=True, parent=cmpOutputAttrGrp)

        # Set IO Targets
        self.debugInput.setTarget(debugInputAttr)
        self.rightSideInput.setTarget(self.rightSideInputAttr)

        self.debugOutput.setTarget(debugOutputAttr)


        # ==============
        # Constrain I/O
        # ==============
        # Constraint inputs
        legRootInputConstraint = PoseConstraint('_'.join([self.legIKCtrl.getName(), 'To', self.legPelvisInputTgt.getName()]))
        legRootInputConstraint.setMaintainOffset(True)
        legRootInputConstraint.addConstrainer(self.legPelvisInputTgt)
        self.femurFKCtrlSpace.addConstraint(legRootInputConstraint)

        # Constraint outputs


        # ==================
        # Add Component I/O
        # ==================
        # Add Xfo I/O's
        # self.addInput(self.legPelvisInputTgt)
        # self.addOutput(self.femurOutputTgt)
        # self.addOutput(self.shinOutputTgt)
        # self.addOutput(self.legEndXfoOutputTgt)
        # self.addOutput(self.legEndPosOutputTgt)

        # Add Attribute I/O's
        # self.addInput(debugInputAttr)
        # self.addInput(self.legBone1LenInputAttr)
        # self.addInput(self.legBone2LenInputAttr)
        # self.addInput(legFkikInputAttr)
        # self.addInput(legSoftIKInputAttr)
        # self.addInput(legSoftDistInputAttr)
        # self.addInput(legStretchInputAttr)
        # self.addInput(legStretchBlendInputAttr)
        # self.addInput(self.rightSideInputAttr)


        # ===============
        # Add Splice Ops
        # ===============
        # Add Splice Op
        # spliceOp = SpliceOperator("legSpliceOp", "LimbSolver", "KrakenLimbSolver")
        # self.addOperator(spliceOp)

        # # Add Att Inputs
        # spliceOp.setInput("debug", debugInputAttr)
        # spliceOp.setInput("bone1Len", self.legBone1LenInputAttr)
        # spliceOp.setInput("bone2Len", self.legBone2LenInputAttr)
        # spliceOp.setInput("fkik", legFkikInputAttr)
        # spliceOp.setInput("softIK", legSoftIKInputAttr)
        # spliceOp.setInput("softDist", legSoftDistInputAttr)
        # spliceOp.setInput("stretch", legStretchInputAttr)
        # spliceOp.setInput("stretchBlend", legStretchBlendInputAttr)
        # spliceOp.setInput("rightSide", self.rightSideInputAttr)

        # # Add Xfo Inputs
        # spliceOp.setInput("root", self.legPelvisInputTgt)
        # spliceOp.setInput("bone1FK", femurFKCtrl)
        # spliceOp.setInput("bone2FK", shinFKCtrl)
        # spliceOp.setInput("ikHandle", self.legIKCtrl)
        # spliceOp.setInput("upV", self.legUpVCtrl)

        # # Add Xfo Outputs
        # spliceOp.setOutput("bone01Out", self.femurOutputTgt)
        # spliceOp.setOutput("bone02Out", self.shinOutputTgt)
        # spliceOp.setOutput("bone03Out", self.legEndXfoOutputTgt)
        # spliceOp.setOutput("bone03PosOut", self.legEndPosOutputTgt)


        # # Add Deformer Splice Op
        # spliceOp = SpliceOperator("legDeformerSpliceOp", "LimbConstraintSolver", "KrakenLimbSolver")
        # self.addOperator(spliceOp)

        # # Add Att Inputs
        # spliceOp.setInput("debug", debugInputAttr)

        # # Add Xfo Inputstrl)
        # spliceOp.setInput("bone01Constrainer", self.femurOutputTgt)
        # spliceOp.setInput("bone02Constrainer", self.shinOutputTgt)
        # spliceOp.setInput("bone03Constrainer", self.legEndXfoOutputTgt)

        # # Add Xfo Outputs
        # spliceOp.setOutput("bone01Deformer", femurDef)
        # spliceOp.setOutput("bone02Deformer", shinDef)
        # spliceOp.setOutput("bone03Deformer", ankleDef)

        Profiler.getInstance().pop()


    def loadData(self, data=None):

        self.setName(data.get('name', 'leg'))
        location = data.get('location', 'M')
        self.setLocation(location)

        self.femurFKCtrlSpace.xfo = data['femurXfo']
        self.femurFKCtrl.xfo = data['femurXfo']
        self.femurFKCtrl.scalePoints(Vec3(data['femurLen'], 1.75, 1.75))

        self.femurOutputTgt.xfo = data['femurXfo']
        self.shinOutputTgt.xfo = data['kneeXfo']

        self.shinFKCtrlSpace.xfo = data['kneeXfo']
        self.shinFKCtrl.xfo = data['kneeXfo']
        self.shinFKCtrl.scalePoints(Vec3(data['shinLen'], 1.5, 1.5))

        self.legIKCtrlSpace.xfo.tr = data['ankleXfo'].tr
        self.legIKCtrl.xfo.tr = data['ankleXfo'].tr

        if self.getLocation() == "R":
            self.legIKCtrl.rotatePoints(0, 90, 0)
            self.legIKCtrl.translatePoints(Vec3(-1.0, 0.0, 0.0))
        else:
            self.legIKCtrl.rotatePoints(0, -90, 0)
            self.legIKCtrl.translatePoints(Vec3(1.0, 0.0, 0.0))

        self.legUpVCtrlSpace.xfo = data['upVXfo']
        self.legUpVCtrl.xfo = data['upVXfo']

        self.rightSideInputAttr.setValue(self.getLocation() is 'R')
        self.legBone1LenInputAttr.setMin(0.0)
        self.legBone1LenInputAttr.setMax(data['femurLen'] * 3.0)
        self.legBone1LenInputAttr.setValue(data['femurLen'])
        self.legBone2LenInputAttr.setMin(0.0)
        self.legBone2LenInputAttr.setMax(data['shinLen'] * 3.0)
        self.legBone2LenInputAttr.setValue(data['shinLen'])

        self.legPelvisInputTgt.xfo = data['femurXfo']

        self.legEndXfoOutputTgt.xfo = data['ankleXfo']
        self.legEndPosOutputTgt.xfo.tr = data['ankleXfo'].tr


from kraken.core.kraken_system import KrakenSystem
ks = KrakenSystem.getInstance()
ks.registerComponent(LegComponent)
ks.registerComponent(LegComponentGuide)
