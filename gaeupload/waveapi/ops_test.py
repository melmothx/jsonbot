#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the ops module."""


import unittest

import ops


class TestOperation(unittest.TestCase):
  """Test case for Operation class."""

  def testFields(self):
    op = ops.Operation(ops.WAVELET_SET_TITLE, 'opid02',
                       {'waveId': 'wavelet-id',
                        'title': 'a title'})
    self.assertEqual(ops.WAVELET_SET_TITLE, op.method)
    self.assertEqual('opid02', op.id)
    self.assertEqual(2, len(op.params))

  def testConstructModifyTag(self):
    q = ops.OperationQueue()
    op = q.wavelet_modify_tag('waveid', 'waveletid', 'tag')
    self.assertEqual(3, len(op.params))
    op = q.wavelet_modify_tag(
        'waveid', 'waveletid', 'tag', modify_how='remove')
    self.assertEqual(4, len(op.params))

  def testConstructRobotFetchWave(self):
    q = ops.OperationQueue('proxyid')
    op = q.robot_fetch_wave('wave1', 'wavelet1')
    self.assertEqual(3, len(op.params))
    self.assertEqual('proxyid', op.params['proxyingFor'])
    self.assertEqual('wave1', op.params['waveId'])
    self.assertEqual('wavelet1', op.params['waveletId'])

if __name__ == '__main__':
  unittest.main()
