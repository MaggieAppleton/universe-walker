"""Check the browser's actual two-badge fixture model."""

import subprocess
import unittest
from pathlib import Path


class PreviewFixtureTests(unittest.TestCase):
    def test_both_badges_agree_on_confirmed_totals_and_sync_gain(self):
        source = Path(__file__).parents[1] / "design-jig/walking/fresh/states.js"
        result = subprocess.run(["node", "-e", """
const assert = require('node:assert/strict');
global.window = {};
require(process.argv[1]);
const { model, CASES } = window.Walking;
const maggie = model('pending', .65, 'Maggie'), martin = model('pending', .65, 'Martin');
assert.equal(maggie.goal, 10000);
assert.equal(model('apart', .65, 'Maggie').own, 0);
assert.equal(model('apart', .65, 'Martin').own, 9900);
assert.equal(maggie.team, 9900); assert.equal(martin.team, 9900);
assert.equal(maggie.newSteps, 60); assert.equal(martin.newSteps, 40);
assert.equal(maggie.own, 60); assert.equal(martin.own, 9940);
for (const badge of ['Maggie', 'Martin']) {
  const success = model('success', .65, badge);
  assert.equal(success.team, maggie.own + martin.own);
  assert.equal(success.team - success.prevTeam, 100);
  assert.equal(success.own + success.partner, success.team);
  assert.equal(success.newSteps, 0); assert.equal(success.reached, true);
  assert.equal(model('goal', .65, badge).team, 10000);
  assert.equal(model('goal', .65, badge).reached, true);
  for (const {id} of CASES) assert.ok(model(id, .65, badge).newSteps >= 0, id);
}
""", str(source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
