#!/usr/bin/env python3

from . import database, settings
import pyparsing
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
class Validator:
    def __init__(self, database : database.Database):
        self.database = database

    def __tag_exists(self, tag_name : str) -> bool:
        output = tag_name in self.database.list_tags()
        logger.info(f"Tag Exists '{tag_name}': {output}")
        return output

    def __file_exists(self, file_system, inode : int) -> bool:
        output = inode in self.database.list_files()
        logger.info(f"File Exists ({file_system}, {inode}): {output}")
        return output

    def __file_has_tag(self, file_system, inode : int, tag_name : str) -> bool:
        output = tag_name in self.database.list_tags_for_file(file_system, inode)
        logger.info(f"File ({file_system}, {inode}) has tag '{tag_name}': {output}")
        return output

    def __tag_has_direct_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        output = inf_tag_name in self.database.list_subtags_for_tag(super_tag_name)
        logger.info(f"Tag '{super_tag_name}' has direct superiority over '{inf_tag_name}': {output}")
        return output

    def __tag_has_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        queue = self.database.list_subtags_for_tag(super_tag_name)
        
        if inf_tag_name in queue:
            logger.info(f"Tag '{super_tag_name}' has superiority over '{inf_tag_name}': True")
            return True
        
        for tag in queue:
            if self.__tag_has_superiority(tag, inf_tag_name):
                logger.info(f"Tag '{super_tag_name}' has superiority over '{inf_tag_name}': True")
                return True
        logger.info(f"Tag '{super_tag_name}' has superiority over '{inf_tag_name}': False")
        return False
    
    def __confirm_path_accuracy(self, file_system, inode, filename):
        existing_filename = self.database.get_file_name(file_system, inode)
        if existing_filename != filename:
            self.database.set_file_name(file_system, inode, filename)

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
        output = len(self.database.list_tags_for_file(file_system, inode)) == 0
        logger.info(f"File ({file_system}, {inode}) is isolated: {output}")
        return output
    
    def tag_is_isolated(self, tag_name : str) -> bool:
        no_attached_files = len(self.database.list_files_for_tag(tag_name)) == 0
        no_superiors = len(self.database.list_superior_tags_for_tag(tag_name)) == 0
        no_inferiors = len(self.database.list_subtags_for_tag(tag_name)) == 0
        logger.info(f"Tag '{tag_name}' has no attached files: {no_attached_files} and no_superiors: {no_superiors} and no_inferiors: {no_inferiors}")
        return no_attached_files and no_superiors and no_inferiors

    def approved_tag_operation(self, file_system, inode, filename, tag) -> bool:
        if not self.__tag_exists(tag):
            logger.info(f"Tag '{tag}' does not exist. Creating tag record.")
            self.database.new_tag(tag)

        if not self.__file_exists(file_system, inode):
            logger.info(f"File ({file_system}, {inode}) not in database. Creating file record.")
            self.database.new_file(file_system, inode, filename)
        else:
            self.__confirm_path_accuracy(file_system, inode, filename)

        permit = not self.__file_has_tag(file_system, inode, tag)
        logger.info(f"Approval for tag operation for file ({file_system}, {inode}) and tag '{tag}': {permit}")
        return permit
        

    def approved_untag_operation(self, file_system, inode, tag) -> bool:
        permit = ( self.__file_exists(file_system, inode) and self.__file_has_tag(file_system, inode, tag) )
        logger.info(f"Approval for untag operation for file ({file_system}, {inode}) and tag '{tag}': {permit}")
        return permit

    def approved_list_for_tag_operation(self, tag_name) -> bool:
        permit = self.__tag_exists(tag_name)
        logger.info(f"Approval for list for tag operation for tag '{tag_name}': {permit}")
        return permit

    def approved_list_for_file_operation(self, file_system, inode) -> bool:
        permit = self.__file_exists(file_system, inode)
        logger.info(f"Approval for list for file operation for file ({file_system}, {inode}): {permit}")
        return permit

    def approved_del_tag_operation(self, tag_name) -> bool:
        permit = self.__tag_exists(tag_name)
        logger.info(f"Approval for delete tag operation for tag '{tag_name}': {permit}")
        return permit

    def approved_subtag_operation(self, super_tag_name, inf_tag_name) -> bool:
        if not self.__tag_exists(super_tag_name):
            logger.info(f"Superior tag '{super_tag_name}' does not exist. Aborting.")
            return False
        if not self.__tag_exists(inf_tag_name):
            logger.info(f"Inferior tag '{inf_tag_name}' does not exist. Creating tag record.")
            self.database.new_tag(inf_tag_name)
        conflicting_hierarchy = (self.__tag_has_direct_superiority(super_tag_name, inf_tag_name) or self.__tag_has_superiority(inf_tag_name, super_tag_name))
        logger.info(f"Approval for subtag operation for superior tag '{super_tag_name}' and inferior tag '{inf_tag_name}': Not exists conflicting hierarchy: {not conflicting_hierarchy}")
        return not conflicting_hierarchy

    def approved_unsubtag_operation(self, super_tag_name, inf_tag_name) -> bool:
        if not self.__tag_exists(super_tag_name) or not self.__tag_exists(inf_tag_name):
            logger.info(f"One of the tags '{super_tag_name}' or '{inf_tag_name}' does not exist. Aborting.")
            return False
        permit = self.__tag_has_direct_superiority(super_tag_name, inf_tag_name)
        logger.info(f"Approval for unsubtag operation for superior tag '{super_tag_name}' and inferior tag '{inf_tag_name}': {permit}")
        return permit
    
    def parse_query(self, query : str) -> list:
        # config

        atom = pyparsing.Word(pyparsing.alphanums + "_")
        operator = pyparsing.one_of("& | -")

        # parsers

        unsplitable_particle = pyparsing.Or(( atom, operator ))
        wrapped_entity = pyparsing.Suppress("(") + ... + pyparsing.Suppress(")")
        parser = pyparsing.Or((
                atom,
                wrapped_entity,
                atom + operator + atom,
                atom + operator + wrapped_entity,
                wrapped_entity + operator + atom,
                wrapped_entity + operator + wrapped_entity ))

        def split_expression(string):
                try:
                    unsplitable_particle.parse_string(string, parse_all=True)
                    return string
                except:
                    partitioned = parser.parse_string(string).as_list()
                    for i, item in enumerate(partitioned):
                        if isinstance(item, str):
                            partitioned[i] = split_expression(item)
                    if len(partitioned) == 1:
                        partitioned = partitioned[0]
                    return partitioned

        output = split_expression(query)
        if isinstance(output, str) : return [output]
        return output
            

        




   
