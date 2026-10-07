"""Public one-message entrypoint stays deterministic and novice-safe."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicEntryTest(unittest.TestCase):
    def test_entrypoint_routes_agent_to_verified_release_and_preserves_notes(self):
        text = (ROOT / 'mneme.md').read_text(encoding='utf-8')
        required = (
            'releases/latest', '.zip.sha256', 'install_v3.py --vault',
            'mneme.py doctor --human', 'mneme.py preferences --human',
            'https://github.com/Mehximus/mneme', 'notlarini silme',
            '.agents/skills/mneme/SKILL.md',
        )
        for phrase in required:
            self.assertIn(phrase, text)
        self.assertNotIn('Mem0 zorunludur', text)
        self.assertNotIn('git reset --hard', text)

    def test_entrypoint_requires_fresh_session_before_memory_success_claim(self):
        text = (ROOT / 'mneme.md').read_text(encoding='utf-8')
        self.assertIn('yeni bir oturum', text)
        self.assertIn('dogrulandi" deme', text)


if __name__ == '__main__':
    unittest.main()
