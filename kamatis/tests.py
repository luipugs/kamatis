from kamatis import util
import os
import shutil
import tempfile
import unittest


class TestMakedirs(unittest.TestCase):

    def test_create(self):
        tempdir = tempfile.gettempdir()
        parent = os.tempnam(tempdir)
        path = os.path.join(parent, 'testdir')
        isdir = util.makedirs(path)
        self.assertEqual(isdir, True)
        self.assertEqual(os.path.isdir(path), True)
        shutil.rmtree(parent)

    def test_existing(self):
        path = tempfile.mkdtemp()
        isdir = util.makedirs(path)
        self.assertEqual(isdir, True)
        os.rmdir(path)

    def test_existing_nondir(self):
        _, path = tempfile.mkstemp()
        isdir = util.makedirs(path)
        self.assertEqual(isdir, False)
        os.unlink(path)

    def test_create_error(self):
        parent = tempfile.mkdtemp()
        os.chmod(parent, 0000)
        path = os.path.join(parent, 'testdir')
        isdir = util.makedirs(path)
        self.assertEqual(isdir, False)
        os.rmdir(parent)


if __name__ == '__main__':
    unittest.main()
