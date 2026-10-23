"""Loyiha test runner'i: testlar haqiqiy media papkasiga yozmasligi uchun."""

import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


class KodxTestRunner(DiscoverRunner):
    """
    Test bazasi yaratilishidan (va seed migratsiyalardan) oldin MEDIA_ROOT ni
    vaqtinchalik papkaga almashtiradi va TESTING=True qo'yadi.
    """

    def setup_test_environment(self, **kwargs) -> None:
        super().setup_test_environment(**kwargs)
        self._media_root = tempfile.mkdtemp(prefix="kodx-test-media-")
        settings.MEDIA_ROOT = self._media_root
        settings.TESTING = True

    def teardown_test_environment(self, **kwargs) -> None:
        super().teardown_test_environment(**kwargs)
        shutil.rmtree(self._media_root, ignore_errors=True)
