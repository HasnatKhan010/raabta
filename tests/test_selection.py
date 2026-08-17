from __future__ import annotations

import unittest

from raabta.data.selection import infer_project_domain, select_deterministic_subset


class SelectionTests(unittest.TestCase):
    def test_project_domain_is_auditable(self) -> None:
        self.assertEqual(
            infer_project_domain("پاکستان", "اسلام آباد پاکستان کا شہر ہے"), "pakistan"
        )

    def test_selection_is_independent_of_input_order(self) -> None:
        records = [
            {"id": str(index), "title": f"مضمون {index}", "url": "", "text": "عام " * 10}
            for index in range(20)
        ]
        first = select_deterministic_subset(records, 5, {"general"}, 42, 1)
        second = select_deterministic_subset(reversed(records), 5, {"general"}, 42, 1)
        self.assertEqual([item.article_id for item in first], [item.article_id for item in second])


if __name__ == "__main__":
    unittest.main()
