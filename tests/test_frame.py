# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


import unittest

from maro.backends.frame import node, NodeBase, NodeAttribute, FrameNode, FrameBase

from maro.utils.exception.backends_exception import (
    BackendsGetItemInvalidException,
    BackendsSetItemInvalidException,
    BackendsArrayAttributeAccessException)


STATIC_NODE_NUM = 5
DYNAMIC_NODE_NUM = 10

@node("static")
class StaticNode(NodeBase):
    a1 = NodeAttribute("i", 2)
    a2 = NodeAttribute("i2")
    a3 = NodeAttribute("i8")

@node("dynamic")
class DynamicNode(NodeBase):
    b1 = NodeAttribute("f")
    b2 = NodeAttribute("d")

def build_frame(enable_snapshot:bool=False, total_snapshot:int=10, backend_name="np"):

    class MyFrame(FrameBase):
        static_nodes = FrameNode(StaticNode, STATIC_NODE_NUM)
        dynamic_nodes = FrameNode(DynamicNode, DYNAMIC_NODE_NUM)

        def __init__(self):
            super().__init__(enable_snapshot=enable_snapshot, total_snapshot=total_snapshot, backend_name=backend_name)

    return MyFrame()

backends_to_test = ["np", "raw"]

class TestFrame(unittest.TestCase):
    def test_node_number(self):
        """Test if node number same as defined"""
        for backend_name in backends_to_test:
            frame = build_frame(backend_name=backend_name)

            self.assertEqual(STATIC_NODE_NUM, len(frame.static_nodes), backend_name)
            self.assertEqual(DYNAMIC_NODE_NUM, len(frame.dynamic_nodes), backend_name)
    
    def test_node_accessing(self):
        """Test node accessing correct"""
        for backend_name in backends_to_test:

            frame = build_frame(backend_name=backend_name)

            # accessing for 1st node for both static and dynamic node
            static_node: StaticNode = frame.static_nodes[0]
            dynamic_node: DynamicNode = frame.dynamic_nodes[0]

            static_node.a2 = 10
            dynamic_node.b1 = 12.34

            self.assertEqual(10, static_node.a2, msg="a2 attribute should be 10 for 1st static node")
            self.assertAlmostEqual(12.34, dynamic_node.b1, 2, msg="b1 attribute should be 12.34 for 1st dynamic node")

            # check if values correct for multiple nodes
            for node in frame.static_nodes:
                node.a2 = node.index

            # check if the value correct
            for node in frame.static_nodes:
                self.assertEqual(node.index, node.a2, msg=f"static node.a2 should be {node.index}")

            # check slice accessing
            static_node.a1[1] = 12
            static_node.a1[0] = 20

            print(static_node.a1[:])

            self.assertListEqual([20, 12], list(static_node.a1[:]), msg="static node's a1 should be [20, 12]")
            self.assertEqual(20, static_node.a1[0], msg="1st slot of a1 should be 20")
            self.assertEqual(12, static_node.a1[1], msg="2nd slot of a1 should be 12")

            # set again with another way
            static_node.a1[(1, 0)] = (22, 11)

            self.assertListEqual([11, 22], list(static_node.a1[:]), msg="static node a1 should be [11, 22]")

            # another way
            # NOTE: additional value will be ignored
            static_node.a1[:] = (1, 2, 3)

            self.assertListEqual([1, 2], list(static_node.a1[:]), msg="static node a1 should be [1, 2")

    def test_invalid_node_accessing(self):
        for backend_name in backends_to_test:
            frm = build_frame(backend_name=backend_name)

            static_node: StaticNode = frm.static_nodes[0]

            # get attribute value with not supported parameter
            with self.assertRaises(BackendsGetItemInvalidException) as ctx:
                a = static_node.a1["a"]

            with self.assertRaises(BackendsSetItemInvalidException) as ctx:
                static_node.a1["a"] = 1

            with self.assertRaises(BackendsArrayAttributeAccessException) as ctx:
                static_node.a1 = 1

    def test_get_node_info(self):
        for backend_name in backends_to_test:
            """Test if node information correct"""
            frm = build_frame(backend_name=backend_name)

            node_info = frm.get_node_info()

            # if should contains 2 nodes
            self.assertTrue("static" in node_info)
            self.assertTrue("dynamic" in node_info)

            # node number
            self.assertEqual(STATIC_NODE_NUM, node_info["static"]["number"])
            self.assertEqual(DYNAMIC_NODE_NUM, node_info["dynamic"]["number"])

            # check attributes
            self.assertTrue("a1" in node_info["static"]["attributes"])
            self.assertTrue("a2" in node_info["static"]["attributes"])
            self.assertTrue("a3" in node_info["static"]["attributes"])
            self.assertTrue("b1" in node_info["dynamic"]["attributes"])
            self.assertTrue("b2" in node_info["dynamic"]["attributes"])

            # check slot number
            self.assertEqual(2, node_info["static"]["attributes"]["a1"]["slots"])
            self.assertEqual(1, node_info["static"]["attributes"]["a2"]["slots"])


    def test_enable_snapshots(self):
        for backend_name in backends_to_test:
            """Test if snapshot enabled"""
            frame = build_frame(enable_snapshot=True, backend_name=backend_name)

            # snapshots should not be None
            self.assertIsNotNone(frame)

            # length should be 10
            self.assertEqual(10, len(frame.snapshots), msg="snapshot length should be 10")

            # another frame without snapshots enabled
            frame1 = build_frame()

            self.assertIsNone(frame1.snapshots)


    def test_reset(self):
        for backend_name in backends_to_test:
            """Test reset work as expected, reset all attributes to 0"""
            frame = build_frame(backend_name=backend_name)

            frame.static_nodes[0].a1[:] = (1, 234)

            # before reset
            self.assertListEqual([1, 234], list(frame.static_nodes[0].a1[:]), msg="static node's a1 should be [1, 234] before reset")

            frame.reset()

            # after reset
            self.assertListEqual([0, 0], list(frame.static_nodes[0].a1[:]), msg="static node's a1 should be [0, 0] after reset")


if __name__ == "__main__":
    unittest.main()
