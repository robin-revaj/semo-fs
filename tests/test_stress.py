
# import unittest, os, sys, pwd, random, time
# user = pwd.getpwuid(os.getuid()).pw_name
# sys.path.append(f"/home/{user}/.semo/semo")
# from argparse import Namespace
# from semo import interface, utils


# class TestStress(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls) -> None:
#         cls.count = 1000
#         cls.path = utils.get_test_db()
#         utils.set_working_db(cls.path)
#         cls.paths = [f"tests/data/file_{i}" for i in range(cls.count)]
#         for path in cls.paths:
#             with open(path, "w") as f:
#                 pass
#         cls.tags = [
#             [f"tagnull_{i}" for i in range(cls.count)],
#             [f"tagstr_{i}" for i in range(cls.count)],
#             [f"tagint_{i}" for i in range(cls.count)]
#             ]
#         cls.values = [
#             lambda: None,
#             lambda: "text" + str(random.randint(1,100)),
#             lambda: random.randint(1,100)
#         ]
#         return super().setUpClass()

#     @classmethod
#     def tearDownClass(cls):
#         os.remove(cls.path)
#         utils.set_working_db()
#         for path in cls.paths:
#             os.remove(path)

#     # @pytest.fixture()
#     # def generate_files(self, num_files = 100):

#     #     names = [f"test/data/file_{i}" for i in range(num_files)]
#     #     for name in names:
#     #         with open(name, "w") as f:
#     #             pass
#     #     yield names
#     #     for name in names:
#     #         os.remove(name)
#     #     os.remove("test/data/testDB.db")

#     # @pytest.fixture()
#     # def generate_tags(self, num_tags = 100):
#     #     yield [f"tag_{i}" for i in range(num_tags)]

#     def test_all_funcs(self):
#         functions = [
#             lambda x: interface.translate_TAG(x, True),
#             lambda x: interface.translate_UNTAG(x, True),
#             lambda x: interface.translate_DELTAG(x, True),
#             lambda x: interface.translate_LISTTAGS(x, True),
#             lambda x: interface.translate_LISTFILES(x, True),
#             lambda x: interface.translate_SUBTAG(x, True),
#             lambda x: interface.translate_LISTSUBTAGS(x, True)
#         ]

#         for i in range(1000):
#             index = random.randint(0, len(functions) - 1)
#             t = random.randint(0,2)
#             tag = self.tags[t][random.randint(0,999)]
#             f = random.choice(self.paths)

#             args = Namespace()
#             match index:
#                 case 0 | 1:
#                     args.filename = f
#                     args.tagname = tag
#                     args.value = self.values[t]()
#                 case 2:
#                     args.tagname = tag
#                 case 3:
#                     args.filename = random.choice(self.paths + [""])
#                 case 4:
#                     args.query = tag
#                 case 5:
#                     args.superior_tag = tag
#                     args.inferior_tag = random.sample(self.tags[t], random.randint(1, 5))
#                     args.unassign = random.choice([True, False])
#                 case 6:
#                     args.tagname = tag
#                     args.direct = True

#             functions[index](args)

#     def test_tag_operations_one_file(self):
#         limit = False
#         ep = 1
#         while not limit:
#             start = time.time()
#             for i in range(50):
#                 t = random.randint(0,2)
#                 args = Namespace()
#                 args.tagname = self.tags[t][random.randint(0,999)]
#                 args.filename = self.paths[0]
#                 args.value = self.values[t]()
#                 interface.translate_TAG(args, True)
#             t = time.time() - start
#             limit = t > 1
#             print(ep, t)
#             ep += 1

