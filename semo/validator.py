#! /usr/bin/env python3

"""Provides functions to check if conditions are met for changes and functions to be performed

File should be imported as a module.

Contains the following classes:

    * Validation
    * Validator
"""

import database, utils
import logging, pyparsing 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(utils.get_log_file())
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)

class Validation:
    """Container for boolean approval and a list of reasons for decision
    
    Attributes
    ----------
    approved : bool
    data : list
    """

    def __init__(self, approved = True, data = []):
        """
        Parameters
        ----------
        approved : str, optional
            Default is True
        data : list, optional
            Default is []
        """

        self.approved = approved
        self.data = data
class Validator:
    """Class verifying if commands can be executed on database
    
    Attributes
    ----------
    database : semo.database.Database

    Methods
    -------
    tag_exists(tag_name)
        Resolve if tag exists in database
    corresponding_tag_type(tag_name, value)
        Resolve if tag and value are of corresponding data type
    file_exists(file_system, inode)
        Resolve if file exists in database
    file_has_tag(file_system, inode, tag_name)
        Resolve if there's a direct relationship between file and tag in database
    file_indirectly_has_tag(file_system, inode, tag_name)
        Resolve if there's a direct or inherited relationship between file and tag in database
    entry_consistent(entry_fsid, entry_inode, entry_path)
        Resolve if the (fsid, inode) to (path) connection in database is still valid in the native filesystem
    tag_has_direct_superiority(super_tag_name, inf_tag_name)
        Resolve if a tag has direct superiority relationship to other tag
    tag_has_superiority(super_tag_name, inf_tag_name)
        Resolve if a tag has direct or inherited superiority relationship to other tag
    file_is_isolated(file_system, inode)
        Resolve if file entry has no relationship entries and is therefore obsolete
    approved_tag_operation(file_system, inode, filepath, tag, value)
        Check if conditions are met to create tag-file relationship
    approved_untag_operation(file_system, inode, filepath, tag)
        Check if conditions are met to remove tag-file relationship
    approved_direct_untag_operation(file_system, inode, filepath, tag)
        Check if conditions are met to remove a direct tag-file relationship
    approved_list_for_tag_operation(tag_name)
        Check if conditions are met to list relationships for a tag 
    approved_conditional_list_for_tag_operation(tag_name, condition)
        Check if conditions are met to list relationships with value conditions for a tag
    approved_list_for_file_operation(self, file_system, inode, filepath)
        Check if conditions are met to list relationships for a file
    approved_del_tag_operation(tag_name)
        Check if conditions are met to delete a tag from database
    approved_subtag_operation(super_tag_name, inf_tag_name)
        Check if conditions are met to create subtag relationship
    approved_unsubtag_operation(super_tag_name, inf_tag_name)
        Check if conditions are met to remove subtag relationship

    """

    def __init__(self, database : database.Database):
        """
        Parameters
        ----------
        database : semo.database.Database
        """
        self.database = database

    def tag_exists(self, tag_name : str) -> bool:
        """ Resolve if tag exists in database

        Parameters
        ----------
        tag_name : str

        Returns
        -------
        bool
        """

        output = tag_name in self.database.get_tags()
        logger.info(f"Tag Exists '{tag_name}': {output}")
        return output
    
    def corresponding_tag_type(self, tag_name : str, value : str | int | None) -> bool:
        """ Resolve if tag and value are of corresponding data type
        
        Parameters
        ----------
        tag_name : str
        value : str | int | None

        Returns
        -------
        bool
        """

        tag_type = self.database.get_tag_type(tag_name)
        if tag_type == "int":
            return (isinstance(value, int)) or (utils.is_integer_string(value))
        if tag_type == "str":
            return (isinstance(value, str))
        return True

    def file_exists(self, file_system : int, inode : int) -> bool:
        """ Resolve if file exists in database
        
        Parameters
        ----------
        file_system : int
        inode : int

        Returns
        -------
        bool
        """

        output = (file_system, inode) in self.database.get_files()
        logger.info(f"File Exists ({file_system}, {inode}): {output}")
        return output

    def file_has_tag(self, file_system : int, inode : int, tag_name : str) -> bool:
        """Resolve if there's a direct relationship between file and tag in database
        
        Parameters
        ----------
        file_system : int
        inode : int
        tag_name : str

        Returns
        -------
        bool
        """

        output = tag_name in self.database._direct_tags_for_file(file_system, inode)
        logger.info(f"File ({file_system}, {inode}) has tag '{tag_name}': {output}")
        return output
    
    def file_indirectly_has_tag(self, file_system : int, inode : int, tag_name : str) -> bool:
        """Resolve if there's a direct or inherited relationship between file and tag in database

        Parameters
        ----------
        file_system : int
        inode : int
        tag_name : str

        Returns
        -------
        bool
        """

        output = tag_name in self.database.get_tags_for_file(file_system, inode)
        logger.info(f"File ({file_system}, {inode}) has tag '{tag_name}': {output}")
        return output
    
    def entry_consistent(self, entry_fsid : int, entry_inode : int, entry_path : str) -> bool:
        """Resolve if the (fsid, inode) to (path) connection in database is still valid in the native filesystem

        Parameters
        ----------
        entry_fsid : int
        entry_inode : int
        entry_path

        Returns
        -------
        bool
        """

        fsid, inode = utils.get_fsid_and_inode(entry_path)
        return fsid == entry_fsid and inode == entry_inode

    def tag_has_direct_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        """Resolve if a tag has direct superiority relationship to other tag

        Parameters
        ----------
        super_tag_name : str
        inf_tag_name : str

        Returns
        -------
        bool
        """

        output = inf_tag_name in self.database._direct_inferiors_for_tag(super_tag_name)
        logger.info(f"Tag '{super_tag_name}' has direct superiority over '{inf_tag_name}': {output}")
        return output

    def tag_has_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        """Resolve if a tag has direct or inherited superiority relationship to other tag

        Parameters
        ----------
        super_tag_name : str
        inf_tag_name : str

        Returns
        -------
        bool
        """

        return super_tag_name in self.database.get_superiors_tree(inf_tag_name)
    
    def __refresh_path_from_access(self, file_system, inode, filename):
        entry = self.database.get_file_by_fsid_inode(file_system, inode)
        if entry:
            _, _, entry_path, _ = entry
            if entry_path != filename:
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
    
    def file_is_isolated(self, file_system : int, inode : int) -> bool:
        """Resolve if file entry has no relationship entries and is therefore obsolete

        Parameters
        ----------
        file_system : int
        inode : int

        Returns
        -------
        bool
        """

        output = len(self.database.get_tags_for_file(file_system, inode)) == 0
        logger.info(f"File ({file_system}, {inode}) is isolated: {output}")
        return output
    
    def approved_tag_operation(self, file_system : int, inode : int, filepath : str, tag : str, value : str | int | None) -> Validation:
        """Check if conditions are met to create tag-file relationship
        
        Parameters
        ----------
        file_system : int
        inode : int
        filepath : str
        tag : str
        value : str | int | None

        Returns
        -------
        semo.validator.Validation
        """
        
        permit = Validation()
        if not self.file_exists(file_system, inode):
            logger.info(f"File ({file_system}, {inode}) not in database. Creating file record.")
            self.database.new_file(file_system, inode, filepath)
        else:
            self.__refresh_path_from_access(file_system, inode, filepath)

        if not self.tag_exists(tag):
            if not self.__approve_string(tag):
                permit.approved = False
                permit.data.append(f"Tag name '{tag}' contains invalid characters. Must be composed of alphanums and _-")
                logger.info(f"Approval for tag operation for file ({file_system}, {inode}) and tag '{tag}': {permit.approved}")
                return permit
            logger.info(f"Tag '{tag}' does not exist. Creating tag record.")
            if value is None:
                self.database.new_tag(tag)
            elif isinstance(value, int) or utils.is_integer_string(value):
                self.database.new_tag(tag, "int")
            elif isinstance(value, str):
                self.database.new_tag(tag, "str")
            
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

    def approved_untag_operation(self, file_system : int, inode : int, tag : str, filepath : str) -> Validation:
        """Check if conditions are met to remove tag-file relationship
        
        Parameters
        ----------
        file_system : int
        inode : int
        filepath : str
        tag : str

        Returns
        -------
        semo.validator.Validation
        """

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

    def approved_direct_untag_operation(self, file_system : int, inode : int, tag : str, filepath : str) -> Validation:
        """Check if conditions are met to remove a direct tag-file relationship
        
        Parameters
        ----------
        file_system : int
        inode : int
        filepath : str
        tag : str

        Returns
        -------
        semo.validator.Validation
        """
        
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

    def approved_list_for_tag_operation(self, tag_name : str) -> Validation:
        """Check if conditions are met to list relationships for a tag
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        semo.validator.Validation
        """
        
        permit = Validation(self.tag_exists(tag_name))
        logger.info(f"Approval for list for tag operation for tag ({tag_name}): {permit.approved}")
        
        if not permit.approved:
            permit.data.append(f"Tag '{tag_name}' does not exist.")
        
        return permit
    
    def approved_conditional_list_for_tag_operation(self, tag_name : str, condition : str | int | None) -> Validation:
        """Check if conditions are met to list relationships with value conditions for a tag
        
        Parameters
        ----------
        tag_name : str
        condition : str | int | None

        Returns
        -------
        semo.validator.Validation
        """
        
        permit = self.approved_list_for_tag_operation(tag_name)
        if not permit.approved or not self.corresponding_tag_type(tag_name, condition):
            permit.approved = False
            permit.data.append(f"Tag '{tag_name}' not type corresponding to '{condition}'")
        return permit

    def approved_list_for_file_operation(self, file_system : int, inode : int, filepath : str) -> Validation:
        """Check if conditions are met to list relationships for a file
        
        Parameters
        ----------
        file_system : int
        inode : int
        filepath : str

        Returns
        -------
        semo.validator.Validation
        """
        
        permit = Validation(self.file_exists(file_system, inode))
        logger.info(f"Approval for list for file operation for file ({file_system}, {inode}): {permit.approved}")
        if not permit.approved:
            permit.data.append(f"'{filepath}' does not exist in database.")
            return permit
        self.__refresh_path_from_access(file_system, inode, filepath)
        return permit

    def approved_del_tag_operation(self, tag_name) -> Validation:
        """Check if conditions are met to delete a tag from database
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        semo.validator.Validation
        """
        
        permit = Validation(self.tag_exists(tag_name))
        logger.info(f"Approval for delete tag operation for tag '{tag_name}': {permit.approved}")
        if not permit.approved:
            permit.data.append(f"Tag '{tag_name}' does not exist.")
        
        return permit

    def approved_subtag_operation(self, super_tag_name : str, inf_tag_name : str) -> Validation:
        """Check if conditions are met to create subtag relationship
        
        Parameters
        ----------
        super_tag_name : str
        inf_tag_name : str

        Returns
        -------
        semo.validator.Validation
        """
        
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
        """Check if conditions are met to remove subtag relationship
        
        Parameters
        ----------
        super_tag_name : str
        inf_tag_name : str

        Returns
        -------
        semo.validator.Validation
        """
        
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
    
            

        




   
