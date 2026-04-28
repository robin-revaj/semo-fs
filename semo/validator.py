#!.venv/bin/python3

from semo import database, settings
import logging, pyparsing 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)

class Validation:
    def __init__(self, approved = True, data = None):
        self.approved = approved
        if data is None:
            data = []
        self.data = data
class Validator:
    def __init__(self, database : database.Database):
        self.database = database

    def tag_exists(self, tag_name : str) -> bool:
        output = tag_name in self.database.get_tags()
        logger.info(f"Tag Exists '{tag_name}': {output}")
        return output
    
    def corresponding_tag_type(self, tag_name : str, value : str | int | None) -> bool:
        tag_type = self.database.get_tag_type(tag_name)
        if tag_type == "int":
            return (isinstance(value, int)) or (self.is_integer_string(value))
        if tag_type == "str":
            return (isinstance(value, str))
        return value is None

    def is_integer_string(self, string):
        try:
            _ = int(string)
            return True
        except ValueError:
            return False

    def file_exists(self, file_system : int, inode : int) -> bool:
        output = (file_system, inode) in self.database.get_files()
        logger.info(f"File Exists ({file_system}, {inode}): {output}")
        return output

    def file_has_tag(self, file_system : int, inode : int, tag_name : str) -> bool:
        output = tag_name in self.database._direct_tags_for_file(file_system, inode)
        logger.info(f"File ({file_system}, {inode}) has tag '{tag_name}': {output}")
        return output
    def file_indirectly_has_tag(self, file_system : int, inode : int, tag_name : str) -> bool:
        output = tag_name in self.database.get_tags_for_file(file_system, inode)
        logger.info(f"File ({file_system}, {inode}) has tag '{tag_name}': {output}")
        return output

    def tag_has_direct_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        output = inf_tag_name in self.database._direct_inferiors_for_tag(super_tag_name)
        logger.info(f"Tag '{super_tag_name}' has direct superiority over '{inf_tag_name}': {output}")
        return output

    def tag_has_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        # queue = self.database.list_subtags_for_tag(super_tag_name)
        
        # if inf_tag_name in queue:
        #     logger.info(f"Tag '{super_tag_name}' has superiority over '{inf_tag_name}': True")
        #     return True
        
        # for tag in queue:
        #     if self.__tag_has_superiority(tag, inf_tag_name):
        #         logger.info(f"Tag '{super_tag_name}' has superiority over '{inf_tag_name}': True")
        #         return True
        # logger.info(f"Tag '{super_tag_name}' has superiority over '{inf_tag_name}': False")
        # return False
        return super_tag_name in self.database.get_superiors_tree(inf_tag_name)
    
    def __refresh_path_from_access(self, file_system, inode, filename):
        existing_filename = self.database.get_file_path(file_system, inode)
        if existing_filename != filename:
            self.database.set_file_path(file_system, inode, filename)

    def __approve_string(self, string : str) -> bool:
        pattern = pyparsing.Word(pyparsing.alphanums + "_-")
        try:
            pattern.parse_string(string, parse_all=True)
            logger.info(f"String '{string}' approved by validator")
            return True
        except pyparsing.ParseException:
            logger.info(f"String '{string}' rejected by validator")
            return False
    
    def file_is_isolated(self, file_system, inode : int) -> bool:
        output = len(self.database.get_tags_for_file(file_system, inode)) == 0
        logger.info(f"File ({file_system}, {inode}) is isolated: {output}")
        return output
    
    # def tag_is_isolated(self, tag_name : str) -> bool:
    #     no_attached_files = len(self.database.list_files_for_tag(tag_name)) == 0
    #     no_superiors = len(self.database.list_superior_tags_for_tag(tag_name)) == 0
    #     no_inferiors = len(self.database.list_subtags_for_tag(tag_name)) == 0
    #     logger.info(f"Tag '{tag_name}' has no attached files: {no_attached_files} and no_superiors: {no_superiors} and no_inferiors: {no_inferiors}")
    #     return no_attached_files and no_superiors and no_inferiors

    def approved_tag_operation(self, file_system, inode, filepath, tag, value) -> Validation:
        permit = Validation()
        if not self.file_exists(file_system, inode):
            logger.info(f"File ({file_system}, {inode}) not in database. Creating file record.")
            self.database.new_file(file_system, inode, filepath)
        else:
            self.__refresh_path_from_access(file_system, inode, filepath)

        if not self.tag_exists(tag):
            logger.info(f"Tag '{tag}' does not exist. Creating tag record.")
            if value is None:
                self.database.new_tag(tag)
            elif isinstance(value, str):
                self.database.new_tag(tag, "str")
            elif isinstance(value, int):
                self.database.new_tag(tag, "int")
            else:
                permit.approved = False
                permit.data.append(f"unsupported data type")
        else:
            if not self.corresponding_tag_type(tag, value):
                permit.approved = False
                permit.data.append(f"incorrect data type for tag {tag}")
            if self.file_indirectly_has_tag(file_system, inode, tag):
                permit.approved = False
                permit.data.append(f"{filepath} already tagged {tag}")
        logger.info(f"Approval for tag operation for file ({file_system}, {inode}) and tag '{tag}': {permit.approved}")
        return permit

    def approved_untag_operation(self, file_system, inode, tag, filepath) -> Validation:
        permit = Validation()
        if not self.file_exists(file_system, inode):
            permit.approved = False
            permit.data.append(f"{filepath} does not exist in database.")
            return permit
        self.__refresh_path_from_access(file_system, inode, filepath)
        if not self.file_indirectly_has_tag(file_system, inode, tag):
            permit.approved = False
            permit.data.append(f"{filepath} is not tagged {tag}")
            return permit
        
        logger.info(f"Approval for untag operation for file ({file_system}, {inode}) and tag '{tag}': {permit.approved}")
        direct_tags = self.database._direct_tags_for_file(file_system, inode)
        if tag in direct_tags:
            permit.data.append(tag)
        else:
            inherited_tags = self.database.get_tags_for_file(file_system, inode).intersection(self.database.get_inferiors_tree(tag))
            permit.data.extend(inherited_tags)
        return permit

    def approved_direct_untag_operation(self, file_system, inode, tag, filepath) -> Validation:
        permit = Validation()
        if not self.file_exists(file_system, inode):
            permit.approved = False
            permit.data.append(f"{filepath} does not exist in database.")
            return permit
        self.__refresh_path_from_access(file_system, inode, filepath)
        if not self.file_has_tag(file_system, inode, tag):
            permit.approved = False
            permit.data.append(f"{filepath} is not tagged {tag}")
        
        logger.info(f"Approval for direct untag operation for file ({file_system}, {inode}) and tag '{tag}': {permit.approved}")
        return permit

    def approved_list_for_tag_operation(self, tag_name) -> Validation:
        permit = Validation(self.tag_exists(tag_name))
        logger.info(f"Approval for list for tag operation for tag ({tag_name}): {permit.approved}")
        
        if not permit.approved:
            permit.data.append(f"Tag '{tag_name}' does not exist.")
        
        return permit
    
    def approved_conditional_list_for_tag_operation(self, tag_name, condition) -> Validation:
        permit = self.approved_list_for_tag_operation(tag_name)
        if not permit.approved or not self.corresponding_tag_type(tag_name, condition):
            permit.approved = False
            permit.data.append(f"Tag '{tag_name}' not type corresponding to '{condition}'")
        return permit

    def approved_list_for_file_operation(self, file_system, inode, filepath) -> Validation:
        permit = Validation(self.file_exists(file_system, inode))
        logger.info(f"Approval for list for file operation for file ({file_system}, {inode}): {permit.approved}")
        if not permit.approved:
            permit.data.append(f"'{filepath}' does not exist in database.")
            return permit
        self.__refresh_path_from_access(file_system, inode, filepath)
        return permit

    def approved_del_tag_operation(self, tag_name) -> Validation:
        permit = Validation(self.tag_exists(tag_name))
        logger.info(f"Approval for delete tag operation for tag '{tag_name}': {permit.approved}")
        if not permit.approved:
            permit.data.append(f"Tag '{tag_name}' does not exist.")
        
        return permit

    def approved_subtag_operation(self, super_tag_name, inf_tag_name) -> Validation:
        permit = Validation()
        if super_tag_name == inf_tag_name:
            permit.approved = False
            permit.data.append("Cannot assign tag as subtag of itself.")
            logger.info(f"Approval for subtag operation for superior tag '{super_tag_name}' and inferior tag '{inf_tag_name}': {permit.approved}")
            return permit
        if not self.tag_exists(super_tag_name):
            permit.approved = False
            permit.data.append(f"Superior tag '{super_tag_name}' does not exist.")
        if not self.tag_exists(inf_tag_name):
            permit.approved = False
            permit.data.append(f"Inferior tag '{inf_tag_name}' does not exist.")

        if permit.approved:
            if self.tag_has_superiority(super_tag_name, inf_tag_name):
                permit.approved = False
                permit.data.append(f"Tag '{super_tag_name}' already has superiority over '{inf_tag_name}'.")
            elif self.tag_has_superiority(inf_tag_name, super_tag_name):
                permit.approved = False
                permit.data.append(f"Tag '{inf_tag_name}' already has superiority over '{super_tag_name}' - denied cycle.")
    
        logger.info(f"Approval for subtag operation for superior tag '{super_tag_name}' and inferior tag '{inf_tag_name}': {permit.approved}")
        return permit

    def approved_unsubtag_operation(self, super_tag_name, inf_tag_name) -> Validation:
        permit = Validation()
        if not self.tag_exists(super_tag_name):
            permit.approved = False
            permit.data.append(f"Superior tag '{super_tag_name}' does not exist.")
        if not self.tag_exists(inf_tag_name):
            permit.approved = False
            permit.data.append(f"Inferior tag '{inf_tag_name}' does not exist.")
        if permit.approved:
            if not self.tag_has_direct_superiority(super_tag_name, inf_tag_name):
                permit.approved = False
                permit.data.append(f"Tag '{super_tag_name}' does not have direct superiority over '{inf_tag_name}'.")
        logger.info(f"Approval for unsubtag operation for superior tag '{super_tag_name}' and inferior tag '{inf_tag_name}': {permit.approved}")
        return permit
    
            

        




   
