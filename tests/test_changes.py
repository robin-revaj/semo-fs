#! /usr/bin/env python3

import unittest, os, sys, pwd, time
user = pwd.getpwuid(os.getuid()).pw_name
sys.path.append(f"/home/{user}/.semo/semo")
from semo import backend as backend, database as db, utils as utils, interface as cli
from utils import SemoException
from argparse import Namespace


class TestChanges(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:

        backend.daemon_pid()

        cls.path = utils.get_test_db()
        utils.set_working_db(cls.path)
        cls.DB = db.Database(cls.path)
        cls.DB.init_create_script()
        cls.loc = os.path.abspath("tests/data")
        cli.translate_WATCH(Namespace(path=cls.loc), suppress=True)
        cls.folders = [cls.loc + "/chfolder1", cls.loc + "/chfolder2"]
        os.mkdir(cls.folders[0])
        os.mkdir(cls.folders[1])
        files = [open(cls.loc + "/chfolder1/file1.txt", "w"),
                 open(cls.loc + "/chfolder2/file2.txt", "w"),
                 open(cls.loc + "/file3.txt", "w")]
        cls.files = []
        for f in files:
            cls.files.append(f.name)
            f.close()

        return super().setUpClass()
    @classmethod
    def tearDownClass(cls) -> None:
        utils.set_working_db(utils.get_default_db())
        os.remove(cls.path)
        for f in cls.files:
            os.remove(f)
        for folder in cls.folders:
            os.rmdir(folder)
        cli.translate_UNWATCH(Namespace(path=cls.loc), suppress=True)
        return super().tearDownClass()
    
    def tearDown(self):
        self.DB.clear_contents()

    def test_watch_and_listwatches(self):
        os.mkdir("tests/folder")
        p = os.path.abspath("tests/folder")
        cli.translate_WATCH(Namespace(path=p), suppress=True)
        watches = cli.translate_LISTWATCHES(Namespace(), suppress=True)
        self.assertIn(p, watches)
        cli.translate_UNWATCH(Namespace(path=p), suppress=True)
        watches = cli.translate_LISTWATCHES(Namespace(), suppress=True)
        self.assertNotIn(p, watches)
        os.rmdir("tests/folder")

    def test_watch_nonexistent(self):
        self.assertEqual("invalid directory path", cli.translate_WATCH(Namespace(path=self.loc + "/nonexistent"), suppress=True))
    
    def test_unwatch_unwatched(self):
        self.assertEqual("directory not watched", cli.translate_UNWATCH(Namespace(path=self.loc + "/nonexistent"), suppress=True))

    def test_delete_file(self):
        cli.translate_TAG(Namespace(filename=self.files[1], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[1])}, cli.translate_LISTFILES(Namespace(query=""), suppress=True))
        self.assertEqual({('testtag', self.files[1])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.remove(self.files[1])
        time.sleep(0.1)
        self.assertEqual(set(), cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        open(self.files[1], "w").close()
        time.sleep(0.1)

    def test_delete_folder(self):
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        cli.translate_TAG(Namespace(filename=self.files[1], tagname="testtag", value=None), suppress=True)
        self.assertEqual(len(cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True)), 2)
        os.remove(self.files[0])
        os.rmdir(self.folders[0])
        time.sleep(0.1)
        self.assertEqual(len(cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True)), 1)
        os.mkdir(self.folders[0])
        with open(self.files[0], 'w') as f:
            pass
        time.sleep(0.1)

    def test_rename_file(self):
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[0])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.files[0], self.loc + "/chfolder1/file.txt")
        time.sleep(0.1)
        self.assertEqual({('testtag', self.loc + "/chfolder1/file.txt")}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.loc + "/chfolder1/file.txt", self.files[0])
        time.sleep(0.1)

    def test_rename_folder(self):
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[0])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.folders[0], self.loc + "/chfolder")
        time.sleep(0.1)
        self.assertEqual({('testtag', self.loc + "/chfolder/file1.txt")}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.loc + "/chfolder", self.folders[0])
        time.sleep(0.1)

    def test_move_file(self):
        newpath = self.loc + "/chfolder2/file1.txt"
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[0])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.files[0], newpath)
        time.sleep(0.1)
        self.assertEqual({('testtag', newpath)}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(newpath, self.files[0])
        time.sleep(0.1)

    def test_move_folder(self):
        newpath = self.loc + "/chfolder2/chfolder1"
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[0])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.folders[0], newpath)
        time.sleep(0.1)
        self.assertEqual({('testtag', newpath + "/file1.txt")}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(newpath, self.folders[0])
        time.sleep(0.1)

    def test_move_file_gone(self):
        newpath = os.path.abspath("tests/file1.txt")
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[0])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.files[0], newpath)
        time.sleep(2)
        self.assertEqual(set(), cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(newpath, self.files[0])
        time.sleep(0.1)

    def test_move_folder_gone(self):
        newpath = os.path.abspath("tests/chfolder1")
        cli.translate_TAG(Namespace(filename=self.files[0], tagname="testtag", value=None), suppress=True)
        self.assertEqual({('testtag', self.files[0])}, cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(self.folders[0], newpath)
        time.sleep(2)
        self.assertEqual(set(), cli.translate_LISTFILES(Namespace(query="testtag"), suppress=True))
        os.rename(newpath, self.folders[0])
        time.sleep(0.1)



if __name__ == '__main__':
    #sys.path.append("/home/mercury/Documents/Motherboard/Semester/BC_THESIS/semo_root")

    
    unittest.main()