# import pytest
# import random
# import os
# from argparse import Namespace
# from semo import interface

# class TestStress:

#     @pytest.fixture()
#     def generate_files(self, num_files = 100):

#         names = [f"test/data/file_{i}" for i in range(num_files)]
#         for name in names:
#             with open(name, "w") as f:
#                 pass
#         yield names
#         for name in names:
#             os.remove(name)
#         os.remove("test/data/testDB.db")

#     @pytest.fixture()
#     def generate_tags(self, num_tags = 100):
#         yield [f"tag_{i}" for i in range(num_tags)]


    

#     def test_stress(self, generate_files, generate_tags):
#         files = generate_files
#         tags = generate_tags
#         functions = [
#             lambda x: interface.interface_translate_TAG(x),
#             lambda x: interface.interface_translate_UNTAG(x),
#             lambda x: interface.interface_translate_DELTAG(x),
#             lambda x: interface.interface_translate_LISTTAGS(x),
#             lambda x: interface.interface_translate_LISTFILES(x),
#             lambda x: interface.interface_translate_SUBTAG(x),
#             lambda x: interface.interface_translate_LISTSUBTAGS(x)
#         ]

#         for i in range(1000):
#             index = random.randint(0, len(functions) - 1)
#             args = Namespace()
#             match index:
#                 case 0 | 1:
#                     args.filename = random.choice(files)
#                     args.tagname = random.choice(tags)
#                 case 2:
#                     args.tagname = random.choice(tags)
#                 case 3:
#                     args.filename = random.choice(files + [""])
#                 case 4:
#                     args.query = random.choice(tags + [""])
#                 case 5:
#                     args.superior_tag = random.choice(tags)
#                     args.inferior_tag = random.sample(tags, random.randint(1, 5))
#                     args.unassign = random.choice([True, False])
#                 case 6:
#                     args.root_tag = random.choice(tags)

#             functions[index](args)


