import unittest

import _paths  # noqa: F401
from ecoguard_common import urls

SHA = "a" * 64


class UrlTests(unittest.TestCase):
    def test_media_and_thumb_keys(self):
        self.assertEqual(urls.media_key(SHA, "my fox.jpg"), f"media/{SHA}/my_fox.jpg")
        self.assertEqual(urls.thumb_key(SHA), f"thumbs/{SHA}.jpg")

    def test_safe_filename(self):
        self.assertEqual(urls.safe_filename("../../etc/passwd"), "passwd")
        self.assertEqual(urls.safe_filename("C:\\pics\\a b.png"), "a_b.png")
        self.assertEqual(urls.safe_filename(""), "upload")
        self.assertEqual(urls.safe_filename(None), "upload")
        self.assertLessEqual(len(urls.safe_filename("x" * 500)), 100)

    def test_virtual_hosted_presigned_url(self):
        url = f"https://bkt.s3.ap-southeast-2.amazonaws.com/media/{SHA}/fox.jpg?X-Amz-Signature=abc&X-Amz-Expires=3600"
        self.assertEqual(urls.key_from_url(url), f"media/{SHA}/fox.jpg")
        self.assertEqual(urls.file_id_from_url(url), SHA)

    def test_path_style_url_with_bucket_prefix(self):
        url = f"https://s3.ap-southeast-2.amazonaws.com/bkt/thumbs/{SHA}.jpg?X-Amz-Signature=abc"
        self.assertEqual(urls.file_id_from_url(url), SHA)

    def test_s3_scheme(self):
        self.assertEqual(urls.file_id_from_url(f"s3://bkt/media/{SHA}/fox.jpg"), SHA)

    def test_rejects_foreign_urls(self):
        for bad in ("", None, "ftp://x/y", "https://example.com/", "https://bkt.s3.amazonaws.com/other/file.jpg",
                    "https://bkt.s3.amazonaws.com/media/not-a-hash/f.jpg"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    urls.file_id_from_url(bad)

    def test_is_sha256(self):
        self.assertTrue(urls.is_sha256(SHA))
        self.assertFalse(urls.is_sha256("A" * 64))  # upper-case is normalised before this check
        self.assertFalse(urls.is_sha256("abc"))


if __name__ == "__main__":
    unittest.main()
