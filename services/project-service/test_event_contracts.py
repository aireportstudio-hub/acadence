import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker


EVENT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "api-contracts"
    / "project-facts-updated.v1.schema.json"
)


class ProjectFactsUpdatedEventContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with EVENT_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
            cls.schema = json.load(schema_file)
        cls.validator = Draft7Validator(cls.schema, format_checker=FormatChecker())

    def test_v1_event_with_opaque_references_is_valid(self):
        event = {
            "event_id": "8b0fbf9c-9eac-49ad-b7bd-b6ae687fdd9e",
            "event_type": "project.facts.updated",
            "event_version": 1,
            "aggregate_id": "33d670c3-66ec-43ec-9500-3f53d81c66dd",
            "aggregate_version": 7,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "fact_snapshot_version": 7,
                "changed_fact_ids": [
                    "05bc5ee1-c651-495f-81ce-d6ab2c30253e",
                ],
            },
        }

        self.validator.validate(event)

    def test_event_rejects_unknown_version_and_missing_changed_facts(self):
        event = {
            "event_id": "8b0fbf9c-9eac-49ad-b7bd-b6ae687fdd9e",
            "event_type": "project.facts.updated",
            "event_version": 2,
            "aggregate_id": "33d670c3-66ec-43ec-9500-3f53d81c66dd",
            "aggregate_version": 7,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "data": {"fact_snapshot_version": 7, "changed_fact_ids": []},
        }

        self.assertFalse(self.validator.is_valid(event))
